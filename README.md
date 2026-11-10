# logsift

> Intelligent log analysis for agentic workflows

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**logsift** is an LLM-optimized log analysis and command monitoring tool designed specifically for Claude Code and other AI agents to efficiently diagnose, fix, and retry failed operations with minimal context overhead.

## The Problem

When running long commands (installations, builds, tests), current tools dump 2000+ lines of verbose output that:

- Burns LLM context window
- Makes error extraction difficult
- Provides no structured actionable information
- Requires manual reading and interpretation

## The Solution

```bash
Command produces 2000 lines → logsift extracts 20-50 lines
✅ Errors with file:line references
✅ Context around errors (±2 lines)
✅ Actionable fix suggestions
✅ toon for LLMs, JSON for programs, Markdown for humans
✅ Enables automated fix/retry loops
```

## Quick Start

```bash
# Monitor a command and analyze its output
logsift monitor -- make build

# Analyze an existing log file
logsift analyze /var/log/app.log

# Monitor with custom name and JSON output
logsift monitor -n my-build --format=json -- npm run build
```

## Usage

### Analyze Command

Analyze an existing log file:

```bash
# Auto-detect output format (toon when piped, Markdown on a terminal)
logsift analyze /var/log/app.log

# Force JSON output (for LLMs)
logsift analyze build.log --format=json

# Force Markdown output (for humans)
logsift analyze build.log --format=markdown
```

### Monitor Command

Execute a command, capture output, and analyze:

```bash
# Monitor a build command
logsift monitor -- make build

# Monitor with custom name (for cache organization)
logsift monitor -n my-project -- npm run build

# Monitor with JSON output
logsift monitor --format=json -- cargo test

# Real-world examples
logsift monitor -- pytest tests/
logsift monitor -n deploy -- task deploy-staging
logsift monitor -- uv run python -m pytest --cov=myapp
```

**How it works:**

1. Runs the command and captures all output
2. Analyzes output for errors, warnings, and patterns
3. Saves the raw log to `$XDG_CACHE_HOME/logsift/raw/<timestamp>-<name>.log` (default
   `~/.cache/logsift`), and the analysis under `json/`, `toon/` and `md/` with the same stem
4. Prints the analysis in the chosen format

### Watching a Growing Log

`analyze --stream` analyzes the whole file, then keeps analyzing as it grows:

```bash
logsift analyze --stream /var/log/app.log
```

### Output Formats

**Auto-detection** (recommended):

- **Terminal (TTY)**: Markdown
- **Piped/headless**: compact toon for LLM consumption. Pass `--format json` for JSON.

```bash
# Terminal → Markdown
logsift analyze app.log

# Piped → toon
logsift analyze app.log | head

# JSON for jq
logsift analyze app.log --format json | jq '.errors[0]'
```

**Force specific format:**

```bash
logsift analyze app.log --format=json
logsift analyze app.log --format=markdown
```

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

Every run reads each `.toml` file in `$XDG_CONFIG_HOME/logsift/patterns/`, which defaults to
`~/.config/logsift/patterns/`. Your patterns are tried before the built-in ones, so yours wins a
line both match. A file that fails validation stops the run, and the error names the file.

### Configuration

Create `~/.config/logsift/config.toml` to customize settings:

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

### Cache Management

Every `monitor` run saves to `$XDG_CACHE_HOME/logsift/`, else `~/.cache/logsift/`. One run's
files share a stem, its UTC start time and a name made from the command:

```text
~/.cache/logsift/
  ├── raw/    2025-11-28T14:30:22-make-build.log    # what the command printed
  ├── json/   2025-11-28T14:30:22-make-build.json   # the analysis, as --format json prints it
  ├── toon/   2025-11-28T14:30:22-make-build.toon
  └── md/     2025-11-28T14:30:22-make-build.md
```

`logsift logs list` lists the raw logs, and `logsift analyze latest` re-runs the patterns over the
newest one.

Clean old logs (older than 90 days by default):

```bash
logsift logs clean --dry-run   # list what would go
logsift logs clean --days 30
```

## Installation

### From the Package Index

Every release is published to a package index of its own:

```bash
uv tool install --index https://pypi.ichrisbirch.com/simple/ logsift
logsift update   # later: install the newest release over this one
```

Name the index on the install. Without it uv asks PyPI, where `logsift` is a different project.

### Local Installation with UV (Development)

Install logsift as a global tool for local testing and development:

```bash
# Clone the repository
git clone https://github.com/datapointchris/logsift.git
cd logsift

# Install as editable global tool
uv tool install --editable .
```

**Benefits:**

- Changes to source code are immediately reflected
- No need to reinstall after modifications
- `logsift` command available system-wide

**Verify installation:**

```bash
which logsift          # Should show ~/.local/bin/logsift
logsift --version      # Prints the installed version
logsift --help         # Show all commands
```

**Uninstall:**

```bash
uv tool uninstall logsift
```

### Troubleshooting Installation

**Command not found after install:**

Ensure `~/.local/bin` is in your PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**Permission errors:**

Check cache directory permissions:

```bash
mkdir -p ~/.cache/logsift
chmod 755 ~/.cache/logsift
```

## Features

- **Three Output Formats**: toon for LLMs, JSON for programs, Markdown for humans
- **Smart Pattern Matching**: Built-in patterns for common tools (Python, npm, cargo, etc.)
- **Context Extraction**: Automatically extracts context around errors (configurable per-pattern)
- **File References**: Extracts file:line references for direct editing
- **Error Code Extraction**: Automatically extracts linter codes (F401, SC2086, FURB101, etc.)
- **Hook Detection**: Identifies which pre-commit hooks passed/failed
- **Process Monitoring**: Run commands and automatically analyze output
- **Log Caching**: Automatic log storage with configurable retention
- **Custom Patterns**: Extensible pattern system for domain-specific errors
- **Auto-Format Detection**: Smart TTY detection for optimal output format

## Project Status

**Status**: Alpha. `logsift --version` prints the installed version, and
`uv run pytest --cov=logsift` prints the current coverage.

## Documentation

- [Development Guide](CLAUDE.md) - For Claude Code and contributors
- CLI Reference - See `logsift --help` and `logsift COMMAND --help`
- Pattern Format - See custom patterns section above

## Contributing

Contributions are welcome! This project is in active development.

Areas where contributions would be especially valuable:

- Pattern libraries for additional tools and languages
- Test coverage improvements
- Documentation
- Real-world log samples for testing

### Development Setup

```bash
git clone https://github.com/datapointchris/logsift.git
cd logsift

# Install dependencies
uv sync --group dev --group test

# Install pre-commit hooks
uv run pre-commit install --install-hooks

# Run tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=logsift --cov-report=term
```

## Architecture

logsift is built with a modular architecture:

- **Core Engine**: Log parsing, pattern matching, context extraction
- **Pattern System**: Extensible TOML-based pattern libraries with validation
- **Output Formatters**: JSON (LLM-optimized) and Markdown (human-readable)
- **Process Monitor**: Command execution and output capture via subprocess
- **Cache System**: Organized log storage with automatic rotation

**Data Flow:**

```bash
Input → Parser (auto-detect format) → Pattern Matching (TOML rules) →
Context Extraction (±2 lines) → Dual Output (JSON for LLMs, Markdown for humans)
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **GitHub**: [https://github.com/datapointchris/logsift](https://github.com/datapointchris/logsift)
- **Issues**: [https://github.com/datapointchris/logsift/issues](https://github.com/datapointchris/logsift/issues)

## Vision

Make log analysis intelligent, efficient, and LLM-friendly to enable fully automated software development workflows.

---

Built with Python 3.13+, Typer, and the uv build backend.
