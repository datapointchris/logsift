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
# A benign line that a catch-all such as "error" would otherwise report. info reports nothing.
[[patterns]]
name = "myapp_retry_error_logged"
regex = "retrying after transient error"
severity = "info"
description = "A retry the client recovers from"
tags = ["myapp"]

[[patterns]]
name = "myapp_database_error"
regex = "DATABASE ERROR (?P<code>DB\\d+): (.+)"
severity = "error"
description = "Database connection or query error"
tags = ["database", "myapp"]
suggestion = "Check database connection string and credentials"

[[patterns]]
name = "myapp_slow_query"
regex = "slow query \\((\\d+) ms\\)"
severity = "warning"
description = "A query slower than the configured threshold"
tags = ["database", "myapp", "performance"]
```

Every run reads each `.toml` file in `$XDG_CONFIG_HOME/logsift/patterns/`, which defaults to
`~/.config/logsift/patterns/`. A file holds as many `[[patterns]]` entries as it needs, and a tag
may repeat across them. The first pattern to match a line decides it: entries in file order,
your files before the built-in ones. So put a specific pattern above a general one. A group named
`code` becomes the issue's `code`, here `DB1042` from `DATABASE ERROR DB1042: ...`. A file that
fails validation stops the run, and the error names the file.

### Configuration

logsift runs on its defaults, and reads `$XDG_CONFIG_HOME/logsift/config.toml`, else
`~/.config/logsift/config.toml`, when it exists. Each key below is set to logsift's default:

```toml
# How monitor and analyze print the analysis: auto, json, toon or markdown.
print_analysis_as = "auto"

[monitor]
# Seconds between monitor's progress reports.
report_progress_every_seconds = 60

[logs.clean]
# `logsift logs clean` deletes raw logs older than this many days.
delete_older_than_days = 90

[analyzed.clean]
# `logsift analyzed clean` deletes saved analyses older than this many days.
delete_older_than_days = 30
```

A flag beats its `LOGSIFT_*` variable, which beats the file. `logsift config` prints each value and
the layer that set it. A file that fails to parse, or names a key logsift does not read, stops
every command and names the problem. [Config Format](docs/api/config-format.md) has the details.

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

`logsift logs list` lists the raw logs, and `logsift analyze --latest` re-runs the patterns over the
newest one.

Clean old raw logs (older than 90 days by default) and old analyses (older than 30 days):

```bash
logsift logs clean --dry-run   # list what would go
logsift logs clean --days 30
logsift analyzed clean
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
which logsift          # Inside the directory `uv tool dir --bin` prints
logsift --version      # Prints the installed version
logsift --help         # Show all commands
```

**Uninstall:**

```bash
uv tool uninstall logsift
```

### Optional Programs

logsift starts four programs when they are on `PATH`, and works without each:

- `fzf`: the `choose` commands pick a file with it. Without it they exit 1 and say to install it.
- `bat`: `latest` and `choose` page a file through it. Without it the file prints as plain text.
- `notify-send` on Linux, `osascript` on macOS: `monitor --notify` posts through it. Without it
  monitor says on stderr that no notification was sent.

### Troubleshooting Installation

**Command not found after install:** uv's tool bin directory is not on `PATH`.

```bash
uv tool dir --bin       # the directory uv installed logsift into
uv tool update-shell    # add it to your shell's PATH, then open a new shell
```

**Permission errors:** logsift writes every run under the directory `logsift config` names on its
`cache` row. Make sure you own it and can write to it.

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
`task test:coverage` prints the current coverage.

## Documentation

- [Development Setup](docs/development/setup.md) - For contributors
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
task setup   # the dev and test groups, and the commit and commit-msg hooks
task test
```

[Development Setup](docs/development/setup.md) has the workflow through to a pull request.

## Architecture

logsift is built with a modular architecture:

- **Core Engine**: Log parsing, pattern matching, context extraction
- **Pattern System**: Extensible TOML-based pattern libraries with validation
- **Output Formatters**: toon for an agent reading piped output, JSON for a program, Markdown for a person
- **Process Monitor**: Runs the command, saves what it prints, and analyzes it
- **Cache System**: One directory per kind of saved file, trimmed by `logs clean` and `analyzed clean`

**Data Flow:**

```bash
Input → Parser (auto-detect format) → Pattern Matching (TOML rules) →
Context Extraction (±2 lines) → Output (toon when piped, JSON on request, Markdown on a terminal)
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **GitHub**: [https://github.com/datapointchris/logsift](https://github.com/datapointchris/logsift)
- **Issues**: [https://github.com/datapointchris/logsift/issues](https://github.com/datapointchris/logsift/issues)

## Vision

Make log analysis intelligent, efficient, and LLM-friendly to enable fully automated software development workflows.

---

Built with Python 3.13+, Typer, and the hatchling build backend.
