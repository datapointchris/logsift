# 5-Minute Quickstart

Get up and running with logsift in 5 minutes.

## Installation

Install logsift as a global tool using UV:

```bash
# Clone the repository
git clone https://github.com/datapointchris/logsift.git
cd logsift

# Install as editable global tool
uv tool install --editable .
```

Verify installation:

```bash
logsift --version  # Should show: logsift version 0.1.0
```

## Your First Analysis

Let's analyze a simple command that produces errors:

```bash
# Monitor a command and analyze its output
logsift monitor -- python -c "import nonexistent_module"
```

The output shows:

- Summary of the command execution
- Extracted errors with context
- File references (if any)
- Actionable suggestions

## Monitor a Build

Monitor a real build command:

```bash
# Monitor npm build
logsift monitor -- npm run build

# Monitor with custom name for better organization
logsift monitor -n my-app-build -- npm run build

# Get JSON output for scripting
logsift monitor --format=json -- npm run build
```

The log is automatically saved to `~/.cache/logsift/monitor/` for later analysis.

## Analyze an Existing Log

Have an existing log file? Analyze it directly:

```bash
# Analyze a log file
logsift analyze /var/log/app.log

# Force JSON output (useful for piping to jq)
logsift analyze build.log --format=json

# Force Markdown output (even when piping)
logsift analyze build.log --format=markdown
```

## Understanding the Output

### Terminal Output (Markdown)

When running in a terminal, logsift outputs beautiful Markdown with colors:

```
# Analysis Summary

**Status**: failed
**Exit Code**: 1
**Duration**: 0.23s
**Command**: python -c import nonexistent_module

## Errors Found (1)

### Error 1: ModuleNotFoundError
**Severity**: error
**Line**: 3

```

ModuleNotFoundError: No module named 'nonexistent_module'

```

**Suggestion**: Install the missing module using pip
```

### JSON Output (for LLMs and Scripts)

When piped or with `--format=json`, logsift outputs structured JSON:

```json
{
  "summary": {
    "status": "failed",
    "exit_code": 1,
    "duration_seconds": 0.23,
    "command": "python -c import nonexistent_module"
  },
  "errors": [
    {
      "id": 1,
      "severity": "error",
      "line_in_log": 3,
      "message": "ModuleNotFoundError: No module named 'nonexistent_module'",
      "suggestion": {
        "action": "install_module",
        "description": "Install the missing module using pip"
      }
    }
  ],
  "stats": {
    "total_errors": 1,
    "total_warnings": 0
  }
}
```

## Auto-Format Detection

logsift automatically detects the best output format:

- **Terminal (TTY)**: Beautiful Markdown with colors
- **Piped/headless**: Structured JSON for processing

```bash
# Terminal → Markdown
logsift analyze app.log

# Piped → JSON automatically
logsift analyze app.log | jq '.errors[0].message'

# Force specific format
logsift analyze app.log --format=json
logsift analyze app.log --format=markdown
```

## Real-World Example: Python Tests

Monitor pytest with coverage:

```bash
logsift monitor -n pytest-run -- uv run pytest --cov=myapp tests/
```

If tests fail, logsift extracts:

- Failed test names with `file:line` references
- Assertion errors with context
- Missing dependencies
- Actionable fix suggestions

## Integration with Claude Code

The real power of logsift comes from agentic integration. Enable Claude Code to autonomously fix errors:

```python
# Claude Code workflow
1. Run: logsift monitor --format=json -- npm run build
2. Parse JSON to extract errors and suggestions
3. Apply suggested fixes automatically
4. Retry: logsift monitor --format=json -- npm run build
5. Repeat until success
```

See [Agentic Integration](concepts/agentic-integration.md) for complete workflows.

## Custom Patterns

Create custom patterns for domain-specific errors:

```bash
# Create custom pattern file
mkdir -p ~/.config/logsift/patterns
cat > ~/.config/logsift/patterns/myapp.toml << 'EOF'
[[patterns]]
name = "myapp_database_error"
regex = "DATABASE ERROR: (.+)"
severity = "error"
description = "Database connection or query error"
tags = ["database", "myapp"]
suggestion = "Check database connection string and credentials"
EOF
```

Patterns are automatically loaded and applied to all analyses.

See [Custom Patterns](guides/custom-patterns.md) for detailed guidance.

## Configuration

Customize behavior via `~/.config/logsift/config.toml`:

```toml
[cache]
directory = "~/.cache/logsift"
retention_days = 90

[analysis]
context_lines = 2
max_errors = 100

[output]
default_format = "auto"  # auto, json, markdown
```

See [Config Format](api/config-format.md) for all options.

## Cache Management

Logs are automatically saved to `~/.cache/logsift/monitor/`. Clean old logs:

```python
from logsift.cache.rotation import clean_old_logs
from pathlib import Path

# Clean logs older than 30 days
deleted = clean_old_logs(Path.home() / '.cache' / 'logsift', retention_days=30)
print(f"Deleted {deleted} old log files")
```

## Next Steps

Now that you have logsift running:

1. **[CLI Reference](cli-reference.md)** - Explore all commands and options
2. **[Agentic Integration](concepts/agentic-integration.md)** - Use with Claude Code
3. **[Structured Logging](guides/structured-logging.md)** - Write better logs
4. **[Custom Patterns](guides/custom-patterns.md)** - Create domain patterns

## Getting Help

- Run `logsift --help` for quick reference
- Check [CLI Reference](cli-reference.md) for detailed docs
- Report issues on [GitHub](https://github.com/datapointchris/logsift/issues)
