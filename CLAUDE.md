# CLAUDE.md

## Project Overview

**logsift** is an LLM-optimized log analysis tool. Extracts 20-50 actionable lines from 2000+ line logs. Primary user is LLMs (structured JSON), secondary is humans (Markdown). Built for automated fix/retry workflows, not general-purpose log viewing.

**Package Management**: uv (`uv.lock`). Python 3.13.

## Essential Commands

```bash
uv sync --group dev --group test          # Install deps
uv run pre-commit install --install-hooks # Install hooks
uv run pre-commit install --hook-type commit-msg

uv run python -m pytest -v                           # All tests
uv run python -m pytest tests/unit/test_parser.py -v  # Specific file
uv run python -m pytest --cov=logsift --cov-report=term # With coverage

uv run ruff check src/ tests/ && uv run ruff format src/ tests/
uv run mypy src/logsift --config-file pyproject.toml
uv run logsift monitor -- echo "test"     # CLI
```

## Design Principles

1. **Core is Analysis** — Log parsing/pattern matching is primary; monitoring is convenience wrapper
2. **LLM-First Output** — JSON schema optimized for agent consumption with predictable structure
3. **Dual Output Modes** — Auto-detects TTY: toon for headless (agents), Markdown for interactive (humans)
4. **Extensible Patterns** — TOML-based pattern libraries (built-in + custom from `~/.config/logsift/patterns/`)
5. **Universal Compatibility** — Works with ANY log format (JSON, structured, plain text)
6. **Fail Fast** — No defensive coding with inline defaults; let it fail if misconfigured

## Pattern Matching — Single Source of Truth (⚠️ CRITICAL — NEVER VIOLATE)

**NEVER duplicate pattern matching logic between Python code and TOML files**:

- ❌ WRONG: Hardcode regex patterns in `parser.py`, `detectors.py`, or any Python module
- ✅ RIGHT: ALL pattern matching must be defined exclusively in TOML files under `src/logsift/patterns/defaults/`

**Parser Responsibilities** (`core/parser.py`):

- Detect log format (JSON, structured, syslog, plain text)
- Normalize to common structure (extract timestamp if present)
- Preserve FULL original message — never strip level indicators
- Always set `level='INFO'` as default
- NO pattern matching for errors/warnings — that's the TOML's job

**Detector Responsibilities** (`core/detectors.py` — IssueDetector):

- For JSON/structured logs: Use explicit `level` field if available
- For plain text logs: Apply TOML patterns to detect errors/warnings
- Single-pass detection (not two separate passes)
- Build issue dictionaries with all metadata

**Pattern Responsibilities** (via TOML files in `patterns/defaults/`):

- Detect error/warning severity from message content (plain text logs)
- Identify specific error types (404, connection refused, etc.)
- Provide suggestions for known error patterns
- Tag issues with categories for filtering

**Why This Rule Exists**:

1. TOML patterns are the contract with users for customization
2. Users can add custom patterns in `~/.config/logsift/patterns/`
3. Hardcoding patterns in Python makes the tool inflexible and non-extensible
4. Violates DRY — maintaining two sources of truth causes bugs
5. Parser changes break user's custom patterns

**Testing Requirements**:

- Parser tests must verify message preservation, NOT level detection
- Pattern tests must verify TOML regex works as expected
- Integration tests must use both parser + patterns together

**Historical Context**: We previously had hardcoded level detection in `parser.py` (lines 231-239) that duplicated logic in `common.toml`. This caused:

- mkdocs warnings not being detected (parser stripped "WARNING -" before patterns could match)
- Inability to customize detection behavior
- Fragile coupling between parser and specific log formats

This rule prevents that recurring. The parser is a format normalizer, NOT a pattern matcher.

## Architecture

```bash
Input → Parser (format detection, normalization) →
IssueDetector (single-pass, TOML patterns) →
Analyzer (file references + context) →
Dual Output (JSON for LLMs, Markdown for humans)
```

- TTY detection (`utils/tty.py`): `detect_output_format()` returns Markdown on a TTY, else toon
- Commands in `commands/` orchestrate but don't implement logic
- Module layout: `cli.py` (Typer entry), `commands/`, `core/`, `patterns/`, `output/`, `monitor/`, `config/`, `cache/`, `utils/`

### TOML Pattern Format

```toml
[[patterns]]
name = "brew_package_already_installed"
regex = "Error:\\s*(.+)\\s+is already installed"
severity = "error"
description = "Package is already installed"
tags = ["brew", "package_conflict", "fixable"]
suggestion = "Remove package from install list or use 'brew upgrade' instead"
```

Required: name, regex, severity, description, tags. Optional: suggestion.

## JSON Output Schema (DO NOT CHANGE — LLM contract)

```json
{
  "summary": { "status": "failed|success", "exit_code": 0, "duration_seconds": 0.0, "command": "", "timestamp": "ISO8601", "log_file": "" },
  "errors": [{ "id": 0, "severity": "error|warning", "line_in_log": 0, "message": "", "file": "", "file_line": 0, "context_before": [], "context_after": [], "suggestion": { "action": "", "description": "", "confidence": "high|medium|low", "automated_fix": "" }, "pattern_matched": "", "tags": [] }],
  "actionable_items": [{ "priority": 0, "file": "", "line": 0, "action": "", "description": "", "automated": false }],
  "stats": { "total_errors": 0, "total_warnings": 0, "fixable_errors": 0, "log_size_bytes": 0, "log_lines": 0 }
}
```

## Conventions specific to logsift

- **Process monitoring**: `monitor/process.py` uses `subprocess`. `sh` is still declared in `pyproject.toml` and imported nowhere — drop it or use it, but do not believe the dependency list.
- **Config validation is not implemented.** `config/validator.py` is a stub raising
  `NotImplementedError`. When it is written, it validates once at startup and nowhere else —
  the fail-fast rule in `standards/python.md` is what makes one site sufficient.
- **Coverage**: `fail_under` in `pyproject.toml` is the enforced floor; run
  `uv run pytest --cov=logsift` for the current figure rather than trusting a number written here.
  There is no Taskfile in this repo, against `standards/repo-structure.md` § "Taskfile is the
  standard runner".

Python conventions and the pre-commit hook set are fleet standards — see
`standards/python.md` and `standards/ci.md`. The hook inventory is generated from the
declaration `forge toolchain show` names; do not restate it here, it drifts.

## Implementation Status

The core analyzer, pattern loading, streaming, and fzf integration are all implemented. What
remains stubbed raises `NotImplementedError`, so `rg -l NotImplementedError src/` is the current
list rather than a phase table here — as of this writing it is the `patterns` and `monitor`
commands, remote monitoring, cache metadata, the plain formatter, and config validation.

**The `mcp/` package is dead, not pending.** MCP servers are retired ecosystem-wide (see
`~/.claude/CLAUDE.md` § Data CLIs); the CLI with `--json` is the integration surface. Those two
stubs should be deleted rather than finished.

When implementing: tests first (TDD), implement in `core/`/`patterns/`/`output/`, wire up in `commands/`.
