# logsift - Comprehensive Project Plan

**Status**: Planning Complete - Ready for Implementation
**Created**: 2025-11-27
**Project Location**: `~/code/logsift/` (standalone Python package)
**Primary Purpose**: LLM-optimized log analysis for agentic automated workflows

---

## 🎯 Executive Summary

**logsift** is an intelligent log analysis and command monitoring tool designed specifically for LLM-driven automated workflows. While it provides beautiful human-readable output, its **primary mission** is to enable Claude Code and other AI agents to efficiently diagnose, fix, and retry failed operations with minimal context overhead.

### The Problem We're Solving

When running long commands (installations, builds, tests), current tools dump 2000+ lines of verbose output that:

- Burns LLM context window
- Makes error extraction difficult
- Provides no structured actionable information
- Requires manual reading and interpretation

### The logsift Solution

```bash
Command produces 2000 lines → logsift extracts 20-50 lines
✅ Errors with file:line references
✅ Context around errors (±2 lines)
✅ Actionable fix suggestions
✅ JSON for LLMs + Markdown for humans
✅ Enables automated fix/retry loops
```

---

## 🔄 Session Recovery Information

### This Conversation

This planning session is stored at:

```bash
~/.claude/sessions/session-2025-11-27-XXXXXX.json
```

### To Resume This Context

1. **From dotfiles directory**: Current session will be in compact/summary mode
2. **From new logsift directory**: Start fresh with this planning document as reference
3. **To find session files**:

   ```bash
   ls -lt ~/.claude/sessions/ | head -5
   ```

### Critical Context to Carry Forward

- Agentic-first design (LLM consumption is PRIMARY, human is secondary)
- Dual output modes (JSON + Markdown simultaneously)
- Pattern library system (extensible, community-driven)
- Python 3.11+, Typer, TOML, sh library
- Will become MCP server in Phase 3

---

## 📋 Project Vision & Mission

### Vision Statement

**"Make log analysis intelligent, efficient, and LLM-friendly to enable fully automated software development workflows."**

### Core Mission

1. **Primary**: Enable LLM agents (Claude Code) to diagnose and fix errors autonomously
2. **Secondary**: Provide beautiful human-readable summaries for learning and debugging
3. **Tertiary**: Build extensible pattern library for community-driven error knowledge

### Key Stakeholders

1. **LLM Agents** (Primary User)
   - Need structured JSON with file:line references
   - Want minimal context usage (20-50 lines not 2000)
   - Require actionable information for automated fixes

2. **Human Developers** (Secondary User)
   - Want readable summaries with colors and formatting
   - Need to learn from error patterns
   - Want to browse and search historical logs

3. **Community** (Tertiary User)
   - Can contribute error pattern libraries
   - Share domain-specific knowledge (brew, apt, docker, etc.)
   - Build on MCP server integration

---

## 🏗️ Architecture Overview

### Fundamental Design Principles

1. **Core is Analysis** - Log analysis is the primary function
2. **Monitoring is Optional** - Convenience wrapper, not required
3. **LLM-First Output** - JSON schema optimized for agent consumption
4. **Human-Friendly Too** - Markdown output for developer learning
5. **Extensible Patterns** - Community-driven error knowledge
6. **Universal Compatibility** - Works with ANY log format
7. **No Dotfiles Coupling** - Completely standalone tool

### Core Components

```bash
logsift
├── Core Engine (Primary Value)
│   ├── Log Parser        # Read any format (structured, unstructured, JSON)
│   ├── Pattern Matcher   # Apply error detection rules
│   ├── Context Extractor # Get ±N lines around errors
│   ├── File Ref Finder   # Extract file:line references
│   └── JSON Formatter    # LLM-optimized structured output
│
├── Optional Features (Convenience)
│   ├── Process Monitor   # Run commands, capture output
│   ├── Live Watcher      # Tail and analyze real-time
│   └── Remote SSH        # Phase 3: remote monitoring
│
├── Pattern System (Community Knowledge)
│   ├── Pattern Loader    # Load .toml pattern files
│   ├── Pattern Matcher   # Apply rules to log content
│   └── Default Patterns  # common.toml, brew.toml, apt.toml, etc.
│
└── Output Formatters (Dual Modes)
    ├── LLM JSON          # Structured schema for agents
    ├── Human Markdown    # Beautiful colored output
    └── Plain Text        # Fallback for piping
```

### Data Flow

```bash
┌─────────────────────────────────────────────────────┐
│ Input Sources                                       │
│  - Command execution (monitored)                    │
│  - Existing log files                               │
│  - Live tailing (watch mode)                        │
│  - Remote SSH (Phase 3)                             │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ Parser                                              │
│  - Auto-detect format (JSON, structured, plain)     │
│  - Extract timestamps, levels, messages             │
│  - Normalize to internal representation             │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ Pattern Matching                                    │
│  - Load pattern libraries (.toml files)             │
│  - Apply regex rules                                │
│  - Match error types                                │
│  - Extract file:line references                     │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ Context Extraction                                  │
│  - Get ±2 lines around each error                   │
│  - Group related errors                             │
│  - Deduplicate similar messages                     │
│  - Priority ordering                                │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│ Output Generation (Dual Mode)                       │
│  ┌──────────────────┬──────────────────────┐        │
│  │ JSON (for LLMs)  │ Markdown (for Human) │        │
│  │ - Structured     │ - Colored            │        │
│  │ - Predictable    │ - Formatted          │        │
│  │ - Actionable     │ - Readable           │        │
│  └──────────────────┴──────────────────────┘        │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 Output Modes & Combinations

### Design Philosophy

> **"JSON for agents, Markdown for humans, both simultaneously when needed"**

### Output Mode Matrix

| Mode | JSON Output | Markdown Output | Use Case |
|------|-------------|-----------------|----------|
| `--format=json` | stdout | none | Agentic automation (default headless) |
| `--format=markdown` | none | stdout | Human terminal use (default interactive) |
| `--stream` | file (.json) | stdout | LLM + human simultaneously |
| `--json-to=file` | file | stdout | Save structured + show readable |
| `--both` | stdout (separator) | stdout | Debug mode |

### JSON Schema for LLMs

**Optimized for Claude Code automated workflows**

```json
{
  "summary": {
    "status": "failed",
    "exit_code": 1,
    "duration_seconds": 222,
    "command": "task install",
    "timestamp": "2025-11-27T14:30:22Z",
    "log_file": "~/.cache/logsift/dotfiles/macos-install-20251127-143022.log"
  },
  "errors": [
    {
      "id": 1,
      "severity": "error",
      "line_in_log": 234,
      "message": "Error: tmux 3.5a is already installed",
      "file": "management/taskfiles/macos.yml",
      "file_line": 45,
      "context_before": [
        "Installing system packages...",
        "==> Installing tmux"
      ],
      "context_after": [
        "To upgrade: brew upgrade tmux",
        "task: Failed to run task \"install-packages\": exit status 1"
      ],
      "suggestion": {
        "action": "remove_line",
        "description": "Remove tmux from brew install list (already installed)",
        "confidence": "high",
        "automated_fix": "sed -i '/tmux/d' management/taskfiles/macos.yml:45"
      },
      "pattern_matched": "brew_package_already_installed",
      "tags": ["brew", "package_conflict", "fixable"]
    }
  ],
  "warnings": [
    {
      "id": 1,
      "severity": "warning",
      "line_in_log": 123,
      "message": "warning: using deprecated `--force` flag",
      "context": ["Installing cargo tools...", "use `--locked` instead"],
      "suggestion": {
        "action": "update_flag",
        "description": "Update cargo-binstall flags to use --locked",
        "confidence": "medium"
      }
    }
  ],
  "actionable_items": [
    {
      "priority": 1,
      "file": "management/taskfiles/macos.yml",
      "line": 45,
      "action": "remove",
      "description": "Remove tmux from install list (already installed)",
      "automated": true
    }
  ],
  "stats": {
    "total_errors": 3,
    "total_warnings": 1,
    "fixable_errors": 2,
    "log_size_bytes": 458392,
    "log_lines": 2847
  }
}
```

**Why This Schema:**

- ✅ **Predictable structure** - Claude knows exactly where to find information
- ✅ **File references** - Exact paths with line numbers for editing
- ✅ **Context included** - No need to read full log
- ✅ **Actionable items** - Direct instructions for fixes
- ✅ **Priority ordering** - Most critical errors first
- ✅ **Automated fix hints** - Suggested commands when confident
- ✅ **Tagging system** - Easy filtering and categorization

### Markdown Format for Humans

**Beautiful, colored, readable terminal output**

```markdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 SUMMARY: macos-install
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Status: ❌ FAILED (exit code 1)
Duration: 3m 42s (222 seconds)
Log: ~/.cache/logsift/dotfiles/macos-install-20251127-143022.log
Started: 2025-11-27 14:30:22

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ERRORS (3 total, 2 fixable)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Error 1] Line 234: Package already installed
    📁 File: management/taskfiles/macos.yml:45

    232 | Installing system packages...
    233 | ==> Installing tmux
 ❌ 234 | Error: tmux 3.5a is already installed
    235 | To upgrade: brew upgrade tmux
    236 | task: Failed to run task "install-packages": exit status 1

    💡 Suggestion: Remove tmux from brew install list (already installed)
    🔧 Auto-fix: sed -i '/tmux/d' management/taskfiles/macos.yml:45

    Pattern: brew_package_already_installed
    Tags: brew, package_conflict, fixable

[Error 2] Line 456: Permission denied
    📁 File: /Users/chris/.zshrc

    454 | Creating symlinks...
    455 | ln -sf ~/.config/zsh/.zshrc ~/.zshrc
 ❌ 456 | ln: /Users/chris/.zshrc: Permission denied
    457 |

    💡 Suggestion: Check file permissions
    🔍 Debug: ls -la /Users/chris/.zshrc

    Pattern: permission_denied
    Tags: filesystem, permissions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 WARNINGS (1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Warning 1] Line 123: Deprecated flag
    121 | Installing cargo tools...
    122 | warning: using deprecated `--force` flag
 ⚠️  123 | use `--locked` instead
    124 | cargo-binstall completed

    💡 Suggestion: Update cargo-binstall flags to use --locked

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ACTIONABLE FIXES (Priority Ordered)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [AUTO] Remove tmux from install list
   File: management/taskfiles/macos.yml:45
   Command: sed -i '/tmux/d' management/taskfiles/macos.yml:45

2. [MANUAL] Check permissions on ~/.zshrc
   File: /Users/chris/.zshrc
   Debug: ls -la /Users/chris/.zshrc

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total Errors: 3 (2 fixable automatically)
Total Warnings: 1
Log Size: 447 KB (2,847 lines)
Analysis Time: 0.34s

For full log: logsift view ~/.cache/logsift/dotfiles/macos-install-latest.log
```

### Output Mode Examples

#### Example 1: Agentic Automation (Default Headless)

```bash
# In Claude Code automation
logsift monitor -- task install
# Automatically outputs JSON to stdout (detected headless)
```

#### Example 2: Human Terminal (Default Interactive)

```bash
# Human running in terminal
logsift monitor -- task install
# Automatically outputs beautiful Markdown (detected interactive TTY)
```

#### Example 3: Both Simultaneously

```bash
# Stream readable output, save JSON for later
logsift monitor --stream -- task install
# stdout: Markdown for human watching
# ~/.cache/logsift/context/name-timestamp.json: structured data
```

#### Example 4: Custom Combination

```bash
# JSON to file, Markdown to terminal
logsift monitor --json-to=result.json --format=markdown -- task install
```

---

## 🔧 Technical Stack

### Language & Version

**Python 3.11+** (Required for stdlib TOML support)

**Why Python:**

- ✅ Excellent text processing (regex, string manipulation)
- ✅ Native JSON/TOML support (3.11+)
- ✅ Rich ecosystem (typer, sh, rich)
- ✅ Easy testing (pytest)
- ✅ Type hints for quality
- ✅ Already in dotfiles stack (uv)
- ✅ NOT Bash (avoids "1000-line behemoth" trap)

### Core Dependencies

```toml
[project.dependencies]
typer = {extras = ["all"], version = ">=0.15.0"}  # CLI framework (includes rich)
tomli-w = ">=1.0.0"                                # TOML writing (read is stdlib)
sh = ">=2.0.0"                                     # Clean subprocess interface
python-dateutil = ">=2.8.0"                        # Robust timestamp parsing
```

**Dependency Justification:**

1. **typer** - Type-hint based CLI, built on click, includes rich for beautiful output
2. **tomli-w** - TOML writing (reading is stdlib in 3.11+)
3. **sh** - Makes subprocess calls Pythonic (no more subprocess confusion!)
4. **python-dateutil** - Parse timestamps from any format reliably

### Development Dependencies

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "pytest-mock>=3.12",
    "ruff>=0.8",           # Linting + formatting
    "mypy>=1.0",           # Type checking
]
```

### Build System

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**Hatchling** - Modern, fast, standards-compliant

---

## 📁 Project Structure

```bash
~/code/logsift/
├── pyproject.toml                    # Project metadata, dependencies
├── README.md                         # Quick start, badges, features
├── LICENSE                          # MIT or Apache 2.0
├── CLAUDE.md                        # Development context (copied from dotfiles)
│
├── docs/                            # Comprehensive documentation
│   ├── index.md                     # Documentation home
│   ├── quickstart.md                # 5-minute getting started
│   ├── installation.md              # Install guide
│   ├── cli-reference.md             # Complete CLI documentation
│   │
│   ├── concepts/                    # Core concepts
│   │   ├── agentic-integration.md   # ⭐ Using with Claude Code
│   │   ├── output-modes.md          # JSON vs Markdown modes
│   │   └── pattern-matching.md      # How pattern system works
│   │
│   ├── guides/                      # How-to guides
│   │   ├── structured-logging.md    # ⭐ Writing log-friendly scripts
│   │   ├── custom-patterns.md       # Creating pattern libraries
│   │   ├── monitoring.md            # Process monitoring guide
│   │   └── remote-ssh.md            # Remote monitoring (Phase 3)
│   │
│   ├── architecture/                # Design docs
│   │   ├── design-principles.md     # Why we made these choices
│   │   ├── data-flow.md            # How data moves through system
│   │   └── mcp-integration.md       # MCP server design (Phase 3)
│   │
│   ├── api/                         # API reference
│   │   ├── json-schema.md           # Complete JSON output schema
│   │   ├── pattern-format.md        # TOML pattern file format
│   │   └── config-format.md         # Configuration file format
│   │
│   └── development/                 # Contributing
│       ├── setup.md                 # Dev environment setup
│       ├── testing.md               # Testing guide
│       └── patterns.md              # Code patterns and conventions
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   │
│   ├── unit/                        # Unit tests
│   │   ├── test_analyzer.py         # Core analysis tests
│   │   ├── test_parser.py           # Log parsing tests
│   │   ├── test_patterns.py         # Pattern matching tests
│   │   ├── test_formatters.py       # Output formatting tests
│   │   ├── test_config.py           # Config loading tests
│   │   └── test_process.py          # Process monitoring tests
│   │
│   ├── integration/                 # Integration tests
│   │   ├── test_monitor_flow.py     # Full monitoring workflow
│   │   ├── test_analyze_flow.py     # Analysis pipeline
│   │   ├── test_error_detection.py  # Error pattern detection
│   │   └── test_output_modes.py     # Dual output modes
│   │
│   └── fixtures/                    # Test data
│       ├── sample_logs/             # Real-world log samples
│       │   ├── brew_install.log
│       │   ├── apt_install.log
│       │   ├── npm_install.log
│       │   └── make_build.log
│       ├── configs/                 # Sample configs
│       │   └── test_config.toml
│       └── patterns/                # Sample pattern files
│           ├── test_patterns.toml
│           └── custom_patterns.toml
│
└── src/                             # Source code
    └── logsift/
        ├── __init__.py              # Package init, version
        ├── __main__.py              # Entry point (python -m logsift)
        ├── cli.py                   # ⭐ Typer CLI - main commands
        │
        ├── commands/                # CLI command implementations
        │   ├── __init__.py
        │   ├── monitor.py           # monitor subcommand
        │   ├── analyze.py           # analyze subcommand
        │   ├── watch.py             # watch subcommand
        │   ├── patterns.py          # patterns subcommand
        │   └── logs.py              # logs subcommand (list, clean)
        │
        ├── core/                    # ⭐ Core analysis engine
        │   ├── __init__.py
        │   ├── analyzer.py          # Main analysis orchestrator
        │   ├── parser.py            # Log parsing (detect format, normalize)
        │   ├── extractors.py        # Extract errors, warnings, file refs
        │   ├── matchers.py          # Pattern matching engine
        │   └── context.py           # Context extraction (±N lines)
        │
        ├── patterns/                # Pattern library system
        │   ├── __init__.py
        │   ├── loader.py            # Load .toml pattern files
        │   ├── matcher.py           # Apply patterns to logs
        │   ├── validator.py         # Validate pattern files
        │   └── defaults/            # Built-in pattern libraries
        │       ├── common.toml      # Universal patterns
        │       ├── brew.toml        # Homebrew errors
        │       ├── apt.toml         # APT errors
        │       ├── npm.toml         # NPM errors
        │       ├── docker.toml      # Docker errors
        │       └── cargo.toml       # Cargo/Rust errors
        │
        ├── output/                  # ⭐ Output formatters (dual mode)
        │   ├── __init__.py
        │   ├── json_formatter.py    # LLM-optimized JSON
        │   ├── markdown_formatter.py # Human-readable Markdown
        │   ├── plain_formatter.py   # Plain text fallback
        │   └── streaming.py         # Dual-stream manager
        │
        ├── monitor/                 # Process monitoring
        │   ├── __init__.py
        │   ├── process.py           # Clean subprocess wrappers (sh library)
        │   ├── watcher.py           # Live log tailing
        │   └── remote.py            # Remote SSH monitoring (Phase 3)
        │
        ├── config/                  # Configuration management
        │   ├── __init__.py
        │   ├── loader.py            # Load TOML config
        │   ├── defaults.py          # Default configuration
        │   └── validator.py         # Config validation
        │
        ├── cache/                   # Log caching system
        │   ├── __init__.py
        │   ├── manager.py           # Cache directory management
        │   ├── rotation.py          # Log rotation/cleanup
        │   └── metadata.py          # Track log metadata
        │
        ├── utils/                   # Utilities
        │   ├── __init__.py
        │   ├── tty.py               # TTY detection (interactive vs headless)
        │   ├── colors.py            # Color output helpers
        │   └── timestamps.py        # Timestamp parsing/formatting
        │
        └── mcp/                     # MCP server (Phase 3)
            ├── __init__.py
            ├── server.py            # MCP server implementation
            └── tools.py             # Tool definitions
```

---

## 🎯 Implementation Phases

### Phase 1: Core Analyzer + Basic Monitor (MVP)

**Goal**: Build functional log analysis with monitoring wrapper

**Duration**: 2-3 weeks

**Tasks**:

1. **Project Setup** (1-2 days)
   - [x] Create `~/code/logsift/` directory
   - [ ] Initialize git repository
   - [ ] Create `pyproject.toml` with dependencies
   - [ ] Set up `src/logsift/` package structure
   - [ ] Create basic `README.md`
   - [ ] Copy `CLAUDE.md` from dotfiles
   - [ ] Set up pytest configuration
   - [ ] Configure ruff for linting/formatting

2. **Core Analysis Engine** (1 week)
   - [ ] **Parser** (`core/parser.py`)
     - Auto-detect log format (JSON, structured, plain text)
     - Extract timestamps, levels, messages
     - Normalize to internal representation
     - Handle ANSI color codes
   - [ ] **Extractor** (`core/extractors.py`)
     - Extract errors (multiple heuristics)
     - Extract warnings
     - Extract file:line references (standard patterns)
     - Extract context (±N lines)
   - [ ] **Pattern System** (`patterns/`)
     - Load default pattern files (common.toml, brew.toml, apt.toml)
     - Match patterns against log content
     - Score confidence levels
   - [ ] **Tests**: Unit tests for each component (80%+ coverage)

3. **Output Formatters** (3-4 days)
   - [ ] **JSON Formatter** (`output/json_formatter.py`)
     - Generate LLM-optimized schema
     - Include all required fields
     - Validate output structure
   - [ ] **Markdown Formatter** (`output/markdown_formatter.py`)
     - Use rich for colored output
     - Beautiful formatting with boxes, separators
     - File references as links
   - [ ] **TTY Detection** (`utils/tty.py`)
     - Detect interactive vs headless
     - Auto-select format appropriately
   - [ ] **Tests**: Output format validation

4. **CLI Foundation** (2-3 days)
   - [ ] **Setup Typer** (`cli.py`)
     - Main app with subcommands
     - Help text and documentation
   - [ ] **analyze command** (`commands/analyze.py`)
     - Takes log file path
     - Runs analysis
     - Outputs in chosen format
     - `logsift analyze logfile.log`
     - `logsift analyze --format=json logfile.log`
   - [ ] **Tests**: CLI integration tests

5. **Process Monitor** (3-4 days)
   - [ ] **Process Wrapper** (`monitor/process.py`)
     - Use `sh` library for clean subprocess
     - Capture stdout/stderr
     - Track exit code
     - Immediate termination detection
   - [ ] **monitor command** (`commands/monitor.py`)
     - Run command in background
     - Create log file
     - Show periodic updates
     - Call analyzer on completion
     - `logsift monitor -- task install`
     - `logsift monitor -n build -i 15 -- make`
   - [ ] **Tests**: Monitor workflow tests

6. **Config System** (2 days)
   - [ ] **Config Loader** (`config/loader.py`)
     - Load from `~/.config/logsift/config.toml`
     - Merge with defaults
     - CLI flags override config
   - [ ] **Default Config** (`config/defaults.py`)
     - Sensible defaults
   - [ ] **Tests**: Config loading and merging

7. **Cache Management** (2 days)
   - [ ] **Cache Manager** (`cache/manager.py`)
     - Create `~/.cache/logsift/context/name-timestamp.log` structure
     - Symlink to `name-latest.log`
     - Metadata tracking
   - [ ] **Tests**: Cache operations

**Success Criteria Phase 1**:

- ✅ Can analyze existing log files
- ✅ Can monitor commands and capture output
- ✅ JSON output matches schema
- ✅ Markdown output is beautiful
- ✅ Auto-detects format based on TTY
- ✅ Config file works
- ✅ 80%+ test coverage
- ✅ Can install with `uv tool install`

### Phase 2: Enhanced Features

**Goal**: Pattern libraries, dual output, fzf integration, streaming

**Duration**: 2-3 weeks

**Tasks**:

1. **Pattern Library System** (1 week)
   - [ ] **Custom Pattern Loading**
     - Load from `~/.config/logsift/patterns/*.toml`
     - Merge with built-in patterns
     - Priority ordering
   - [ ] **Pattern Validator** (`patterns/validator.py`)
     - Validate .toml format
     - Check regex syntax
     - `logsift patterns validate custom.toml`
   - [ ] **Pattern Management Commands**
     - `logsift patterns list` - List available patterns
     - `logsift patterns show brew` - Show specific pattern file
     - `logsift patterns validate` - Validate custom patterns
   - [ ] **More Built-in Patterns**
     - `docker.toml` - Docker errors
     - `npm.toml` - NPM errors
     - `cargo.toml` - Rust/Cargo errors
     - `make.toml` - Make build errors
     - `pytest.toml` - Python test errors
   - [ ] **Community Pattern Template**
     - Example custom pattern file
     - Documentation for creating patterns
   - [ ] **Tests**: Pattern loading, validation, merging

2. **Dual Output Modes** (3-4 days)
   - [ ] **Streaming Manager** (`output/streaming.py`)
     - Manage dual streams (JSON to file, Markdown to stdout)
     - Handle combinations
   - [ ] **Stream Flags**
     - `--stream` - Markdown to stdout, JSON to cache
     - `--json-to=file` - JSON to specific file
     - `--both` - Both formats to stdout (separated)
   - [ ] **Tests**: All output combinations

3. **fzf Integration** (2 days)
   - [ ] **logs list Command** (`commands/logs.py`)
     - Find logs in cache
     - Pass to fzf with preview
     - `logsift logs list`
     - `logsift logs list --context=dotfiles`
   - [ ] **Preview Integration**
     - Use `bat` for syntax highlighting
     - Show log metadata
   - [ ] **Tests**: Log listing and filtering

4. **Live Watching** (2-3 days)
   - [ ] **Watcher** (`monitor/watcher.py`)
     - Tail log file
     - Analyze incrementally
     - Show updates
   - [ ] **watch Command** (`commands/watch.py`)
     - `logsift watch /var/log/app.log`
     - Real-time analysis
   - [ ] **Tests**: Live watching behavior

5. **External Log Support** (2 days)
   - [ ] **External Log Monitor**
     - `--external-log` flag
     - Tail external file while monitoring command
     - Merge both sources
   - [ ] **Tests**: External log integration

6. **Append Mode** (1 day)
   - [ ] **Resume Functionality**
     - `--append` flag
     - Append to existing log instead of creating new
     - `logsift monitor -n build --append -- make`
   - [ ] **Tests**: Append behavior

7. **Notifications** (2 days)
   - [ ] **Platform Notifications**
     - macOS: osascript
     - Linux: notify-send
     - `--notify` flag
   - [ ] **Config Options**
     - `notifications.on_success`
     - `notifications.on_failure`
   - [ ] **Tests**: Notification delivery

8. **Log Cleanup** (1 day)
   - [ ] **clean Command** (`commands/logs.py`)
     - `logsift logs clean` - Remove >90 days (default)
     - `logsift logs clean --days=30` - Custom retention
   - [ ] **Tests**: Cleanup behavior

**Success Criteria Phase 2**:

- ✅ Can load custom pattern libraries
- ✅ fzf integration works beautifully
- ✅ Dual output modes work correctly
- ✅ Live watching provides real-time analysis
- ✅ External log support functional
- ✅ Notifications work cross-platform
- ✅ Log cleanup maintains cache
- ✅ 80%+ test coverage maintained

### Phase 3: MCP Server & Remote Monitoring

**Goal**: Claude Code native integration, remote SSH monitoring

**Duration**: 2-3 weeks

**Tasks**:

1. **MCP Server Implementation** (1.5 weeks)
   - [ ] **Research MCP Protocol**
     - Study Claude Agent SDK
     - Review MCP specification
     - Analyze existing MCP servers
   - [ ] **MCP Server** (`mcp/server.py`)
     - Implement MCP protocol
     - Tool definitions
     - Request handling
   - [ ] **Tool Definitions** (`mcp/tools.py`)
     - `logsift_monitor` tool
     - `logsift_analyze` tool
     - `logsift_watch` tool
   - [ ] **Integration Testing**
     - Test with Claude Code
     - Verify tool calling
   - [ ] **Documentation**
     - MCP server setup guide
     - Tool usage examples
     - Claude Code integration

2. **Remote SSH Monitoring** (1 week)
   - [ ] **Remote Monitor** (`monitor/remote.py`)
     - SSH connection management
     - Remote script execution
     - Log streaming back
   - [ ] **--ssh Flag**
     - `logsift monitor --ssh user@host -- ./deploy.sh`
     - Handle authentication
     - Stream output
   - [ ] **Tests**: Remote execution (mocked)

3. **Advanced Features** (Remaining time)
   - [ ] **Log Compression**
     - Compress old logs (>30 days)
     - Automatic cleanup
   - [ ] **Export Summaries**
     - `logsift export --format=html summary.html`
     - Generate shareable reports
   - [ ] **Performance Optimization**
     - Large log file handling
     - Incremental parsing
     - Memory efficiency

**Success Criteria Phase 3**:

- ✅ MCP server works with Claude Code
- ✅ Can be called as native tool
- ✅ Remote monitoring functional
- ✅ Export features work
- ✅ Performance acceptable for large logs
- ✅ Complete documentation

---

## 🧪 Testing Strategy

### Philosophy

> **"Test behavior, not implementation. Aim for 80%+ coverage. Integration tests are as important as unit tests."**

### Test Categories

1. **Unit Tests** (`tests/unit/`)
   - Test individual components in isolation
   - Mock external dependencies
   - Fast execution (<1 second total)
   - 80%+ coverage target

2. **Integration Tests** (`tests/integration/`)
   - Test complete workflows
   - Use real log fixtures
   - Test component interactions
   - Moderate execution (<10 seconds total)

3. **Fixture-Based Tests** (`tests/fixtures/`)
   - Real-world log samples
   - Known error patterns
   - Regression prevention

### Test Structure

```python
# Example: tests/unit/test_analyzer.py
import pytest
from logsift.core.analyzer import Analyzer
from logsift.core.parser import LogParser

def test_analyzer_detects_errors():
    """Test that analyzer correctly identifies errors in logs"""
    log_content = """
    2025-11-27T14:30:22Z [INFO] Starting installation
    2025-11-27T14:30:23Z [ERROR] Package tmux already installed
    2025-11-27T14:30:24Z [INFO] Continuing...
    """

    parser = LogParser()
    analyzer = Analyzer()

    parsed = parser.parse(log_content)
    results = analyzer.analyze(parsed)

    assert len(results.errors) == 1
    assert "already installed" in results.errors[0].message
    assert results.errors[0].severity == "error"

def test_analyzer_extracts_file_references():
    """Test file:line reference extraction"""
    log_content = """
    Error in file src/main.py:123: undefined variable
    """

    parser = LogParser()
    analyzer = Analyzer()

    parsed = parser.parse(log_content)
    results = analyzer.analyze(parsed)

    assert len(results.errors) == 1
    assert results.errors[0].file == "src/main.py"
    assert results.errors[0].file_line == 123
```

### Coverage Requirements

| Component | Target Coverage | Why |
|-----------|----------------|-----|
| Core (analyzer, parser, extractors) | 90%+ | Mission-critical |
| Output formatters | 80%+ | User-facing |
| Pattern matching | 85%+ | Core functionality |
| CLI commands | 70%+ | Integration-heavy |
| Config/cache | 75%+ | Support systems |
| Overall | 80%+ | Quality baseline |

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=logsift --cov-report=html

# Specific category
pytest tests/unit/
pytest tests/integration/

# Specific file
pytest tests/unit/test_analyzer.py

# Specific test
pytest tests/unit/test_analyzer.py::test_analyzer_detects_errors

# Watch mode (during development)
pytest-watch
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ['3.11', '3.12', '3.13']

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e '.[dev]'
      - run: pytest --cov=logsift --cov-report=xml
      - uses: codecov/codecov-action@v4
```

---

## 🎓 Structured Logging Guide (For Documentation)

### Industry Standards & Research

**Sources**:

- [Structured Logging Best Practices](https://betterstack.com/community/guides/logging/structured-logging/)
- [JSON Logging Guide](https://betterstack.com/community/guides/logging/json-logging/)
- [Python structlog](https://www.structlog.org/en/stable/logging-best-practices.html)
- [Syslog RFC 5424](https://datatracker.ietf.org/doc/html/rfc5424)
- [GitLab CI/CD Logging](https://the-pi-guy.com/blog/gitlab_cicd_and_logging_best_practices_for_logging_in_your_cicd_pipeline_and_deployed_applications/)

### Recommended Format

**JSON (Structured) - For Parseable Logs**

```json
{
  "timestamp": "2025-11-27T14:30:22.123456Z",
  "level": "ERROR",
  "message": "Package installation failed",
  "context": {
    "package": "tmux",
    "reason": "already_installed",
    "phase": "install",
    "attempt": 1
  },
  "caller": {
    "file": "install.sh",
    "line": 234,
    "function": "install_package"
  }
}
```

**Human-Readable (Hybrid) - For Scripts**

```yaml
2025-11-27T14:30:22Z [ERROR] Package installation failed {package: tmux, reason: already_installed, phase: 1/9}
```

### Key Elements

1. **Timestamp**: ISO 8601 format (`YYYY-MM-DDTHH:MM:SS.SSSSSSZ`)
2. **Level**: DEBUG, INFO, WARN, ERROR, FATAL
3. **Message**: Human-readable description
4. **Context**: Structured metadata (key:value pairs)
5. **Caller**: File, line, function (when available)

### Auto-Detection Strategy

logsift will auto-detect and parse:

1. **JSON** - Try `json.loads()`, if success, use structured parser
2. **Structured key=value** - Parse `key=value` or `key: value` patterns
3. **Syslog** - Detect RFC 5424 or BSD syslog format
4. **Plain text** - Fall back to heuristic-based parsing

### Writing Scripts for logsift

**Best Practices**:

1. **Use Standard Exit Codes**

   ```bash
   # Success
   exit 0

   # General failure
   exit 1

   # Specific failures (optional)
   exit 2  # Misuse (bad arguments)
   exit 126  # Command cannot execute
   exit 127  # Command not found
   ```

2. **Include Timestamps**

   ```bash
   echo "$(date -Iseconds) [INFO] Starting installation"
   ```

3. **Use Consistent Markers**

   ```bash
   echo "✅ Step completed successfully"
   echo "❌ Step failed: reason"
   echo "⚠️  Warning: potential issue"
   echo "ℹ️  Info: useful context"
   ```

4. **Include Context in Errors**

   ```bash
   # Bad
   echo "Error"

   # Good
   echo "❌ Error: Failed to install package 'tmux' (already installed at version 3.5a)"
   echo "   File: management/taskfiles/macos.yml:45"
   ```

5. **Show Progress**

   ```bash
   echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
   echo " Phase 1/3: Installing packages"
   echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
   ```

6. **File References**

   ```bash
   # Standard format: file:line
   echo "Error in src/main.py:123: undefined variable"
   ```

7. **Idempotency**

   ```bash
   # Check before doing
   if [[ -d "$TARGET" ]]; then
     echo "✅ Directory already exists: $TARGET"
   else
     mkdir -p "$TARGET"
     echo "✅ Created directory: $TARGET"
   fi
   ```

---

## 🤖 Agentic Integration Guide

### The Agentic Loop

**From [Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)**:

```text
gather context → take action → verify work → repeat
```

**Where logsift fits**:

```yaml
Claude Code (agent)
  ↓
Runs: logsift monitor -- task install
  ↓
Gets JSON output (20-50 lines, not 2000)
  ↓
Sees: errors, file:line refs, suggested fixes
  ↓
Edits: management/taskfiles/macos.yml:45
  ↓
Reruns: logsift monitor -- task install
  ↓
Repeats until success ✅
```

### Integration Patterns

#### Pattern 1: Direct CLI Usage

```python
# In Claude Code automation
import subprocess
import json

result = subprocess.run(
    ["logsift", "monitor", "--format=json", "--", "task", "install"],
    capture_output=True,
    text=True
)

data = json.loads(result.stdout)

for error in data["errors"]:
    # Claude edits: error["file"] at line error["file_line"]
    print(f"Fix needed: {error['file']}:{error['file_line']}")
    print(f"Suggestion: {error['suggestion']['description']}")
```

#### Pattern 2: MCP Tool Integration (Phase 3)

```typescript
// Claude Code calls logsift as MCP tool
const result = await call_tool("logsift_monitor", {
  command: "task install",
  name: "macos-install",
  format: "json"
});

// Result is structured JSON, ready to analyze
for (const error of result.errors) {
  // Apply fixes
}
```

#### Pattern 3: Slash Command Integration

```markdown
# In Claude Code
User: /install

# Claude runs:
logsift monitor --format=json -- task install

# Analyzes output, fixes errors, retries automatically
```

### Output Optimization for LLMs

**Key Principles** ([source](https://www.deeplearning.ai/the-batch/agentic-design-patterns-part-3-tool-use/)):

1. **Predictable Structure** - Same schema every time
2. **Minimal Context** - Only actionable information
3. **File References** - Exact paths for editing
4. **Prioritization** - Most important errors first
5. **Actionable Items** - Direct fix instructions

### Example Automated Workflow

```python
# autonomous_install.py
import subprocess
import json
import time

MAX_RETRIES = 5

def install_with_retry():
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"Attempt {attempt}/{MAX_RETRIES}")

        # Run installation with logsift
        result = subprocess.run(
            ["logsift", "monitor", "--format=json", "--", "task", "install"],
            capture_output=True,
            text=True
        )

        data = json.loads(result.stdout)

        # Check success
        if data["summary"]["status"] == "success":
            print("✅ Installation successful!")
            return True

        # Extract fixes needed
        print(f"❌ Installation failed ({len(data['errors'])} errors)")

        for item in data["actionable_items"]:
            if item.get("automated"):
                # Apply automated fix
                print(f"🔧 Auto-fixing: {item['description']}")
                # Execute automated_fix command
                subprocess.run(item["automated_fix"], shell=True)
            else:
                # Manual intervention needed
                print(f"⚠️  Manual fix required: {item['description']}")
                print(f"   File: {item['file']}:{item['line']}")

        # Wait before retry
        time.sleep(2)

    print("❌ Installation failed after max retries")
    return False

if __name__ == "__main__":
    install_with_retry()
```

---

## ⚙️ Configuration System

### Config File Location

```text
~/.config/logsift/config.toml
```

### Default Configuration

```toml
# logsift configuration

[general]
cache_dir = "~/.cache/logsift"
default_interval = 60  # seconds between progress checks

[output]
default_format = "auto"  # auto, json, markdown, plain
use_colors = true
use_emoji = true
context_lines = 2  # lines before/after errors

[summary]
max_errors = 10
max_warnings = 5
show_line_numbers = true
show_context = true
show_suggestions = true
deduplicate_errors = true

[patterns]
load_builtin = true
load_custom = true
custom_dir = "~/.config/logsift/patterns"

[notifications]
enabled = true
on_success = false
on_failure = true

[cleanup]
retention_days = 90
auto_cleanup = false

[monitor]
check_interval = 60
show_progress = true
save_logs = true

[watch]
update_interval = 1  # seconds
clear_screen = false
```

### CLI Flags Override Config

Priority order: `CLI flags > Config file > Defaults`

```bash
# Config says: default_format = "json"
# But CLI flag wins:
logsift analyze --format=markdown log.txt
# Uses markdown format
```

---

## 📦 Installation & Setup

### Installing logsift

#### From Development (During Development)

```bash
# Clone/create project
cd ~/code
mkdir logsift
cd logsift

# Initialize git
git init

# Create virtual environment (optional but recommended)
python3.11 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# Or with uv
uv pip install -e .
```

#### System-Wide Installation (After Phase 1)

```bash
# Install as uv tool (recommended)
uv tool install ~/code/logsift

# Or with pipx
pipx install ~/code/logsift

# Or system-wide with pip (not recommended)
pip install ~/code/logsift
```

### Initial Setup

```bash
# Run initial setup (creates config, cache dirs)
logsift --version
# logsift version 0.1.0

# Check configuration
logsift config show

# Test with sample log
logsift analyze tests/fixtures/sample_logs/brew_install.log
```

### Updating

```bash
# Development
cd ~/code/logsift
git pull
pip install -e .

# uv tool
uv tool upgrade logsift
```

---

## 📚 Documentation Strategy

### Documentation Structure

```text
docs/
├── index.md                         # Landing page
├── quickstart.md                    # 5-minute getting started
├── installation.md                  # Install guide
├── cli-reference.md                 # Complete CLI docs
│
├── concepts/                        # Core concepts
│   ├── agentic-integration.md       # ⭐ Using with Claude Code
│   ├── output-modes.md              # JSON vs Markdown
│   └── pattern-matching.md          # Pattern system
│
├── guides/                          # How-to guides
│   ├── structured-logging.md        # ⭐ Writing log-friendly scripts
│   ├── custom-patterns.md           # Creating patterns
│   ├── monitoring.md                # Process monitoring
│   └── remote-ssh.md                # Remote monitoring (Phase 3)
│
├── architecture/                    # Design docs
│   ├── design-principles.md         # Why these choices
│   ├── data-flow.md                # How data moves
│   └── mcp-integration.md           # MCP server (Phase 3)
│
├── api/                             # API reference
│   ├── json-schema.md               # JSON output schema
│   ├── pattern-format.md            # Pattern file format
│   └── config-format.md             # Config file format
│
└── development/                     # Contributing
    ├── setup.md                     # Dev environment
    ├── testing.md                   # Testing guide
    └── patterns.md                  # Code patterns
```

### Key Documentation (Priority Order)

1. **README.md** (Phase 1)
   - Project overview
   - Quick start
   - Installation
   - Basic usage examples
   - Links to docs

2. **quickstart.md** (Phase 1)
   - 5-minute getting started
   - Install logsift
   - Analyze a log
   - Monitor a command
   - View results

3. **cli-reference.md** (Phase 1)
   - Complete command reference
   - All flags and options
   - Examples for each command

4. **concepts/agentic-integration.md** (Phase 1) ⭐ CRITICAL
   - How to use with Claude Code
   - Agentic loop patterns
   - JSON output schema explanation
   - Automated fix/retry workflows
   - Best practices for automation

5. **guides/structured-logging.md** (Phase 1) ⭐ CRITICAL
   - Industry standards (JSON, syslog, etc.)
   - Recommended formats
   - Writing scripts for logsift
   - Best practices
   - Examples

6. **guides/custom-patterns.md** (Phase 2)
   - Creating pattern libraries
   - TOML format specification
   - Contributing to community patterns
   - Testing patterns

7. **architecture/mcp-integration.md** (Phase 3)
   - MCP server setup
   - Tool definitions
   - Claude Code native integration
   - Advanced workflows

### Documentation Tools

- **MkDocs** - Static site generator
- **Material theme** - Beautiful, searchable docs
- **mkdocstrings** - Auto-generate API docs from docstrings

```yaml
# mkdocs.yml
site_name: logsift
site_description: Intelligent log analysis for agentic workflows
repo_url: https://github.com/yourusername/logsift

theme:
  name: material
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - search.suggest
    - search.highlight
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true

nav:
  - Home: index.md
  - Quick Start: quickstart.md
  - Installation: installation.md
  - CLI Reference: cli-reference.md
  - Concepts:
      - Agentic Integration: concepts/agentic-integration.md
      - Output Modes: concepts/output-modes.md
      - Pattern Matching: concepts/pattern-matching.md
  - Guides:
      - Structured Logging: guides/structured-logging.md
      - Custom Patterns: guides/custom-patterns.md
      - Process Monitoring: guides/monitoring.md
  - Architecture:
      - Design Principles: architecture/design-principles.md
      - Data Flow: architecture/data-flow.md
  - API Reference:
      - JSON Schema: api/json-schema.md
      - Pattern Format: api/pattern-format.md
      - Config Format: api/config-format.md
  - Development:
      - Setup: development/setup.md
      - Testing: development/testing.md
```

---

## ✅ Success Criteria

### Phase 1 Success

- [ ] Can analyze existing log files
- [ ] Can monitor commands and capture output
- [ ] JSON output matches schema specification
- [ ] Markdown output is beautiful and readable
- [ ] Auto-detects output format (interactive vs headless)
- [ ] Config file works correctly
- [ ] 80%+ test coverage
- [ ] Can install with `uv tool install`
- [ ] Documentation covers core features
- [ ] Works on macOS and Linux

### Phase 2 Success

- [ ] Custom pattern libraries load correctly
- [ ] fzf integration works beautifully
- [ ] Dual output modes function correctly
- [ ] Live watching provides real-time analysis
- [ ] External log support works
- [ ] Notifications work cross-platform
- [ ] Log cleanup maintains cache properly
- [ ] 80%+ test coverage maintained
- [ ] Pattern library has 10+ built-in patterns
- [ ] Documentation covers all features

### Phase 3 Success

- [ ] MCP server works with Claude Code
- [ ] Can be called as native MCP tool
- [ ] Remote SSH monitoring functional
- [ ] Export features work
- [ ] Performance acceptable for large logs (>100MB)
- [ ] Complete comprehensive documentation
- [ ] Ready for open-source release
- [ ] Community contribution guidelines

### Overall Project Success

- [ ] Used daily in dotfiles automated testing
- [ ] Reduces LLM context usage by 95%+ (2000 lines → 50 lines)
- [ ] Enables fully automated fix/retry loops
- [ ] Beautiful human output for learning
- [ ] Extensible pattern library growing
- [ ] 5+ community contributors
- [ ] 100+ GitHub stars
- [ ] Featured in Claude Code examples

---

## 🚀 Getting Started (First Steps)

### Immediate Actions

1. **Create Project**

   ```bash
   cd ~/code
   mkdir logsift
   cd logsift
   git init
   ```

2. **Copy This Planning Document**

   ```bash
   cp /Users/chris/dotfiles/.planning/logsift-planning.md PLANNING.md
   ```

3. **Create Basic Structure**

   ```bash
   mkdir -p src/logsift
   mkdir -p tests/{unit,integration,fixtures}
   mkdir -p docs
   touch src/logsift/__init__.py
   touch README.md
   ```

4. **Create pyproject.toml**

   ```bash
   # See detailed pyproject.toml in this document
   ```

5. **Copy CLAUDE.md**

   ```bash
   cp /Users/chris/dotfiles/CLAUDE.md CLAUDE.md
   # Edit to remove dotfiles-specific content
   # Keep: Git hygiene, problem-solving philosophy, testing
   ```

6. **Install Dependencies**

   ```bash
   pip install -e '.[dev]'
   ```

7. **First Test**

   ```bash
   # Create simple test
   # Run pytest
   pytest
   ```

### Development Workflow

1. **Pick a task from Phase 1**
2. **Write tests first** (TDD approach)
3. **Implement feature**
4. **Run tests** (`pytest`)
5. **Check coverage** (`pytest --cov`)
6. **Lint/format** (`ruff check`, `ruff format`)
7. **Commit with good message** (atomic commits)
8. **Document in docstrings and docs/**

---

## 🎓 Critical Lessons from dotfiles (CLAUDE.md)

### Git Hygiene (Non-Negotiable)

- ALWAYS review: `git status`, `git diff --staged`
- NEVER use `git add -A` without careful review
- Atomic commits - ONE logical change
- NEVER bypass pre-commit hooks
- NEVER push to remote unless requested

### Problem-Solving Philosophy

- Solve root causes, not symptoms
- Think before coding
- Test minimal changes
- DRY principles
- When debugging, check fundamentals first

### Documentation

- Write in imperative tone
- WHY over WHAT
- Technical and factual
- Reference files, don't duplicate code
- Keep up to date

### Testing

- Test behavior, not implementation
- Aim for 80%+ coverage
- Integration tests are critical
- Use real-world fixtures
- Fast execution

---

## 📖 Key Research & Sources

### Agentic Workflows

- [Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Agentic Design Patterns: Tool Use](https://www.deeplearning.ai/the-batch/agentic-design-patterns-part-3-tool-use/)
- [Agentic Design Patterns: Reflection](https://www.deeplearning.ai/the-batch/agentic-design-patterns-part-2-reflection/)

### MCP & Tool Integration

- [Agent SDK Overview](https://docs.claude.com/en/api/agent-sdk/overview)
- [Advanced Tool Use](https://www.anthropic.com/engineering/advanced-tool-use)
- [Model Context Protocol](https://modelcontextprotocol.io/)

### Structured Logging

- [Structured Logging Best Practices](https://betterstack.com/community/guides/logging/structured-logging/)
- [JSON Logging Guide](https://betterstack.com/community/guides/logging/json-logging/)
- [Python structlog](https://www.structlog.org/en/stable/logging-best-practices.html)
- [Syslog RFC 5424](https://datatracker.ietf.org/doc/html/rfc5424)
- [GitLab CI/CD Logging](https://the-pi-guy.com/blog/gitlab_cicd_and_logging_best_practices_for_logging_in_your_cicd_pipeline_and_deployed_applications/)

### LLM Tool Design

- [Patterns for Building LLM Systems](https://eugeneyan.com/writing/llm-patterns/)
- [Agent System Design Patterns](https://docs.databricks.com/aws/en/generative-ai/guide/agent-system-design-patterns)

---

## 🔄 Future Enhancements (Post-Phase 3)

### Community Features

- **Pattern Marketplace** - Share and discover pattern libraries
- **Web UI** - Browse logs and summaries via web interface
- **Plugin System** - Custom extractors and formatters
- **Language Support** - Support logs in multiple languages

### Advanced Analysis

- **ML-Based Error Classification** - Train model on error patterns
- **Root Cause Analysis** - Link related errors across logs
- **Performance Metrics** - Extract timing and resource usage
- **Trend Analysis** - Historical error patterns

### Integration Ecosystem

- **GitHub Actions Integration** - Native GitHub Actions workflow
- **GitLab CI Integration** - GitLab CI/CD pipeline support
- **Docker Integration** - Container log analysis
- **Kubernetes Integration** - Pod log aggregation
- **VS Code Extension** - Analyze logs in editor

### Enterprise Features

- **Multi-User Support** - Team pattern libraries
- **Access Control** - Permissions for sensitive logs
- **Audit Logging** - Track who analyzed what
- **Compliance** - GDPR, SOC2 compliance

---

## 📝 Notes & Reminders

### Context from Previous Session

This planning document captures the complete context from our extensive planning session on 2025-11-27. Key decisions made:

1. **Name**: logsift (clear, actionable, universal)
2. **Language**: Python 3.11+ (not Bash - avoiding "behemoth" trap)
3. **Primary Purpose**: LLM-driven automated workflows (agentic-first)
4. **Secondary Purpose**: Beautiful human-readable output
5. **Dual Output**: JSON + Markdown simultaneously
6. **Pattern System**: Community-driven, extensible
7. **Location**: Standalone project in `~/code/logsift/`
8. **Distribution**: `uv tool install` for system-wide use

### Moving Forward

1. This document is comprehensive enough to implement from scratch
2. All architectural decisions are documented with rationale
3. Phase breakdown provides clear roadmap
4. Success criteria define "done" for each phase
5. Testing strategy ensures quality
6. Research is captured with sources

### If Starting Fresh in logsift Directory

1. Copy this planning document to `~/code/logsift/PLANNING.md`
2. Copy dotfiles `CLAUDE.md` patterns (git hygiene, testing, docs)
3. Follow "Getting Started" section above
4. Reference this document for all architectural decisions
5. Update this document as you learn and adapt

---

## 🎉 Final Thoughts

This is an **ambitious**, **well-designed** project that will:

- ✅ Enable truly automated software development workflows
- ✅ Save massive amounts of LLM context
- ✅ Provide beautiful human-readable output for learning
- ✅ Build extensible community knowledge base
- ✅ Pioneer patterns for agentic tool design
- ✅ Potentially become essential tool in AI-assisted development

**The vision is clear. The architecture is solid. The roadmap is detailed.**

**Time to build something amazing! 🚀**

---

*End of Planning Document*

*Last Updated: 2025-11-27*
*Next Review: After Phase 1 completion*
