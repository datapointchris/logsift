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
✅ JSON for LLMs + Markdown for humans
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
# Auto-detect output format (JSON for pipes, Markdown for terminal)
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
3. Saves log to `~/.cache/logsift/monitor/`
4. Outputs structured analysis (JSON or Markdown)

### Watch Command

Watch a log file in real-time (Phase 3):

```bash
logsift watch /var/log/app.log
```

### Output Formats

**Auto-detection** (recommended):

- **Terminal (TTY)**: Beautiful Markdown with colors and formatting
- **Piped/headless**: Structured JSON for LLM consumption

```bash
# Terminal → Markdown
logsift analyze app.log

# Piped → JSON
logsift analyze app.log | jq '.errors[0]'
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

Patterns are automatically loaded and merged with built-in patterns.

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

Logs are automatically saved to `~/.cache/logsift/`:

```text
~/.cache/logsift/
  ├── monitor/          # Logs from monitored commands
  │   └── make-20231128_143022.log
  └── default/          # Other logs
```

Clean old logs (older than 90 days by default):

```python
from logsift.cache.rotation import clean_old_logs
from pathlib import Path

deleted = clean_old_logs(Path.home() / '.cache' / 'logsift', retention_days=30)
print(f"Deleted {deleted} old log files")
```

## Installation

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
logsift --version      # Should show version 0.1.0
logsift --help         # Show all commands
```

**Uninstall:**

```bash
uv tool uninstall logsift
```

### With uv (from PyPI - coming soon)

```bash
uv tool install logsift
```

### With pipx (from PyPI - coming soon)

```bash
pipx install logsift
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

- **Dual Output Modes**: JSON for LLMs, beautiful Markdown for humans
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

**Current Version**: 0.1.0 (Alpha)

✅ **Phase 1 Complete**: Core Analyzer + Basic Monitor (MVP)
✅ **Phase 2 Complete**: Enhanced features (pattern validation, monitoring, cache rotation)

**Test Coverage**: 85% (372 tests passing)

See [PLANNING.md](PLANNING.md) for the complete roadmap and implementation plan.

## Development Phases

- ✅ **Phase 1**: Core Analyzer + Basic Monitor (MVP) - **COMPLETE**
- ✅ **Phase 2**: Enhanced features (pattern validation, monitoring, cache rotation) - **COMPLETE**
- **Phase 3** (Planned): MCP Server & Remote Monitoring (Claude Code native integration)
- **Phase 4** (Planned): Advanced Features (streaming, fzf integration, web UI)

## Documentation

- [Planning Document](PLANNING.md) - Complete project vision and roadmap
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
