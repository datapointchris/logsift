# Output Modes

Understanding logsift's dual output system: JSON for machines, Markdown for humans.

## Overview

logsift provides two output formats optimized for different consumers:

- **JSON** - Structured data for LLMs and scripts
- **Markdown** - Beautiful formatted text for humans

The format is automatically detected based on context, but can be forced with `--format`.

## Auto-Detection

By default (`--format=auto`), logsift detects the best format:

```python
import sys

if sys.stdout.isatty():
    # Running in terminal → Markdown
    format = 'markdown'
else:
    # Piped or redirected → JSON
    format = 'json'
```

### Examples

```bash
# Terminal → Markdown with colors
logsift analyze app.log

# Piped → JSON automatically
logsift analyze app.log | jq '.errors'

# Redirected → JSON automatically
logsift analyze app.log > analysis.json
```

## JSON Output

Structured output optimized for machine consumption and LLM parsing.

### When to Use JSON

- **AI Agents** - Claude Code and other LLMs
- **Scripting** - Bash, Python, Node.js scripts
- **Automation** - CI/CD pipelines
- **Processing** - jq, Python json module
- **Storage** - Save analysis for later

### JSON Structure

```json
{
  "summary": {
    "status": "failed",
    "exit_code": 1,
    "duration_seconds": 2.45,
    "command": "npm run build",
    "timestamp": "2024-01-15T10:30:00Z",
    "log_file": "/Users/user/.cache/logsift/monitor/npm-20240115_103000.log"
  },
  "errors": [
    {
      "id": 1,
      "severity": "error",
      "line_in_log": 45,
      "message": "Module not found: Error: Can't resolve './missing.js'",
      "file": "src/index.js",
      "file_line": 12,
      "context_before": [
        "import React from 'react';",
        "import App from './App';"
      ],
      "context_after": [
        "",
        "ReactDOM.render(<App />, document.getElementById('root'));"
      ],
      "suggestion": {
        "action": "create_missing_file",
        "description": "Create the missing file or fix the import path",
        "confidence": "high",
        "automated_fix": "touch src/missing.js"
      },
      "pattern_matched": "webpack_module_not_found",
      "tags": ["webpack", "import", "fixable"]
    }
  ],
  "actionable_items": [
    {
      "priority": 1,
      "file": "src/index.js",
      "line": 12,
      "action": "fix_import",
      "description": "Create ./missing.js or fix import path",
      "automated": true
    }
  ],
  "stats": {
    "total_errors": 1,
    "total_warnings": 3,
    "fixable_errors": 1,
    "log_size_bytes": 45678,
    "log_lines": 234
  }
}
```

### JSON Stability Guarantee

The JSON schema is a **stable contract**. Changes require a major version bump.

Fields will never be:

- Removed without deprecation
- Changed in type
- Renamed without migration path

New optional fields may be added in minor versions.

### Processing JSON

#### With jq

```bash
# Extract error messages
logsift analyze app.log --format=json | jq -r '.errors[].message'

# Count errors
logsift analyze app.log --format=json | jq '.stats.total_errors'

# Get file references
logsift analyze app.log --format=json | jq -r '.errors[] | select(.file) | "\(.file):\(.file_line)"'

# Filter high-confidence fixes
logsift analyze app.log --format=json | jq '.errors[] | select(.suggestion.confidence == "high")'

# Extract automated fixes
logsift analyze app.log --format=json | jq -r '.errors[].suggestion.automated_fix | select(. != null)'
```

#### With Python

```python
import json
import subprocess

# Run logsift and parse JSON
result = subprocess.run(
    ['logsift', 'analyze', 'app.log', '--format=json'],
    capture_output=True,
    text=True
)
analysis = json.loads(result.stdout)

# Process errors
for error in analysis['errors']:
    print(f"Error at {error.get('file')}:{error.get('file_line')}")
    print(f"  {error['message']}")

    if error.get('suggestion'):
        print(f"  Fix: {error['suggestion']['description']}")
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
    console.log(`Fix: ${error.suggestion.description}`);
  }
});
```

## Markdown Output

Beautiful, human-readable formatted output with colors.

### When to Use Markdown

- **Interactive terminals** - When you're reading the output
- **Documentation** - Include in reports or docs
- **Debugging** - Visual inspection of errors
- **Demos** - Presenting logsift functionality

### Markdown Structure

```markdown
# Analysis Summary

**Status**: failed
**Exit Code**: 1
**Duration**: 2.45s
**Command**: npm run build
**Log File**: ~/.cache/logsift/monitor/npm-20240115_103000.log

## Errors Found (1)

### Error 1: Module not found
**Severity**: error
**File**: src/index.js:12
**Line in Log**: 45
**Pattern**: webpack_module_not_found
**Tags**: webpack, import, fixable

**Context:**
```

 43 | import React from 'react';
 44 | import App from './App';
→45 | import Missing from './missing.js';  # Error here
 46 |
 47 | ReactDOM.render(<App />, document.getElementById('root'));

```

**Message:**
Module not found: Error: Can't resolve './missing.js'

**Suggestion:**
Create the missing file or fix the import path

**Confidence**: high
**Automated Fix**: `touch src/missing.js`

---

## Statistics

- **Total Errors**: 1
- **Total Warnings**: 3
- **Fixable Errors**: 1
- **Log Size**: 44.6 KB (234 lines)
```

### Colors and Formatting

Markdown output uses colors when in a terminal:

- **Red** - Errors
- **Yellow** - Warnings
- **Green** - Success messages
- **Blue** - File references
- **Cyan** - Suggestions
- **Bold** - Field labels

Colors are automatically disabled when:

- Output is piped
- Output is redirected
- `NO_COLOR` environment variable is set
- Terminal doesn't support ANSI colors

### Copying from Terminal

Markdown output is designed to be copy-pasteable:

```bash
# Copy error context
logsift analyze app.log | grep -A 5 "Context:"

# Save to file
logsift analyze app.log --format=markdown > report.md
```

## Forcing a Format

Override auto-detection with `--format`:

```bash
# Force JSON (even in terminal)
logsift analyze app.log --format=json

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

## Plain Text Output (Future)

Phase 3 will add `--format=plain` for:

- No ANSI colors
- Simple text output
- Logging to files
- Email-friendly format

```bash
# Future
logsift analyze app.log --format=plain > errors.txt
```

## Comparison Table

| Feature | JSON | Markdown |
|---------|------|----------|
| **Machine readable** | ✅ Yes | ⚠️ Partial |
| **Human readable** | ⚠️ Requires parsing | ✅ Beautiful |
| **Colors** | ❌ No | ✅ Yes (terminal) |
| **Scriptable** | ✅ Easy | ⚠️ Harder |
| **LLM consumption** | ✅ Optimized | ⚠️ Works but verbose |
| **Copy-paste** | ⚠️ Need jq | ✅ Easy |
| **Schema stability** | ✅ Guaranteed | ⚠️ May change |
| **File size** | ⚠️ Larger | ✅ Smaller |
| **Debugging** | ⚠️ Hard to read | ✅ Easy to read |

## Design Decisions

### Why JSON for LLMs?

LLMs excel at parsing structured data:

- Predictable schema reduces token usage
- Fields are explicitly labeled
- Arrays and objects are natural
- No ambiguity in parsing

### Why Markdown for Humans?

Humans prefer formatted text:

- Visual hierarchy with headers
- Color-coded severity
- Code blocks for context
- Readable without tools

### Why Auto-Detection?

Best of both worlds:

- Terminal users get beauty
- Scripts get structure
- No manual flags needed
- Optimal default behavior

## Best Practices

### 1. Let Auto-Detection Work

```bash
# ✓ GOOD - Auto-detects correctly
logsift analyze app.log
logsift analyze app.log | jq

# ✗ UNNECESSARY - Auto would work
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
- [CLI Reference](../cli-reference.md) - All format options
