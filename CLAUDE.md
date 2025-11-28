# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**logsift** is an LLM-optimized log analysis tool designed to enable Claude Code and other AI agents to diagnose and fix errors autonomously. It extracts 20-50 actionable lines from 2000+ line logs, providing structured JSON for agents and beautiful Markdown for humans.

**Core Mission**: Primary user is LLMs (structured JSON output), secondary is humans (readable Markdown). This is NOT a general-purpose log viewer - it's built specifically for automated fix/retry workflows.

## Critical Rules

### Git Safety Protocol

- NEVER run `git rebase`, `git push --force`, or `git reset --hard` unless explicitly requested
- NEVER use `--no-verify` to bypass pre-commit hooks - fix issues instead
- NEVER push to remote repositories unless explicitly requested
- NEVER amend commits that have been pushed - use new commits instead
- Always check `git status` before destructive operations
- Pre-commit hooks exist for quality control - respect them

### Git Commit Messages

- NEVER add "Generated with Claude Code" or AI tool attribution
- NEVER add "Co-Authored-By: Claude" lines
- Keep commits clean and professional

### Git Hygiene (⚠️ CRITICAL - Perfect git hygiene is non-negotiable)

- ALWAYS review what will be committed: `git status`, `git diff --staged` before every commit
- NEVER use `git add -A` or `git add .` without carefully reviewing what's being staged
- ONLY stage files relevant to the specific change - use explicit `git add <file>` for each file
- Each commit must be atomic and focused on ONE logical change
- If something goes wrong, STOP and figure out the correct solution - do not rush
- Do not create commits that mix unrelated changes or that will need to be fixed later
- Take time to ensure commits are correct the first time

### Problem Solving Philosophy

- Solve root causes, not symptoms - no band-aid solutions
- Think through issues before adding code - analyze existing behavior first
- Test minimal changes instead of complex workarounds
- DRY principles - avoid duplication and unnecessary abstractions
- When debugging, check existing patterns and similar code first

## Development Commands

### Environment Setup

```bash
# Install dependencies
uv sync --group dev --group test

# Install pre-commit hooks
uv run pre-commit install --install-hooks
uv run pre-commit install --hook-type commit-msg
```

### Testing

```bash
# Run all tests
uv run python -m pytest -v

# Run with coverage
uv run python -m pytest --cov=logsift --cov-report=term

# Run specific test file
uv run python -m pytest tests/unit/test_parser.py -v

# Run specific test
uv run python -m pytest tests/unit/test_parser.py::test_parser_initialization -v
```

### Linting and Formatting

```bash
# Run all pre-commit checks
uv run pre-commit run --all-files

# Run ruff linting
uv run ruff check src/ tests/

# Run ruff formatting
uv run ruff format src/ tests/

# Run type checking
uv run mypy src/logsift --config-file pyproject.toml

# Run security scanning
uv run bandit -c pyproject.toml -r .
```

### Building

```bash
# Build package (creates wheel and sdist in dist/)
uv build

# Install locally in editable mode
uv sync
```

### Running the CLI

```bash
# Run CLI directly
uv run logsift --version
uv run logsift --help

# Run specific commands (currently stubs)
uv run logsift monitor -- echo "test"
uv run logsift analyze /path/to/log.log
```

## Architecture

### Design Principles (CRITICAL)

1. **Core is Analysis** - Log parsing/pattern matching is primary; monitoring is convenience wrapper
2. **LLM-First Output** - JSON schema optimized for agent consumption with predictable structure
3. **Dual Output Modes** - Auto-detects TTY: JSON for headless (agents), Markdown for interactive (humans)
4. **Extensible Patterns** - TOML-based pattern libraries (built-in + custom from `~/.config/logsift/patterns/`)
5. **Universal Compatibility** - Works with ANY log format (JSON, structured, plain text)
6. **Fail Fast** - No defensive coding with inline defaults; let it fail if misconfigured

### Module Organization

```
src/logsift/
├── cli.py              # Typer CLI entry point (app = typer.Typer())
├── commands/           # CLI command implementations (monitor, analyze, watch, patterns, logs)
├── core/               # Analysis pipeline
│   ├── parser.py       # Auto-detect format, normalize to internal representation
│   ├── extractors.py   # Extract errors, warnings, file:line references
│   ├── matchers.py     # Apply pattern rules to detect known error types
│   ├── context.py      # Extract ±N lines around errors
│   └── analyzer.py     # Orchestrates the analysis pipeline
├── patterns/           # Pattern library system
│   ├── loader.py       # Load TOML pattern files
│   ├── matcher.py      # Apply patterns to logs
│   ├── validator.py    # Validate pattern file format
│   └── defaults/       # Built-in patterns (common.toml, brew.toml, apt.toml)
├── output/             # Dual output formatters
│   ├── json_formatter.py     # LLM-optimized structured output
│   ├── markdown_formatter.py # Human-readable colored output
│   ├── plain_formatter.py    # Fallback for piping
│   └── streaming.py          # Dual-stream manager (JSON to file, Markdown to stdout)
├── monitor/            # Process monitoring (optional convenience)
│   ├── process.py      # Run commands, capture output (uses sh library)
│   ├── watcher.py      # Live log tailing
│   └── remote.py       # Remote SSH monitoring (Phase 3)
├── config/             # Configuration management
│   ├── defaults.py     # DEFAULT_CONFIG dict with all settings
│   ├── loader.py       # Load from ~/.config/logsift/config.toml
│   └── validator.py    # Validate config structure
├── cache/              # Log storage
│   ├── manager.py      # ~/.cache/logsift/context/name-timestamp.log structure
│   ├── rotation.py     # Cleanup based on retention policy
│   └── metadata.py     # Track log metadata
├── utils/              # Utilities
│   ├── tty.py          # TTY detection (is_interactive(), detect_output_format())
│   ├── colors.py       # Rich console helpers (print_error, print_warning, etc.)
│   └── timestamps.py   # Parse/format timestamps, format_duration()
└── mcp/                # MCP server for Claude Code native integration (Phase 3)
```

### Data Flow (Critical to Understand)

```
Input → Parser (auto-detect format) → Pattern Matching (apply .toml rules) →
Context Extraction (±2 lines) → Dual Output (JSON for LLMs, Markdown for humans)
```

**Key insight**: Analysis happens in `core/`, output format selection in `utils/tty.py`, actual formatting in `output/`. Commands in `commands/` orchestrate but don't implement logic.

## Pattern Library System

Pattern files are **TOML** in `src/logsift/patterns/defaults/`:

```toml
[[patterns]]
name = "brew_package_already_installed"
regex = "Error:\\s*(.+)\\s+is already installed"
severity = "error"
description = "Package is already installed"
tags = ["brew", "package_conflict", "fixable"]
suggestion = "Remove package from install list or use 'brew upgrade' instead"
```

**Required fields**: name, regex, severity, description, tags
**Optional fields**: suggestion (for automated fix hints)

Custom patterns load from `~/.config/logsift/patterns/*.toml` and merge with built-in.

## JSON Output Schema (CRITICAL - DO NOT CHANGE)

LLMs depend on this stable structure:

```json
{
  "summary": {
    "status": "failed|success",
    "exit_code": int,
    "duration_seconds": float,
    "command": "string",
    "timestamp": "ISO8601",
    "log_file": "path"
  },
  "errors": [
    {
      "id": int,
      "severity": "error|warning",
      "line_in_log": int,
      "message": "string",
      "file": "path (optional)",
      "file_line": int (optional),
      "context_before": ["lines"],
      "context_after": ["lines"],
      "suggestion": {
        "action": "string",
        "description": "string",
        "confidence": "high|medium|low",
        "automated_fix": "shell command (optional)"
      },
      "pattern_matched": "pattern_name",
      "tags": ["tag1", "tag2"]
    }
  ],
  "actionable_items": [
    {
      "priority": int,
      "file": "path",
      "line": int,
      "action": "string",
      "description": "string",
      "automated": bool
    }
  ],
  "stats": {
    "total_errors": int,
    "total_warnings": int,
    "fixable_errors": int,
    "log_size_bytes": int,
    "log_lines": int
  }
}
```

## Development Standards

### Code Quality (Non-Negotiable)

- **PEP 8** style, **Google-style docstrings** for public functions
- **Type hints** using Python 3.11+ syntax (`list[str]` not `List[str]`)
- **Fail fast** - raise specific exceptions, no inline defaults/fallbacks
- **No defensive coding** - `config.key` not `getattr(config, 'key', 'default')`
- **All code must pass pre-commit hooks** before committing

### Testing Philosophy

- **Target coverage: 80%** (currently 40% due to stub implementations - will increase)
- **Test behavior, not implementation** - verify outputs/effects, not internal calls
- **Use pytest fixtures** - see `tests/conftest.py` for shared fixtures
- **Real log samples** - put in `tests/fixtures/sample_logs/` for integration tests

### Pre-commit Hooks (15 total)

Must pass before committing:

- Conventional commits (commit-msg format)
- actionlint (GitHub Actions validation)
- uv-lock (dependency sync check)
- ruff (lint + format)
- codespell, bandit, markdownlint, shellcheck
- refurb, pyupgrade, mypy

### Commit Message Format

Use conventional commits:

```
feat: add npm error pattern library
fix: correct file reference extraction regex
docs: update pattern format documentation
test: add integration tests for analyze command
chore: update dependencies to latest versions
```

## Implementation Status

**Phase 1 (Current)**: Core Analyzer + Basic Monitor - Most modules are **stubs** raising `NotImplementedError`. This is intentional scaffolding.

**When implementing**:

1. Write tests FIRST (TDD approach)
2. Implement functionality in `core/`, `patterns/`, `output/`
3. Wire up in `commands/` to CLI
4. Update coverage threshold in pyproject.toml as coverage increases (currently 40%, target 80%)

**Phase 2**: Enhanced features (custom pattern loading, streaming, fzf integration)
**Phase 3**: MCP server for native Claude Code integration

## Critical Gotchas

1. **Coverage threshold**: Set to 40% for Phase 1 stubs. Increase to 60% → 70% → 80% as implementation progresses.
2. **Output format stability**: JSON schema is a contract with LLMs - changes require major version bump.
3. **Pattern files are TOML**: Not YAML, not JSON. Use `tomllib` (stdlib 3.11+) for reading.
4. **TTY detection determines format**: `sys.stdout.isatty()` → Markdown if True, JSON if False.
5. **sh library for process monitoring**: Not `subprocess` - see `sh` library docs for clean interface.
6. **Type hints use modern syntax**: `list[str]`, `dict[str, Any]`, `str | None` (not `Optional[str]`)

## Configuration Files

- `pyproject.toml` - Project metadata, dependencies, all tool configs (ruff, mypy, pytest, coverage, bandit)
- `.python-version` - Python 3.11 (required for stdlib TOML support)
- `.pre-commit-config.yaml` - 15 pre-commit hooks
- `.markdownlint.json` - Markdown linting rules (allows long lines in docs)
- `.shellcheckrc` - Shell script linting config
- `.dockerignore` - Docker build exclusions (for future containerization)

## Key Resources

- **PLANNING.md** - Complete project vision, architecture, implementation phases
- **README.md** - Quick start, installation, usage examples
- **Pattern examples** - `src/logsift/patterns/defaults/*.toml`
- **Test fixtures** - `tests/fixtures/sample_logs/` for real-world examples

## Documentation Philosophy

When creating documentation for logsift (if adding docs/ directory in future):

### Writing Guidelines

- ALWAYS write in the imperative tone:
  - Good: "Copy the config file"
  - Bad: "You should copy the config file"
  - Bad: "Now you can copy the config file"
- WHY over WHAT - explain decisions and trade-offs, not just commands
- Conversational paragraphs over bulleted lists - maintain context and reasoning
- Reference files instead of copying code examples when possible
- Technical and factual, not promotional
- Keep markdown files lowercase: `pattern-format.md` NOT `PATTERN_FORMAT.md`
- Exceptions: `README.md` and `CLAUDE.md` (standard conventions)

### Learnings Directory Pattern

When documenting critical lessons learned, create focused learning documents (30-50 lines max):

1. **Title and context** (1-2 lines)
2. **The Problem** (2-4 lines + minimal code)
3. **The Solution** (2-4 lines + code)
4. **Key Learnings** (3-5 actionable bullets)
5. **Testing** (optional, 5-10 lines)
6. **Related links** (1-2 lines)

Focus on what future you needs to remember, not comprehensive guides. Document critical bugs, best practices to follow consistently, common pitfalls, tool gotchas.

## NO Defensive Coding Rule

**CRITICAL**: This project follows "fail fast" philosophy:

❌ **WRONG**: `value = getattr(config, 'key', 'default')`
✅ **RIGHT**: `value = config.key` (let it raise AttributeError if misconfigured)

❌ **WRONG**: `return data.get('field', [])`
✅ **RIGHT**: `return data['field']` (let it raise KeyError if malformed)

Configuration validation happens once at startup in `config/validator.py`. Business logic should assume valid configuration and fail loudly if assumptions are violated.
