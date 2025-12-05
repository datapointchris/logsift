# CLI Reference

Complete command-line reference for logsift.

## Global Options

Available for all commands:

```bash
logsift [OPTIONS] COMMAND [ARGS]...
```

### Cache Options

- `--cache-dir PATH` - Path to the cache directory (env: `LOGSIFT_CACHE_DIR`)
- `--no-cache` - Avoid reading from or writing to the cache (env: `LOGSIFT_NO_CACHE`)

### Configuration Options

- `-V, --version` - Display the logsift version
- `--config-file PATH` - Path to a logsift.toml configuration file (env: `LOGSIFT_CONFIG_FILE`)
- `--no-config` - Avoid loading configuration files (env: `LOGSIFT_NO_CONFIG`)

**Examples:**

```bash
# Display version
logsift --version
logsift -V

# Use custom config file
logsift --config-file /path/to/config.toml monitor -- make build

# Disable caching
logsift --no-cache monitor -- npm test

# Custom cache directory
logsift --cache-dir /tmp/logsift-cache monitor -- pytest
```

### `--help`

Show help message:

```bash
logsift --help        # Global help
logsift monitor --help  # Command-specific help
logsift help monitor  # Alternative help syntax
```

## Commands

### `monitor`

Execute a command, capture output, and analyze it.

```bash
logsift monitor [OPTIONS] -- COMMAND [ARGS]...
```

**Arguments:**

- `COMMAND` - Command to monitor (required)
- `ARGS` - Arguments passed to the command

**Options:**

- `-n, --name NAME` - Custom name for monitoring session (default: auto-generated timestamp)
- `--format FORMAT` - Output format: `auto`, `json`, `markdown`, `plain` (default: `auto`)
- `--stream` - Stream all output to terminal in real-time (default: show periodic updates)
- `--update-interval SECONDS` - Seconds between progress updates when not streaming (default: 60)
- `--minimal` - Suppress all progress output, only show final analysis (ideal for LLM workflows)
- `--notify` - Send desktop notification on completion (requires notify-send or osascript)
- `--external-log PATH` - Tail external log file while monitoring (merges with command output)
- `--append` - Append to existing log instead of creating new (useful for iterative debugging)

**Examples:**

```bash
# Basic monitoring
logsift monitor -- npm run build

# Custom name for organization
logsift monitor -n my-app-build -- npm run build

# Force JSON output
logsift monitor --format=json -- pytest tests/

# Stream all output in real-time
logsift monitor --stream -- npm install

# Minimal output for LLM workflows
logsift monitor --minimal -- pre-commit run --files file.py

# Desktop notification on completion
logsift monitor --notify -- make build

# Monitor with external log file
logsift monitor --external-log /var/log/app.log -- ./script.sh

# Append to existing log for debugging
logsift monitor --append -- pytest tests/test_feature.py
```

**Behavior:**

1. Runs the command and captures all output (stdout + stderr)
2. Saves log to `~/.cache/logsift/monitor/<name>-<timestamp>.log`
3. Analyzes output for errors, warnings, and patterns
4. Outputs structured analysis (JSON or Markdown)
5. Exits with command's exit code (0 for success, non-zero for failure)

**Auto-Format Detection:**

- **Terminal (TTY)**: Outputs beautiful Markdown with colors
- **Piped/headless**: Outputs structured JSON for processing

```bash
# Terminal → Markdown
logsift monitor -- make build

# Piped → JSON automatically
logsift monitor -- make build | jq '.errors'
```

### `analyze`

Analyze an existing log file.

```bash
logsift analyze [OPTIONS] LOG_FILE
```

**Arguments:**

- `LOG_FILE` - Path to log file to analyze (required)

**Options:**

- `--format FORMAT` - Output format: `auto`, `json`, `markdown` (default: `auto`)

**Examples:**

```bash
# Analyze a log file
logsift analyze /var/log/app.log

# Force JSON output
logsift analyze build.log --format=json

# Force Markdown output
logsift analyze build.log --format=markdown

# Pipe JSON to jq
logsift analyze app.log --format=json | jq '.errors[0]'

# Analyze different log types
logsift analyze /var/log/syslog
logsift analyze ~/.npm/_logs/2024-01-01T00_00_00_000Z-debug.log
logsift analyze build-output.txt
```

**Behavior:**

1. Reads the log file
2. Auto-detects log format (JSON, structured, plain text)
3. Applies pattern matching
4. Extracts errors, warnings, and file references
5. Outputs structured analysis

**Supported Log Formats:**

- Plain text logs
- JSON logs (one JSON object per line)
- Structured logs (key=value pairs)
- Build tool outputs (npm, cargo, pytest, etc.)
- System logs (syslog, journalctl)

### `logs`

Manage cached log files.

```bash
logsift logs [SUBCOMMAND]
```

**Subcommands:**

- `list` - List all cached log files
- `clean` - Clean old log files (planned)
- `show` - Show a specific log file (planned)

**Examples:**

```bash
# List cached logs
logsift logs list

# Clean old logs (planned)
logsift logs clean --days=30
```

### `analyzed`

Manage saved analysis results.

```bash
logsift analyzed [SUBCOMMAND]
```

View previously saved analysis results in various formats.

### `raw`, `json`, `toon`, `md`

View format-specific files from cache.

```bash
logsift raw    # View raw log files
logsift json   # View JSON analysis results
logsift toon   # View toon format files
logsift md     # View markdown analysis results
```

### `help`

Display help information for logsift commands.

```bash
logsift help [COMMAND]
```

**Examples:**

```bash
# General help
logsift help

# Command-specific help
logsift help monitor
```

## Output Formats

### Auto (`--format=auto`)

Default behavior - automatically detects best format:

- **TTY (terminal)**: Markdown with colors and formatting
- **Non-TTY (piped)**: JSON for machine processing

```bash
# Auto-detects terminal → Markdown
logsift analyze app.log

# Auto-detects pipe → JSON
logsift analyze app.log | jq
```

### JSON (`--format=json`)

Structured JSON output optimized for LLM consumption:

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
      "context_before": ["import React from 'react';", "import App from './App';"],
      "context_after": ["", "ReactDOM.render(<App />, document.getElementById('root'));"],
      "suggestion": {
        "action": "create_missing_file",
        "description": "Create the missing file or fix the import path",
        "confidence": "high"
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
      "automated": false
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

See [JSON Schema](api/json-schema.md) for complete schema documentation.

### Markdown (`--format=markdown`)

Human-readable formatted output with colors:

```markdown
# Analysis Summary

**Status**: failed
**Exit Code**: 1
**Duration**: 2.45s
**Command**: npm run build

## Errors Found (1)

### Error 1: Module not found
**Severity**: error
**File**: src/index.js:12
**Line in Log**: 45

**Context:**
```

import React from 'react';
import App from './App';
→ import Missing from './missing.js';  # Error here

ReactDOM.render(<App />, document.getElementById('root'));

```

**Message:**
Module not found: Error: Can't resolve './missing.js'

**Suggestion:**
Create the missing file or fix the import path

**Tags**: webpack, import, fixable
```

## Cache and Configuration

### Cache Location

Logs are saved to `~/.cache/logsift/`:

```
~/.cache/logsift/
├── monitor/                    # Monitored command logs
│   ├── npm-20240115_103000.log
│   ├── pytest-20240115_110000.log
│   └── cargo-20240115_120000.log
└── default/                    # Other logs
```

### Cache Cleanup

Manually clean old logs using Python:

```python
from logsift.cache.rotation import clean_old_logs
from pathlib import Path

# Clean logs older than 30 days
deleted = clean_old_logs(Path.home() / '.cache' / 'logsift', retention_days=30)
print(f"Deleted {deleted} old log files")
```

Planned CLI command (Phase 3):

```bash
logsift logs clean              # Clean >90 days (default)
logsift logs clean --days=30    # Custom retention
```

### Configuration File

Create `~/.config/logsift/config.toml`:

```toml
[cache]
directory = "~/.cache/logsift"
retention_days = 90

[analysis]
context_lines = 2      # Lines of context around errors
max_errors = 100       # Maximum errors to extract

[output]
default_format = "auto"  # auto, json, markdown
```

See [Config Format](api/config-format.md) for all options.

### Custom Patterns

Create custom pattern files in `~/.config/logsift/patterns/`:

```toml
# ~/.config/logsift/patterns/myapp.toml
[[patterns]]
name = "myapp_database_error"
regex = "DATABASE ERROR: (.+)"
severity = "error"
description = "Database connection or query error"
tags = ["database", "myapp"]
suggestion = "Check database connection string and credentials"
```

Patterns are automatically loaded from:

1. Built-in patterns: `src/logsift/patterns/defaults/*.toml`
2. Custom patterns: `~/.config/logsift/patterns/*.toml`

See [Pattern Format](api/pattern-format.md) and [Custom Patterns](guides/custom-patterns.md).

## Exit Codes

logsift uses standard exit codes:

- **0**: Success - command completed without errors
- **1**: Analysis error - logsift failed to analyze (file not found, invalid format)
- **Other**: Command exit code - when using `monitor`, exits with monitored command's exit code

```bash
# Check exit code
logsift monitor -- npm run build
echo $?  # Will be npm's exit code

# Use in scripts
if logsift monitor -- make test; then
    echo "Tests passed"
else
    echo "Tests failed"
fi
```

## Environment Variables

logsift supports the following environment variables:

### Configuration

- `LOGSIFT_CONFIG_FILE` - Custom config file path (overrides default `~/.config/logsift/config.toml`)
- `LOGSIFT_NO_CONFIG` - Set to `1` or `true` to avoid loading configuration files

### Cache

- `LOGSIFT_CACHE_DIR` - Custom cache directory (overrides default `~/.cache/logsift`)
- `LOGSIFT_NO_CACHE` - Set to `1` or `true` to avoid reading from or writing to cache

### Monitor Command

- `LOGSIFT_SESSION_NAME` - Default session name for monitor command
- `LOGSIFT_OUTPUT_FORMAT` - Default output format: `auto`, `json`, `markdown`, `plain`
- `LOGSIFT_UPDATE_INTERVAL` - Default update interval in seconds (default: 60)

**Examples:**

```bash
# Use custom cache directory
export LOGSIFT_CACHE_DIR=/tmp/logsift-cache
logsift monitor -- make build

# Disable caching for CI/CD
export LOGSIFT_NO_CACHE=1
logsift monitor -- pytest

# Force JSON output globally
export LOGSIFT_OUTPUT_FORMAT=json
logsift monitor -- npm test

# Use custom config file
export LOGSIFT_CONFIG_FILE=/etc/logsift/config.toml
logsift analyze app.log
```

## Performance Considerations

### Large Log Files

For very large log files (>100 MB):

- Analysis may take several seconds
- Memory usage scales with file size
- Phase 3 will add streaming/incremental parsing

```bash
# Current behavior
logsift analyze huge.log  # May be slow for >100MB files

# Phase 3 planned
logsift analyze --streaming huge.log  # Process incrementally
```

### Batch Processing

Process multiple logs efficiently:

```bash
# Sequential
for log in logs/*.log; do
    logsift analyze "$log" --format=json > "analysis/$(basename $log .log).json"
done

# Parallel (GNU parallel)
parallel logsift analyze {} --format=json '>' analysis/{/.}.json ::: logs/*.log
```

## Shell Integration

### Bash/Zsh Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Shorthand aliases
alias lsm='logsift monitor'
alias lsa='logsift analyze'

# Common workflows
alias lsm-json='logsift monitor --format=json'
alias lsa-json='logsift analyze --format=json'
```

### Shell Completion (Planned)

Tab completion planned for Phase 3:

```bash
# Bash
eval "$(_LOGSIFT_COMPLETE=bash_source logsift)"

# Zsh
eval "$(_LOGSIFT_COMPLETE=zsh_source logsift)"
```

## Integration with Other Tools

### jq (JSON Processing)

```bash
# Extract first error message
logsift analyze app.log --format=json | jq -r '.errors[0].message'

# Count errors by severity
logsift analyze app.log --format=json | jq '.stats.total_errors'

# Get all file references
logsift analyze app.log --format=json | jq -r '.errors[] | select(.file) | "\(.file):\(.file_line)"'
```

### fzf (Fuzzy Finding)

Planned integration (Phase 2):

```bash
# Interactively select error
logsift logs list | fzf

# Jump to error in editor
logsift analyze app.log --format=json | jq -r '.errors[] | "\(.file):\(.file_line)"' | fzf | xargs -I {} vim {}
```

### Claude Code

Use with Claude Code for automated workflows:

```python
# Claude Code can parse JSON and apply fixes
result = subprocess.run(['logsift', 'monitor', '--format=json', '--', 'npm', 'run', 'build'],
                       capture_output=True, text=True)
analysis = json.loads(result.stdout)

for error in analysis['errors']:
    if error['suggestion']['automated_fix']:
        # Apply fix automatically
        apply_fix(error)
```

See [Agentic Integration](concepts/agentic-integration.md) for complete workflows.

## Tips and Best Practices

1. **Use `--format=json` for scripting** - Stable schema, easy to parse
2. **Name monitoring sessions** - Use `-n` for better organization
3. **Let auto-format work** - Default `auto` usually does the right thing
4. **Pipe to jq** - Extract specific fields from JSON output
5. **Create custom patterns** - Domain-specific error detection
6. **Clean cache regularly** - Prevent disk space issues

## See Also

- [5-Minute Quickstart](quickstart.md) - Get started quickly
- [Agentic Integration](concepts/agentic-integration.md) - Use with Claude Code
- [JSON Schema](api/json-schema.md) - Complete JSON output spec
- [Pattern Format](api/pattern-format.md) - Create custom patterns
- [Monitoring Guide](guides/monitoring.md) - Advanced monitoring techniques
