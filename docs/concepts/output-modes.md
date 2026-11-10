# Output Modes

Understanding logsift's three output formats: toon for agents, JSON for programs, Markdown for humans.

## Overview

logsift prints one analysis in three formats, each for a different reader:

- **toon** - Compact text an LLM reads with the fewest tokens
- **JSON** - Structured data for scripts and programs
- **Markdown** - Formatted text for humans

The format is automatically detected based on context, but can be forced with `--format`.

## Auto-Detection

By default (`--format=auto`), `resolve_format()` in `output/analysis_format.py` picks Markdown
when stdout is a terminal and toon when it is not. Any other value prints that format.
`--format` accepts `auto`, `json`, `toon` and `markdown`, and refuses anything else with exit 2.

### Examples

```bash
# Terminal → Markdown
logsift analyze app.log

# Piped → toon
logsift analyze app.log | head

# JSON needs asking for, piped or redirected
logsift analyze app.log --format=json | jq '.errors'
logsift analyze app.log --format=json > analysis.json
```

## toon Output

toon is the default whenever stdout is not a terminal, because an agent running logsift reads
piped output. Each issue keeps its id, severity, line, message, code and suggestion. It drops
`pattern_name`, `tags`, `file_references` and the context lines, except the lines a multi-line
pattern asked for. A program that needs those fields asks for JSON.

## JSON Output

Structured output optimized for machine consumption and LLM parsing.

### When to Use JSON

- **Agent code** - A program an agent writes to parse the result
- **Scripting** - Bash, Python, Node.js scripts
- **Automation** - CI/CD pipelines
- **Processing** - jq, Python json module
- **Storage** - Save analysis for later

### JSON Structure

[`schemas/analysis.schema.json`](https://github.com/datapointchris/logsift/blob/main/schemas/analysis.schema.json)
is the shape, and [JSON Schema](../api/json-schema.md) says how to read it. Every document carries
`schema_version`, which rises whenever a field is renamed, removed or changes meaning.

### Processing JSON

#### With jq

```bash
# Extract error messages
logsift analyze app.log --format=json | jq -r '.errors[].message'

# Count errors
logsift analyze app.log --format=json | jq '.stats.total_errors'

# Get file references
logsift analyze app.log --format=json | jq -r '.errors[].file_references[]? | "\(.[0]):\(.[1])"'

# Errors a pattern recognized, with its fix hint
logsift analyze app.log --format=json | jq '.errors[] | select(.suggestion) | {pattern_name, suggestion}'
```

#### With Python

```python
import json
import subprocess

# Run logsift and parse JSON
result = subprocess.run(['logsift', 'analyze', 'app.log', '--format=json'], capture_output=True, text=True)
analysis = json.loads(result.stdout)

# Process errors
for error in analysis['errors']:
    print(f'Line {error["line_in_log"]}: {error["message"]}')
    for path, line in error.get('file_references', []):
        print(f'  at {path}:{line}')
    if error.get('suggestion'):
        print(f'  Fix: {error["suggestion"]}')
```

#### With Node.js

```javascript
const { execSync } = require('child_process');

// Run logsift and parse JSON
const output = execSync('logsift analyze app.log --format=json', {
  encoding: 'utf-8'
});
const analysis = JSON.parse(output);

// Process errors
analysis.errors.forEach(error => {
  console.log(`Error: ${error.message}`);
  if (error.suggestion) {
    console.log(`Fix: ${error.suggestion}`);
  }
});
```

## Markdown Output

Plain Markdown text for a person to read. It carries no ANSI colors, so it reads the same on a
terminal, in a file or in an email.

### When to Use Markdown

- **Interactive terminals** - When you're reading the output
- **Documentation** - Include in reports or docs
- **Debugging** - Visual inspection of errors

### Markdown Structure

`logsift analyze --format=markdown build.log` prints:

```markdown
# Log Analysis Results

**Errors:** 2 | **Warnings:** 1

## Errors

### Error #1 (Line 2)

bash: frobnicate: command not found

**Suggestion:** Check command spelling and ensure it's installed and in PATH

**Context:** Lines 1-4

### Error #2 (Line 3)

src/main.py:42:5: F401 'os' imported but unused

**Files:** `src/main.py:42`

**Context:** Lines 1-5

## Warnings

### Warning #1 (Line 4)

WARNING: deprecated flag --legacy

**Context:** Lines 2-5
```

`**Suggestion:**` appears where the matching pattern has a fix hint, and `**Files:**` where the
message names a file. `monitor` prints the command's exit code and duration to stderr, in color on
a terminal, so they never enter the Markdown.

### Copying from Terminal

Markdown output is designed to be copy-pasteable:

```bash
# Show each error's context range
logsift analyze app.log --format=markdown | grep "Context:"

# Save to file
logsift analyze app.log --format=markdown > report.md
```

## Forcing a Format

Override auto-detection with `--format`:

```bash
# Force JSON (piped or on a terminal)
logsift analyze app.log --format=json

# Force toon (even on a terminal)
logsift analyze app.log --format=toon

# Force Markdown (even when piped)
logsift analyze app.log --format=markdown | less

# Default auto-detection
logsift analyze app.log --format=auto  # or omit --format
```

## Use Cases by Format

### JSON Use Cases

1. **Automated Fix Loops**

   ```bash
   logsift monitor --format=json -- npm run build | python fix_errors.py
   ```

2. **CI/CD Integration**

   ```yaml
   - run: logsift monitor --format=json -- npm test > test-results.json
   - uses: actions/upload-artifact@v2
     with:
       path: test-results.json
   ```

3. **Database Storage**

   ```python
   analysis = run_logsift(['npm', 'run', 'build'])
   db.save_analysis(analysis)
   ```

4. **Metrics Collection**

   ```bash
   total_errors=$(logsift analyze app.log --format=json | jq '.stats.total_errors')
   ```

### Markdown Use Cases

1. **Quick Debugging**

   ```bash
   logsift monitor -- pytest tests/
   # Read errors in terminal
   ```

2. **Documentation**

   ```bash
   # Include in docs
   logsift analyze build.log --format=markdown > docs/build-errors.md
   ```

3. **Email Reports**

   ```bash
   logsift analyze app.log --format=markdown | mail -s "Build Report" team@example.com
   ```

4. **Terminal Dashboards**

   ```bash
   watch -n 60 'logsift analyze /var/log/app.log --format=markdown'
   ```

## Plain Text Output

Markdown has no ANSI colors, so `--format=markdown` is already plain text in a file:

```bash
logsift analyze app.log --format=markdown > errors.txt
```

## Comparison Table

| Feature | toon | JSON | Markdown |
| --- | --- | --- | --- |
| **Default when** | Piped | Never | On a terminal |
| **Machine readable** | ⚠️ Needs a toon decoder | ✅ Yes | ⚠️ Partial |
| **Human readable** | ✅ Compact | ⚠️ Requires parsing | ✅ Easy |
| **Fields kept** | Message, code, suggestion | All | Message, files, suggestion, context range |
| **LLM consumption** | ✅ Fewest tokens | ⚠️ Verbose | ⚠️ Verbose |
| **Schema** | — | ✅ `schemas/analysis.schema.json` | ⚠️ May change |

## Design Decisions

### Why toon for LLMs?

An agent that runs logsift reads piped output, and every token of it costs context. toon carries
the same errors as JSON with no braces, quotes or repeated keys, and leaves out the pattern
metadata an agent reading the message does not need.

### Why Markdown for Humans?

Humans prefer formatted text:

- Visual hierarchy with headers
- Errors and warnings under separate headings
- Readable without tools, and pasteable into an issue or a doc

### Why Auto-Detection?

A person at a terminal gets Markdown and an agent reading a pipe gets toon, with no flag. A
program that parses the output asks for JSON, because a parser should never depend on whether
stdout is a terminal.

## Best Practices

### 1. Let Auto-Detection Work for Readers

```bash
# ✓ GOOD - Markdown for you, toon for an agent reading the pipe
logsift analyze app.log

# ✗ BAD - jq cannot parse toon
logsift analyze app.log | jq

# ✓ GOOD - ask for JSON when a program parses it
logsift analyze app.log --format=json | jq
```

### 2. Force Format for Consistency

```bash
# ✓ GOOD - CI/CD always gets JSON
logsift monitor --format=json -- npm test

# ✗ BAD - Might get Markdown if run interactively
logsift monitor -- npm test
```

### 3. Use JSON for Scripts

```python
# ✓ GOOD - Stable, parseable
result = subprocess.run(['logsift', 'analyze', 'app.log', '--format=json'], ...)
data = json.loads(result.stdout)

# ✗ BAD - Fragile, parsing needed
result = subprocess.run(['logsift', 'analyze', 'app.log', '--format=markdown'], ...)
errors = re.findall(r'Error: (.+)', result.stdout)
```

### 4. Use Markdown for Humans

```bash
# ✓ GOOD - Easy to read
logsift analyze app.log

# ✗ BAD - Hard to read
logsift analyze app.log --format=json
```

## See Also

- [JSON Schema](../api/json-schema.md) - Complete JSON specification
- [Agentic Integration](agentic-integration.md) - Using JSON with AI agents
- [CLI Reference](../cli-reference.md) - Where the help lives, what each stream carries, and the exit codes
