# CLAUDE.md

## Project Overview

**logsift** is an LLM-optimized log analysis tool. Extracts 20-50 actionable lines from 2000+ line logs. Primary user is LLMs (structured JSON), secondary is humans (Markdown). Built for automated fix/retry workflows, not general-purpose log viewing.

**Package Management**: uv (`uv.lock`). Python 3.13.

## Essential Commands

`Taskfile.yml` holds the developer commands, and `task --list` names them.

```bash
task setup                                # Install deps and the git hooks
task test                                 # All tests
task test -- tests/unit/test_parser.py -v # Specific file
task test:coverage                        # With coverage
task lint                                 # ruff, mypy and bandit, read-only
task format                               # ruff format and autofixes
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

**What breaks when the parser detects levels**: a parser that strips a level prefix hides it from
the patterns. A plain-text line such as mkdocs' `WARNING -  Doc file ...` then matches no
warning pattern, and a user's custom pattern cannot change what the parser already decided. The
parser is a format normalizer, NOT a pattern matcher.

## Architecture

```bash
Input → Parser (format detection, normalization) →
IssueDetector (single-pass, TOML patterns) →
Analyzer (file references + context) →
Output (toon for LLMs when piped, JSON for programs, Markdown on a terminal)
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

Required: name, regex, severity, description, tags. Optional: suggestion, context_lines_after.

## JSON Output Contract (agents parse it — change it only with a version)

`schemas/analysis.schema.json` is the shape `--format json` prints, for `analyze`, for `monitor` and
for every saved analysis. Read the fields there, and copy none of them into a doc.
`tests/integration/test_json_contract.py` validates a real run of both commands against it.

Agents parse this output, so a renamed or removed field breaks them without an error. Such a change
edits the schema in the same commit, and raises both `SCHEMA_VERSION` in
`output/json_formatter.py` and the schema's `$id`. An added optional field raises neither.

## Conventions specific to logsift

- **Every external process starts in `process_runner.py`**: `run()` for fzf, bat, notify-send and
  osascript, and `stream()` for the command `monitor` watches, with the interactive-shell fallback
  for an alias or function. Nothing else imports `subprocess`. A missing program raises
  `FileNotFoundError`, and each caller falls back without it, as the README's Optional Programs
  section lists.
- **Runtime dependencies** are the ones `pyproject.toml` declares. Typer builds the CLI, tomllib
  reads config and patterns, python-dateutil parses timestamps and toon-format writes toon. Only
  pyselfupdate reaches the network: `logsift update`, and a daily check for a newer release.
- **`config.toml` is Click's `default_map`.** The root callback in `cli.py` reads and validates
  it once, through `config/loader.py`, and no later code re-checks it. Click then resolves each
  option from its flag, its variable, the file, then its default, and `logsift config` reports
  Click's own parameter source. A new file key goes in `FILE_KEYS`. A new option with an `envvar`
  goes in `RESOLVED_OPTIONS` in `config/resolved_values.py`, or
  `tests/integration/test_config_cli.py` fails.
- **Coverage**: `fail_under` in `pyproject.toml` is the enforced floor; run
  `task test:coverage` for the current figure rather than trusting a number written here.

The pre-commit hook set is `.pre-commit-config.yaml`, and it is generated. Read it there rather
than restating it here, where it drifts.

## Scope

Every module under `src/` is reached from a command. A feature is added when it is built, not as
a stub that waits for one.

**There is no MCP server and no remote monitor, by design.** The CLI is the integration surface
for an agent: `--format json` for a program that parses the result, or the default toon when an
agent reads piped output itself. No command takes `--json`. A remote command is monitored like any other:
`logsift monitor -- ssh user@host ./deploy.sh`.

When implementing: tests first (TDD), implement in `core/`/`patterns/`/`output/`, wire up in `commands/`.
