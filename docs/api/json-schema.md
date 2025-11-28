# JSON Output Schema

Complete specification of logsift's JSON output format.

## Schema Stability

The JSON schema is a **stable contract** between logsift and consuming applications:

- Fields will never be removed without deprecation
- Types will never change
- Field names will never change
- Breaking changes require major version bump

New optional fields may be added in minor versions.

## Root Object

```json
{
  "summary": {...},
  "errors": [...],
  "actionable_items": [...],
  "stats": {...}
}
```

## summary

Command execution metadata:

```json
{
  "summary": {
    "status": "failed",              // "failed" | "success"
    "exit_code": 1,                  // integer
    "duration_seconds": 2.45,        // float
    "command": "npm run build",      // string
    "timestamp": "2024-01-15T10:30:00Z",  // ISO8601
    "log_file": "/path/to/log.log"   // string | null
  }
}
```

**Fields:**

- `status` (string) - `"failed"` or `"success"`
- `exit_code` (integer) - Command exit code
- `duration_seconds` (float) - Execution time
- `command` (string) - Command that was run
- `timestamp` (string) - ISO8601 timestamp
- `log_file` (string | null) - Path to cached log file

## errors

Array of detected errors with context:

```json
{
  "errors": [
    {
      "id": 1,
      "severity": "error",
      "line_in_log": 45,
      "message": "Module not found: Error: Can't resolve './missing.js'",
      "file": "src/index.js",
      "file_line": 12,
      "context_before": ["import React from 'react';", "import App from './App';"],
      "context_after": ["", "ReactDOM.render(<App />, document.getElementById('root'));"],
      "suggestion": {
        "action": "create_missing_file",
        "description": "Create the missing file or fix the import path",
        "confidence": "high",
        "automated_fix": "touch src/missing.js"
      },
      "pattern_matched": "webpack_module_not_found",
      "tags": ["webpack", "import", "fixable"]
    }
  ]
}
```

**Error Object Fields:**

- `id` (integer) - Unique error identifier (1-indexed)
- `severity` (string) - `"error"`, `"warning"`, or `"info"`
- `line_in_log` (integer) - Line number in original log
- `message` (string) - Error message
- `file` (string | null) - Source file path (if detected)
- `file_line` (integer | null) - Line number in source file (if detected)
- `context_before` (array[string]) - Lines before error (default: 2 lines)
- `context_after` (array[string]) - Lines after error (default: 2 lines)
- `suggestion` (object | null) - Fix suggestion (if available)
- `pattern_matched` (string | null) - Pattern name that matched
- `tags` (array[string]) - Categorization tags

## suggestion

Fix suggestion for automated workflows:

```json
{
  "suggestion": {
    "action": "create_missing_file",
    "description": "Create the missing file or fix the import path",
    "confidence": "high",
    "automated_fix": "touch src/missing.js"
  }
}
```

**Fields:**

- `action` (string) - Action type identifier
- `description` (string) - Human-readable fix description
- `confidence` (string) - `"high"`, `"medium"`, or `"low"`
- `automated_fix` (string | null) - Shell command to fix (if available)

## actionable_items

Prioritized list of fixes:

```json
{
  "actionable_items": [
    {
      "priority": 1,
      "file": "src/index.js",
      "line": 12,
      "action": "fix_import",
      "description": "Create ./missing.js or fix import path",
      "automated": true
    }
  ]
}
```

**Fields:**

- `priority` (integer) - Priority (1 = highest)
- `file` (string | null) - File to edit
- `line` (integer | null) - Line to edit
- `action` (string) - Action type
- `description` (string) - What to do
- `automated` (boolean) - Can be automated?

## stats

Summary statistics:

```json
{
  "stats": {
    "total_errors": 1,
    "total_warnings": 3,
    "fixable_errors": 1,
    "log_size_bytes": 45678,
    "log_lines": 234
  }
}
```

**Fields:**

- `total_errors` (integer) - Count of errors
- `total_warnings` (integer) - Count of warnings
- `fixable_errors` (integer) - Errors with automated fixes
- `log_size_bytes` (integer) - Log file size
- `log_lines` (integer) - Total log lines

## Complete Example

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
    "total_warnings": 0,
    "fixable_errors": 1,
    "log_size_bytes": 45678,
    "log_lines": 234
  }
}
```

## Parsing Examples

### Python

```python
import json

data = json.loads(logsift_output)

if data['summary']['status'] == 'failed':
    for error in data['errors']:
        print(f"Error: {error['message']}")
        if error['file']:
            print(f"  at {error['file']}:{error['file_line']}")
```

### jq

```bash
# Get all error messages
jq -r '.errors[].message'

# Get file references
jq -r '.errors[] | select(.file) | "\(.file):\(.file_line)"'

# Count fixable errors
jq '.stats.fixable_errors'
```

## Version History

- **v0.1.0** - Initial schema

## See Also

- [Output Modes](../concepts/output-modes.md) - JSON vs Markdown
- [Agentic Integration](../concepts/agentic-integration.md) - Using JSON with AI
