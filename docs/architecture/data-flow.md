# Data Flow

How log analysis works internally in logsift.

## Overview

```text
Input → Parser → IssueDetector → Analyzer → Formatter → Output
```

## Detailed Pipeline

### 1. Input

Command execution or file reading:

```python
# Monitor mode
result = subprocess.run(command, capture_output=True, text=True)
log_content = result.stdout + result.stderr

# Analyze mode
log_content = Path(log_file).read_text()
```

### 2. Parser

Auto-detect format and normalize to internal representation:

```python
def parse(log_content: str) -> list[LogLine]:
    if is_json_log(log_content):
        return parse_json_log(log_content)
    elif is_structured_log(log_content):
        return parse_structured_log(log_content)
    else:
        return parse_plain_text(log_content)
```

**Critical**: Parser preserves FULL original message content and always sets `level='INFO'` as default. It does NOT detect error/warning levels from message content - that's the IssueDetector's job.

Output: List of `LogLine` objects with:

- `line_number`
- `content` (full original message preserved)
- `timestamp` (if detected from structured format)
- `level` (explicit field from JSON/structured, or 'INFO' default)

### 3. IssueDetector

Single-pass detection of errors, warnings, and issues using TOML patterns:

```python
errors, warnings = IssueDetector().detect_issues(log_entries, patterns)
```

Detection strategy:

- **For JSON/structured logs**: Use explicit `level` field if present
- **For plain text logs**: Apply TOML pattern regex to message content
- **Single pass**: All pattern matching happens in one iteration
- **First match wins**: custom files are tried first, then the built-in files by name with
  `common.toml` last, so its catch-alls such as `generic_error` never shadow a specific pattern

Pattern matching:

```python
for entry in log_entries:
    for pattern in all_patterns:
        if re.search(pattern['regex'], entry['message']):
            issue = self._build_issue(entry, pattern['severity'], issue_id, pattern)
            # issue['pattern_name'], ['description'], ['tags'] and ['suggestion'] come from the pattern
            break  # First match wins
```

`Analyzer.__init__` loads the patterns, and detection tries them in this order:

1. Custom patterns (`$XDG_CONFIG_HOME/logsift/patterns/*.toml`, else `~/.config/logsift/patterns/*.toml`)
2. Built-in patterns (`src/logsift/patterns/defaults/*.toml`)

### 4. Analyzer

Orchestrates the analysis pipeline and enhances issues with context:

```python
analyzer = Analyzer(context_lines=2)
result = analyzer.analyze(log_content)
```

Responsibilities:

- Extract file:line references from each issue's message into `file_references`
- Add the parsed lines around each issue as `context_before` and `context_after`
- Name the pre-commit hooks the log shows passing or failing, under `hooks`
- Count errors and warnings under `stats`

Context extraction works on the parsed entries, so a blank line, which parses to nothing, is never
context:

```python
idx = position of the issue's entry in log_entries
issue['context_before'] = log_entries[max(0, idx - context_lines) : idx]
issue['context_after'] = log_entries[idx + 1 : idx + 1 + (pattern_context_lines_after or context_lines)]
```

Default: `context_lines = 2`

### 5. Formatter

`monitor` adds a `summary` of the run to the result, then the requested format renders it:

```python
if output_format == 'json':
    output = format_json(analysis_result)  # adds schema_version
elif output_format == 'toon':
    output = format_toon(analysis_result)
else:
    output = format_markdown(analysis_result)
```

`format_json` writes the document `schemas/analysis.schema.json` describes.

### 6. Output

Write to stdout (and optionally save to cache):

```python
print(output)

if save_log:
    log_file = cache.create_log_path(name, context='monitor')
    log_file.write_text(raw_log_content)
```

## Data Structures

### LogLine

```python
@dataclass
class LogLine:
    line_number: int
    content: str
    timestamp: datetime | None = None
    level: str | None = None  # INFO, WARNING, ERROR
```

### Issues and the Analysis Result

The analyzer passes plain dictionaries from stage to stage, with no dataclass for an issue or a
result. `schemas/analysis.schema.json` is the shape the result takes once `format_json` writes it.

## Performance Characteristics

### Time Complexity

- **Parsing**: O(n) where n = number of log lines
- **Extraction**: O(n × p) where p = number of patterns
- **Context**: O(e × c) where e = errors, c = context lines
- **Formatting**: O(e) where e = errors

Total: O(n × p) dominated by pattern matching

### Space Complexity

- **Input**: O(n) - full log in memory
- **Parsed**: O(n) - LogLine objects
- **Errors**: O(e) - typically e << n
- **Output**: O(e × c) - errors with context

Memory therefore grows with the log, because the whole file is read before analysis starts.

### Optimization Strategies

1. **Early exit** - Stop parsing on first pattern match
2. **Compiled regex** - Patterns compiled once at load
3. **Lazy context** - Extract context only for matched errors
4. **Capped errors** - `max_errors` prevents unbounded growth

## Caching Strategy

```text
$XDG_CACHE_HOME/logsift/      # else ~/.cache/logsift/
├── raw/<stem>.log            # what a monitored command printed
├── json/<stem>.json          # its analysis, in each output format
├── toon/<stem>.toon
└── md/<stem>.md
```

`CacheManager.create_paths(name)` builds the stem as `<UTC timestamp>-<name>`. `monitor` writes all
four files. `analyze <file>` writes only the three analyses, named after the log file.

Nothing is cleaned automatically. `logsift logs clean` deletes raw logs older than `--days`, 90 by
default.

## See Also

- [Design Principles](design-principles.md) - Why these choices
- [Pattern Matching](../concepts/pattern-matching.md) - How patterns work
