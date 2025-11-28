# logsift Documentation

Welcome to the official documentation for **logsift** - an intelligent log analysis tool designed specifically for LLM-driven automated workflows.

## What is logsift?

logsift transforms verbose command output (2000+ lines) into actionable intelligence (20-50 lines) optimized for AI agents like Claude Code. It extracts errors, warnings, file references, and provides structured fix suggestions - enabling fully automated diagnose-fix-retry loops.

## Key Features

- **LLM-First Design**: JSON output optimized for agent consumption
- **Smart Pattern Matching**: Built-in patterns for common tools (Python, npm, cargo, brew, apt)
- **Context Extraction**: Automatically captures ±2 lines around errors
- **File References**: Extracts `file:line` references for direct editing
- **Actionable Suggestions**: Pattern-based fix hints for automated workflows
- **Process Monitoring**: Run commands and analyze output automatically
- **Dual Output Modes**: JSON for agents, beautiful Markdown for humans

## Quick Links

### Getting Started

- [5-Minute Quickstart](quickstart.md) - Get up and running fast
- [Installation Guide](installation.md) - Detailed installation instructions
- [CLI Reference](cli-reference.md) - Complete command documentation

### Core Concepts

- [Agentic Integration](concepts/agentic-integration.md) ⭐ Using with Claude Code
- [Output Modes](concepts/output-modes.md) - JSON vs Markdown
- [Pattern Matching](concepts/pattern-matching.md) - How patterns work

### How-To Guides

- [Structured Logging](guides/structured-logging.md) ⭐ Write log-friendly scripts
- [Custom Patterns](guides/custom-patterns.md) - Create your own patterns
- [Process Monitoring](guides/monitoring.md) - Monitor commands effectively

### Architecture

- [Design Principles](architecture/design-principles.md) - Why logsift works this way
- [Data Flow](architecture/data-flow.md) - How analysis works internally

### API Reference

- [JSON Schema](api/json-schema.md) - Output format specification
- [Pattern Format](api/pattern-format.md) - TOML pattern file spec
- [Config Format](api/config-format.md) - Configuration file spec

### Development

- [Development Setup](development/setup.md) - Contributing guide
- [Testing Guide](development/testing.md) - How to test
- [Code Patterns](development/patterns.md) - Code standards

## The Problem logsift Solves

When running installations, builds, or tests, current tools dump thousands of lines that:

- Burn precious LLM context windows
- Make error extraction difficult
- Provide no structured actionable information
- Require manual reading and interpretation

## The logsift Solution

```bash
Command produces 2000 lines → logsift extracts 20-50 lines
✅ Errors with file:line references
✅ Context around errors (±2 lines)
✅ Actionable fix suggestions
✅ JSON for LLMs + Markdown for humans
✅ Enables automated fix/retry loops
```

## Project Status

**Current Version**: 0.1.0 (Alpha)

- ✅ **Phase 1 Complete**: Core Analyzer + Basic Monitor (MVP)
- ✅ **Phase 2 Complete**: Enhanced features (validation, monitoring, cache)
- 📋 **Phase 3 Planned**: MCP Server & Remote Monitoring
- 📋 **Phase 4 Planned**: Advanced Features (streaming, web UI)

**Test Coverage**: 85% (245 tests passing)

## Use Cases

### For AI Agents

Enable Claude Code and other AI agents to autonomously:

1. Run commands with `logsift monitor`
2. Get structured JSON with errors and fix suggestions
3. Apply fixes automatically
4. Retry and validate success
5. Repeat until success or escalate

### For Developers

Get actionable insights from logs without reading thousands of lines:

```bash
# Monitor a build and get only the errors
logsift monitor -- npm run build

# Analyze an existing log file
logsift analyze /var/log/app.log

# Get JSON for scripting
logsift analyze build.log --format=json | jq '.errors[0].suggestion'
```

## Philosophy

logsift follows these core principles:

1. **LLM-First**: Primary user is AI agents, secondary is humans
2. **Fail Fast**: No defensive coding - let it fail if misconfigured
3. **Universal Compatibility**: Works with ANY log format
4. **Extensible Patterns**: TOML-based pattern libraries (built-in + custom)
5. **Dual Output**: Auto-detects TTY for optimal format

## Community

- **GitHub**: [github.com/datapointchris/logsift](https://github.com/datapointchris/logsift)
- **Issues**: [Report bugs or request features](https://github.com/datapointchris/logsift/issues)
- **Contributing**: See [Development Setup](development/setup.md)

## License

MIT License - see [LICENSE](https://github.com/datapointchris/logsift/blob/main/LICENSE)

---

**Ready to get started?** Head to the [5-Minute Quickstart](quickstart.md) or dive into [Agentic Integration](concepts/agentic-integration.md) to see logsift in action with Claude Code.
