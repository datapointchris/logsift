# Testing Guide

Best practices for testing logsift.

## Testing Philosophy

> "Test behavior, not implementation. Aim for 80%+ coverage. Integration tests are as important as unit tests."

## Test Structure

```text
tests/
├── unit/                        # Fast, isolated unit tests, one file per module
│   ├── test_parser.py
│   ├── test_analyzer.py
│   ├── test_patterns.py
│   └── ...
├── integration/                 # End-to-end runs through the CLI
│   ├── test_cli.py
│   ├── test_json_contract.py    # validates --format json against schemas/analysis.schema.json
│   ├── test_logs_cli.py
│   └── test_workflows.py
├── fixtures/
│   └── pre-commit-violations/   # files that fail each linter, for the pre-commit patterns
└── conftest.py                  # Isolates every test's cache, HOME and XDG directories
```

Most tests write their log inline or under `tmp_path` rather than reading a fixture file.

## Running Tests

```bash
# All tests
uv run pytest -v

# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v

# With coverage
uv run pytest --cov=logsift --cov-report=term

# Specific test
uv run pytest tests/unit/test_parser.py::test_parser_initialization -v
```

## Writing Unit Tests

Test individual components in isolation:

```python
from logsift.core.parser import Parser


def test_parser_initialization():
    """Test that Parser initializes correctly."""
    parser = Parser()
    assert parser is not None


def test_parse_plain_text():
    """Test parsing plain text logs."""
    parser = Parser()
    log_content = 'ERROR: Something failed\nWARNING: Be careful'

    lines = parser.parse(log_content)

    assert len(lines) == 2
    assert lines[0].content == 'ERROR: Something failed'
    assert lines[1].content == 'WARNING: Be careful'
```

### Using Fixtures

```python
import pytest


@pytest.fixture
def sample_log():
    """Provide sample log content."""
    return """
    [INFO] Application started
    [ERROR] Connection failed
    [WARNING] Retry attempt 1
    """


def test_extract_errors(sample_log):
    """Test error extraction."""
    from logsift.core.extractors import extract_errors

    errors = extract_errors(sample_log)

    assert len(errors) == 1
    assert 'Connection failed' in errors[0].message
```

## Writing Integration Tests

Test complete workflows:

```python
from typer.testing import CliRunner
from logsift.cli import app

runner = CliRunner()


def test_monitor_command_end_to_end():
    """Test complete monitor workflow."""
    result = runner.invoke(app, ['monitor', '--format=json', '--', 'echo', 'test'])

    assert result.exit_code == 0
    assert 'summary' in result.stdout

    # Parse JSON
    import json

    analysis = json.loads(result.stdout)
    assert analysis['summary']['status'] == 'success'
```

## Test Coverage

Current coverage: **85%** (245 tests passing)

Target: **80%+**

Check coverage:

```bash
uv run pytest --cov=logsift --cov-report=term
uv run pytest --cov=logsift --cov-report=html  # HTML report
```

## Testing Best Practices

### 1. Test Behavior, Not Implementation

```python
# ✓ GOOD - Test behavior
def test_parser_handles_empty_input():
    parser = Parser()
    result = parser.parse('')
    assert result == []


# ✗ BAD - Test implementation
def test_parser_calls_internal_method():
    parser = Parser()
    assert parser._internal_method() is called
```

### 2. Use Descriptive Names

```python
# ✓ GOOD
def test_extract_errors_from_python_traceback(): ...


# ✗ BAD
def test_extractor(): ...
```

### 3. One Assertion Per Concept

```python
# ✓ GOOD
def test_error_has_correct_message():
    error = extract_first_error(log)
    assert error.message == 'Expected message'


def test_error_has_correct_line_number():
    error = extract_first_error(log)
    assert error.line_number == 42


# ✗ BAD
def test_error():
    error = extract_first_error(log)
    assert error.message == 'Expected message'
    assert error.line_number == 42
    assert error.severity == 'error'
    # Too many unrelated assertions
```

### 4. Test Edge Cases

```python
def test_parser_handles_edge_cases():
    parser = Parser()

    # Empty input
    assert parser.parse('') == []

    # Single line
    assert len(parser.parse('one line')) == 1

    # Very long line
    long_line = 'x' * 10000
    assert len(parser.parse(long_line)) == 1

    # Unicode
    assert len(parser.parse('日本語')) == 1
```

## Mocking

Use pytest-mock for mocking:

```python
def test_monitor_command_sends_notification(mocker):
    """Test that monitor_command reports a finished run to the notifier."""
    # Patch the name where monitor_command looks it up, not where it is defined
    mock_notify = mocker.patch('logsift.commands.monitor.notify_command_complete')

    monitor_command(['echo', 'test'], output_format='json', save_log=False, notify=True)

    mock_notify.assert_called_once()
    assert mock_notify.call_args.kwargs['success'] is True
```

## Temporary Files

Use pytest's tmp_path fixture:

```python
def test_cache_manager_creates_log_file(tmp_path):
    """Test that CacheManager creates log files."""
    cache = CacheManager(cache_dir=tmp_path)

    log_file = cache.create_log_path('test', context='monitor')

    assert log_file.exists()
    assert log_file.parent == tmp_path / 'monitor'
```

## Testing with Real Logs

Keep a captured log beside the tests that read it under `tests/fixtures/`, as
`tests/unit/test_precommit_patterns.py` does with
`tests/fixtures/pre-commit-violations/codespell_output.txt`:

```python
from pathlib import Path

from logsift.core.analyzer import Analyzer


def test_codespell_output_is_matched():
    """Real codespell output reaches a codespell pattern."""
    log_content = Path('tests/fixtures/pre-commit-violations/codespell_output.txt').read_text()

    result = Analyzer().analyze(log_content)

    assert [w['pattern_name'] for w in result['warnings']] == ['codespell_typo', 'codespell_typo']
```

pre-commit excludes `tests/fixtures/pre-commit-violations/`, so its files may break the very rules
the hooks enforce.

## Continuous Testing

Run tests automatically on file changes:

```bash
# Install pytest-watch
uv add --group dev pytest-watch

# Watch mode
uv run ptw
```

## See Also

- [Development Setup](setup.md) - Environment setup
- [Code Patterns](patterns.md) - Code standards
