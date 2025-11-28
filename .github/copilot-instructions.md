# AI Coding Agent Instructions for logsift

## 🎯 PROFESSIONAL DEVELOPMENT STANDARDS 🎯

**You are a professional Python developer with expert-level knowledge and must write production-quality code that follows industry standards and conventions.**

**Code Quality Requirements**:

- Follow PEP 8 style guidelines and Python best practices
- Write clean, readable, maintainable code with meaningful variable names
- Use proper type hints for functions unless the type hint will be complex or Any
- Write docstrings in the Google style format for all public functions and classes, unless they are simple and the docstring would be superfluous
- Implement proper error handling with specific exceptions rather than broad catches
- Every piece of code must pass a rigorous code review - no hacky solutions or quick fixes
- Fail fast and explicit is better than hidden defaults or defensive coding in business logic

**Investigation Protocol**:

- When something is not working, STOP and investigate the root cause thoroughly
- Do NOT change unrelated components without understanding why they might be affected
- Examine existing tooling and patterns BEFORE making changes
- Follow the principle: "First understand, then fix"
- Document your investigation process and findings in a technical documentation style, not storytelling

**Code Review Process**:

- After completing any substantial changes, review your work for improvements
- Look for opportunities to enhance clarity, performance, or maintainability
- Refactor immediately if you identify better patterns or approaches
- Ensure all changes align with existing codebase patterns and conventions

## Project Overview: logsift

**logsift** is an intelligent log analysis and command monitoring tool designed specifically for LLM-driven automated workflows. The primary mission is to enable Claude Code and other AI agents to efficiently diagnose, fix, and retry failed operations with minimal context overhead.

### Core Mission

1. **Primary**: Enable LLM agents (Claude Code) to diagnose and fix errors autonomously
2. **Secondary**: Provide beautiful human-readable summaries for learning and debugging
3. **Tertiary**: Build extensible pattern library for community-driven error knowledge

### Architecture Principles

1. **Core is Analysis** - Log analysis is the primary function
2. **Monitoring is Optional** - Convenience wrapper, not required
3. **LLM-First Output** - JSON schema optimized for agent consumption
4. **Human-Friendly Too** - Markdown output for developer learning
5. **Extensible Patterns** - Community-driven error knowledge
6. **Universal Compatibility** - Works with ANY log format
7. **No External Dependencies** - Completely standalone tool

## Development Standards

### Testing Requirements

- **Target Coverage**: 80% (currently 40% due to stub implementations)
- **Test Philosophy**: Test behavior, not implementation
- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test complete workflows with real fixtures
- Use pytest fixtures for common test data and setup
- All tests must pass before committing

### Code Organization

```
logsift/
├── src/logsift/           # Source code
│   ├── cli.py             # Main CLI entry point
│   ├── commands/          # CLI command implementations
│   ├── core/              # Core analysis engine
│   ├── patterns/          # Pattern library system
│   ├── output/            # Dual output formatters
│   ├── monitor/           # Process monitoring
│   ├── config/            # Configuration management
│   ├── cache/             # Log caching system
│   ├── utils/             # Utility functions
│   └── mcp/               # MCP server (Phase 3)
└── tests/                 # Test suite
```

### Pattern Matching System

- Pattern files use TOML format (src/logsift/patterns/defaults/)
- Each pattern includes: name, regex, severity, description, tags, optional suggestion
- Built-in patterns for: common errors, brew, apt, npm, docker, cargo
- Custom patterns can be loaded from ~/.config/logsift/patterns/

### Output Modes

**Dual Output Philosophy**: "JSON for agents, Markdown for humans, both simultaneously when needed"

- **JSON**: Structured, predictable schema for LLM consumption
- **Markdown**: Beautiful, colored output for human reading
- **Auto-detection**: Uses TTY to determine interactive vs headless mode
- **Stream mode**: JSON to file, Markdown to stdout simultaneously

## Development Workflow

### Setting Up Development Environment

```bash
# Clone and enter directory
cd ~/code/logsift

# Install dependencies with uv
uv sync --group dev --group test

# Install pre-commit hooks
uv run pre-commit install --install-hooks
uv run pre-commit install --hook-type commit-msg

# Run tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=logsift --cov-report=term

# Build package
uv build
```

### Pre-commit Checks

All code must pass these checks before committing:

- Conventional commits (commit message format)
- actionlint (GitHub Actions validation)
- uv-lock (dependency sync)
- ruff (linting and formatting)
- codespell (spell checking)
- bandit (security scanning)
- markdownlint (markdown formatting)
- shellcheck (shell script validation)
- refurb (refactoring suggestions)
- pyupgrade (Python syntax modernization)
- mypy (type checking)

### Commit Message Format

Use conventional commits format:

```
feat: add new error pattern for npm
fix: correct file reference extraction regex
docs: update pattern library documentation
test: add integration tests for monitor command
chore: update dependencies
```

## Implementation Phases

### Phase 1 (Current): Core Analyzer + Basic Monitor (MVP)

Focus on building:

- Core analysis engine (parser, extractors, matchers)
- Basic CLI with monitor and analyze commands
- JSON and Markdown output formatters
- Default pattern libraries
- Basic test coverage

### Phase 2: Enhanced Features

- Custom pattern library loading
- Dual output modes (streaming)
- fzf integration for log browsing
- Live watching (tail mode)
- External log support
- Notifications

### Phase 3: MCP Server & Remote Monitoring

- MCP server for native Claude Code integration
- Remote SSH monitoring
- Advanced features and optimizations

## Critical Gotchas

1. **Coverage Threshold**: Currently set to 40% for Phase 1 (stub implementations). Will increase as functionality is implemented.
2. **Pattern Files**: Must be valid TOML with required fields (name, regex, severity, description)
3. **Output Format**: JSON schema must remain stable for LLM consumption
4. **TTY Detection**: Auto-format selection based on sys.stdout.isatty()
5. **Type Hints**: Use modern Python 3.13+ syntax (list[str] not List[str])
6. **Error Handling**: Prefer raising NotImplementedError for stubs, specific exceptions for errors

## Development Principles

**NO Defensive Coding**: Do NOT add inline defaults or fallbacks scattered throughout the codebase:

- ❌ WRONG: `getattr(config, 'key', 'default')` inside business logic
- ✅ RIGHT: `config.key` - let it fail fast if misconfigured
- Application should fail at startup if configuration is missing, not hide problems with random defaults

**Pattern Consistency**:

- Use existing utility functions (utils.tty, utils.colors, utils.timestamps)
- Follow established naming conventions
- Maintain consistent import patterns
- Keep docstrings concise but informative

**Testing Strategy**:

- Write tests BEFORE implementing features (TDD approach)
- Use real log samples in tests/fixtures/
- Test edge cases and error conditions
- Maintain 80%+ coverage as implementation progresses

## Documentation Standards

All documentation must be:

- Written for technical developers
- Precise and accurate
- Focused on "why" not just "what"
- Include code examples and technical details
- Keep up to date with code changes

See PLANNING.md for complete project specification and architecture details.

## Key Configuration Files

- `pyproject.toml`: Project metadata, dependencies, tool configs
- `.pre-commit-config.yaml`: Pre-commit hook configuration
- `.python-version`: Python version requirement (3.13)
- `.markdownlint.json`: Markdown linting rules
- `.shellcheckrc`: Shell script linting configuration
- `.gitignore`: Git ignore patterns
- `.dockerignore`: Docker build ignore patterns

## Resources

- Planning Document: PLANNING.md
- README: Quick start and features overview
- Tests: examples/fixtures/ for real-world log samples
- Patterns: src/logsift/patterns/defaults/ for pattern examples
