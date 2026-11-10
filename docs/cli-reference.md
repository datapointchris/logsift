# CLI Reference

Complete command-line reference for logsift.

## Global Options

Available for all commands:

```bash
logsift [OPTIONS] COMMAND [ARGS]...
```

- `-V, --version` - Display the logsift version

**Examples:**

```bash
# Display version
logsift --version
logsift -V
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
- `--format FORMAT` - Output format: `auto`, `json`, `toon`, `markdown`, or `plain`, which prints the same Markdown (default: `auto`)
- `--stream` - Stream all output to terminal in real-time (default: show periodic updates)
- `--update-interval SECONDS` - Seconds between progress updates when not streaming (default: 60)
- `--minimal` - Suppress all progress output, only show final analysis (ideal for LLM workflows)
- `--notify` - Send desktop notification on completion (requires notify-send or osascript)
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

# Append to existing log for debugging
logsift monitor --append -- pytest tests/test_feature.py
```

**Behavior:**

1. Runs the command and captures all output (stdout + stderr)
2. Saves the raw log to `$XDG_CACHE_HOME/logsift/raw/<timestamp>-<name>.log` (default `~/.cache/logsift`)
3. Analyzes output for errors, warnings, and patterns
4. Prints the analysis in the chosen format
5. Exits with command's exit code (0 for success, non-zero for failure)

**Auto-Format Detection:**

- **Terminal (TTY)**: Markdown
- **Piped/headless**: compact toon for LLM consumption. Pass `--format json` for JSON.

```bash
# Terminal → Markdown
logsift monitor -- make build

# JSON for jq
logsift monitor --minimal --format json -- make build | jq '.errors'
```

### `analyze`

Analyze an existing log file.

```bash
logsift analyze [OPTIONS] LOG_FILE
```

**Arguments:**

- `LOG_FILE` - Path to log file to analyze (required)

**Options:**

- `--format FORMAT` - Output format: `auto`, `json`, `toon`, `markdown`, or `plain`, which prints the same Markdown (default: `auto`)

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

- **TTY (terminal)**: Markdown
- **Non-TTY (piped)**: toon, a compact text form for LLM consumption

```bash
# Auto-detects terminal → Markdown
logsift analyze app.log

# Auto-detects pipe → toon
logsift analyze app.log | head
```

### toon (`--format=toon`)

The compact form an agent reads with the fewest tokens. Each issue keeps its id, severity, line,
message, code and suggestion. It drops `pattern_name`, `tags`, `file_references` and the context
lines, so a program that needs those asks for JSON.

### JSON (`--format=json`)

Structured JSON for scripts and programs. Its shape is
[`schemas/analysis.schema.json`](https://github.com/datapointchris/logsift/blob/main/schemas/analysis.schema.json),
and [JSON Schema](api/json-schema.md) says how to read it. `monitor` adds a `summary` of the run that
`analyze` does not have.

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

```text

**Message:**
Module not found: Error: Can't resolve './missing.js'

**Suggestion:**
Create the missing file or fix the import path

**Tags**: webpack, import, fixable
```

## Cache and Configuration

### Cache Location

Logs are saved to `$XDG_CACHE_HOME/logsift/`, else `~/.cache/logsift/`. One `monitor` run writes
four files that share a stem, its UTC start time and a name made from the command or `-n`:

```text
~/.cache/logsift/
├── raw/2024-01-15T10:30:00-npm-run-build.log    # what the command printed
├── json/2024-01-15T10:30:00-npm-run-build.json  # the analysis in each format
├── toon/2024-01-15T10:30:00-npm-run-build.toon
└── md/2024-01-15T10:30:00-npm-run-build.md
```

`logsift analyze <file>` writes only the `json/`, `toon/` and `md/` files, named after the log
file. `logsift logs list`, `logs latest` and `logs browse` read `raw/`, and `logsift analyzed`
reads `json/`.

### Cache Cleanup

```bash
logsift logs clean              # Clean >90 days (default)
logsift logs clean --days=30    # Custom retention
logsift logs clean --dry-run    # List what would be deleted
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

Every run tries patterns in this order, and the first to match a line wins:

1. Custom patterns: `$XDG_CONFIG_HOME/logsift/patterns/*.toml`, else `~/.config/logsift/patterns/*.toml`
2. Built-in patterns: `src/logsift/patterns/defaults/*.toml`, with `common.toml` last

A custom file that fails validation stops the run, and the error names the file.

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

### Cache

- `XDG_CACHE_HOME` - logsift keeps its cache in `$XDG_CACHE_HOME/logsift`, else `~/.cache/logsift`

### Monitor Command

- `LOGSIFT_SESSION_NAME` - Default session name for monitor command
- `LOGSIFT_OUTPUT_FORMAT` - Default output format for `monitor` and `analyze`: `auto`, `json`, `toon`, `markdown`, `plain`
- `LOGSIFT_UPDATE_INTERVAL` - Default update interval in seconds (default: 60)

**Examples:**

```bash
# Use a custom cache directory
export XDG_CACHE_HOME=/tmp/cache
logsift monitor -- make build

# Force JSON output globally
export LOGSIFT_OUTPUT_FORMAT=json
logsift monitor -- npm test
```

## Performance Considerations

### Large Log Files

For very large log files (>100 MB):

- Analysis may take several seconds
- Memory usage scales with file size, because the whole file is read first

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

## Integration with Other Tools

### jq (JSON Processing)

```bash
# Extract first error message
logsift analyze app.log --format=json | jq -r '.errors[0].message'

# Count errors by severity
logsift analyze app.log --format=json | jq '.stats.total_errors'

# Get all file references
logsift analyze app.log --format=json | jq -r '.errors[].file_references[]? | "\(.[0]):\(.[1])"'
```

### fzf (Fuzzy Finding)

`logsift logs browse` and `logsift analyze browse` pick a cached log with fzf.

```bash
# Interactively select a cached log
logsift logs list | fzf

# Jump to error in editor
logsift analyze app.log --format=json | jq -r '.errors[].file_references[]? | "+\(.[1]) \(.[0])"' | fzf | xargs -o vim
```

### Claude Code

Use with Claude Code for automated workflows:

```python
# An agent reads the errors, then decides the fix itself
result = subprocess.run(['logsift', 'monitor', '--minimal', '--format=json', '--', 'npm', 'run', 'build'], capture_output=True, text=True)
analysis = json.loads(result.stdout)

for error in analysis['errors']:
    print(error['message'], error.get('suggestion', ''))
```

See [Agentic Integration](concepts/agentic-integration.md) for complete workflows.

## Tips and Best Practices

1. **Use `--format=json` for scripting** - Stable schema, easy to parse
2. **Name monitoring sessions** - Use `-n` for better organization
3. **Let auto-format work** - Markdown on a terminal, toon for an agent reading piped output
4. **Pipe `--format=json` to jq** - Extract specific fields from JSON output
5. **Create custom patterns** - Domain-specific error detection
6. **Clean cache regularly** - Prevent disk space issues

## See Also

- [5-Minute Quickstart](quickstart.md) - Get started quickly
- [Agentic Integration](concepts/agentic-integration.md) - Use with Claude Code
- [JSON Schema](api/json-schema.md) - Complete JSON output spec
- [Pattern Format](api/pattern-format.md) - Create custom patterns
- [Monitoring Guide](guides/monitoring.md) - Advanced monitoring techniques
