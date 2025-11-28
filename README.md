# logsift

> Intelligent log analysis for agentic workflows

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
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

## Features

- **Dual Output Modes**: JSON for LLMs, beautiful Markdown for humans
- **Smart Pattern Matching**: Built-in patterns for common tools (brew, apt, npm, cargo, etc.)
- **Context Extraction**: Automatically extracts relevant lines around errors
- **File References**: Extracts file:line references for direct editing
- **Actionable Suggestions**: Provides fix suggestions when patterns are recognized
- **Process Monitoring**: Run commands and automatically analyze output
- **Live Watching**: Monitor log files in real-time
- **Extensible**: Add custom pattern libraries for domain-specific errors

## Installation

### With uv (recommended)

```bash
uv tool install logsift
```

### With pipx

```bash
pipx install logsift
```

### Development Installation

```bash
git clone https://github.com/datapointchris/logsift.git
cd logsift
uv sync
```

## Quick Start

### Analyze an existing log file

```bash
logsift analyze /var/log/app.log
```

### Monitor a command

```bash
logsift monitor -- make build
logsift monitor -n install -i 30 -- task install
```

### Watch a log file in real-time

```bash
logsift watch /var/log/app.log
```

## Usage Examples

### For LLM Automation (Claude Code)

```bash
# Automatically outputs JSON in headless mode
logsift monitor -- task install > result.json
```

### For Human Terminal Use

```bash
# Automatically outputs beautiful Markdown
logsift monitor -- task install
```

### Dual Output (Best of Both)

```bash
# Stream readable output, save JSON for later
logsift monitor --stream -- task install
```

## Project Status

**Current Version**: 0.1.0 (Alpha)

This project is in active development. Phase 1 (Core Analyzer + Basic Monitor) is currently being implemented.

See [PLANNING.md](PLANNING.md) for the complete roadmap and implementation plan.

## Development Phases

- **Phase 1** (Current): Core Analyzer + Basic Monitor (MVP)
- **Phase 2**: Enhanced features (pattern libraries, dual output, streaming)
- **Phase 3**: MCP Server & Remote Monitoring (Claude Code native integration)

## Documentation

- [Planning Document](PLANNING.md) - Complete project vision and roadmap
- CLI Reference - Coming soon
- Pattern Format - Coming soon
- API Documentation - Coming soon

## Contributing

Contributions are welcome! This project is in early development.

Areas where contributions would be especially valuable:

- Pattern libraries for additional tools and languages
- Test coverage improvements
- Documentation
- Real-world log samples for testing

## Architecture

logsift is built with a modular architecture:

- **Core Engine**: Log parsing, pattern matching, context extraction
- **Pattern System**: Extensible pattern libraries for error detection
- **Output Formatters**: JSON (LLM-optimized) and Markdown (human-readable)
- **Process Monitor**: Command execution and output capture
- **Cache System**: Organized log storage and management

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **GitHub**: [https://github.com/datapointchris/logsift](https://github.com/datapointchris/logsift)
- **Issues**: [https://github.com/datapointchris/logsift/issues](https://github.com/datapointchris/logsift/issues)

## Vision

Make log analysis intelligent, efficient, and LLM-friendly to enable fully automated software development workflows.

---

Built with Python 3.11+, Typer, and the uv build backend.
