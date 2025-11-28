# Data Flow

How log analysis works internally in logsift.

## Overview

```
Input → Parser → Extractors → Pattern Matcher → Context Extractor → Formatter → Output
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

Output: List of `LogLine` objects with:

- `line_number`
- `content`
- `timestamp` (if detected)
- `level` (if detected)

### 3. Extractors

Extract errors, warnings, and file references:

```python
errors = extract_errors(log_lines)
warnings = extract_warnings(log_lines)
file_refs = extract_file_references(log_lines)
```

Uses regex patterns to identify:

- Error indicators (`ERROR:`, `FATAL:`, exception types)
- Warning indicators (`WARNING:`, `WARN:`)
- File:line patterns (`file.py:42`, `"file.js", line 123`)

### 4. Pattern Matcher

Apply TOML pattern libraries to detected errors:

```python
for error in errors:
    for pattern in patterns:
        if re.match(pattern.regex, error.message):
            error.pattern_matched = pattern.name
            error.suggestion = pattern.suggestion
            error.tags = pattern.tags
            break  # First match wins
```

Patterns tried in order:

1. Built-in patterns (`src/logsift/patterns/defaults/*.toml`)
2. Custom patterns (`~/.config/logsift/patterns/*.toml`)

### 5. Context Extractor

Extract ±N lines around each error:

```python
for error in errors:
    line_idx = error.line_in_log - 1
    error.context_before = log_lines[max(0, line_idx - context_lines):line_idx]
    error.context_after = log_lines[line_idx + 1:line_idx + 1 + context_lines]
```

Default: `context_lines = 2`

### 6. Formatter

Convert to JSON or Markdown based on format:

```python
if output_format == 'json':
    output = format_json(analysis_result)
else:
    output = format_markdown(analysis_result)
```

JSON formatter creates stable schema.
Markdown formatter creates colored, formatted text.

### 7. Output

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

### Error

```python
@dataclass
class Error:
    id: int
    severity: str  # error, warning, info
    line_in_log: int
    message: str
    file: str | None = None
    file_line: int | None = None
    context_before: list[str] = field(default_factory=list)
    context_after: list[str] = field(default_factory=list)
    pattern_matched: str | None = None
    tags: list[str] = field(default_factory=list)
    suggestion: Suggestion | None = None
```

### Analysis Result

```python
@dataclass
class AnalysisResult:
    summary: Summary
    errors: list[Error]
    actionable_items: list[ActionableItem]
    stats: Stats
```

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

For large logs (>100 MB), Phase 3 adds streaming to reduce memory.

### Optimization Strategies

1. **Early exit** - Stop parsing on first pattern match
2. **Compiled regex** - Patterns compiled once at load
3. **Lazy context** - Extract context only for matched errors
4. **Capped errors** - `max_errors` prevents unbounded growth

## Caching Strategy

```
~/.cache/logsift/
├── monitor/               # Monitored command logs
│   └── <name>-<timestamp>.log
└── default/              # Other logs
```

Cache hit: Re-analyze existing log file
Cache miss: Save new log for future analysis

Rotation: Automatic cleanup after `retention_days`

## See Also

- [Design Principles](design-principles.md) - Why these choices
- [Pattern Matching](../concepts/pattern-matching.md) - How patterns work
