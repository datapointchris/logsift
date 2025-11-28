# Development Setup

Complete guide for contributing to logsift.

## Requirements

- Python 3.13+
- uv (package installer)
- Git

## Initial Setup

```bash
# Clone repository
git clone https://github.com/datapointchris/logsift.git
cd logsift

# Install all dependencies (dev + test groups)
uv sync --group dev --group test

# Install pre-commit hooks
uv run pre-commit install --install-hooks
uv run pre-commit install --hook-type commit-msg

# Install as editable tool
uv tool install --editable .
```

## Verify Installation

```bash
# Check logsift command works
logsift --version

# Run tests
uv run pytest -v

# Run pre-commit hooks
uv run pre-commit run --all-files
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code in `src/logsift/`

### 3. Write Tests

Create tests in `tests/unit/` or `tests/integration/`

```bash
# Run tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=logsift --cov-report=term
```

### 4. Run Pre-commit

```bash
uv run pre-commit run --all-files
```

This runs:

- ruff (linting + formatting)
- mypy (type checking)
- bandit (security scanning)
- codespell, markdownlint, shellcheck
- And 10+ other checks

### 5. Commit Changes

```bash
git add <files>
git commit -m "feat: add new feature"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `chore:` - Maintenance

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Create pull request on GitHub.

## Project Structure

```
logsift/
├── src/logsift/              # Source code
│   ├── cli.py                # CLI entry point
│   ├── commands/             # CLI commands
│   ├── core/                 # Analysis engine
│   ├── patterns/             # Pattern system
│   ├── output/               # Formatters
│   ├── monitor/              # Process monitoring
│   ├── cache/                # Cache management
│   └── utils/                # Utilities
├── tests/                    # Tests
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── conftest.py           # Shared fixtures
├── docs/                     # Documentation
├── pyproject.toml            # Project config
└── README.md                 # Project README
```

## Running Tests

```bash
# All tests
uv run pytest -v

# Specific file
uv run pytest tests/unit/test_parser.py -v

# Specific test
uv run pytest tests/unit/test_parser.py::test_parser_initialization -v

# With coverage
uv run pytest --cov=logsift --cov-report=term

# Watch mode (requires pytest-watch)
uv run ptw
```

## Code Quality Tools

### Ruff (Linting + Formatting)

```bash
# Check linting
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/
```

### Mypy (Type Checking)

```bash
uv run mypy src/logsift --config-file pyproject.toml
```

### Bandit (Security)

```bash
uv run bandit -c pyproject.toml -r .
```

## Pre-commit Hooks

All hooks (15 total):

```bash
# Run all hooks
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run ruff --all-files

# Update hooks
uv run pre-commit autoupdate
```

## Testing Philosophy

Follow these principles:

1. **Test behavior, not implementation**
2. **Aim for 80%+ coverage**
3. **Integration tests as important as unit tests**
4. **Use real log samples**

## Documentation

Build docs locally:

```bash
# Install mkdocs (in dev group)
uv sync --group dev

# Serve docs locally
uv run mkdocs serve

# Build static site
uv run mkdocs build
```

## Troubleshooting

### Pre-commit Fails

```bash
# See what failed
uv run pre-commit run --all-files

# Auto-fix what can be fixed
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/

# Re-run
uv run pre-commit run --all-files
```

### Tests Fail

```bash
# Run with verbose output
uv run pytest -vv

# Run with print statements
uv run pytest -s

# Run specific failing test
uv run pytest tests/unit/test_file.py::test_name -vv
```

### Type Errors

```bash
# Check types
uv run mypy src/logsift

# See specific error
uv run mypy src/logsift --show-error-codes
```

## See Also

- [Testing Guide](testing.md) - Testing best practices
- [Code Patterns](patterns.md) - Code standards
- [Contributing Guide](https://github.com/datapointchris/logsift/blob/main/CONTRIBUTING.md)
