# Testing Guide

Best practices for testing logsift.

## Testing Philosophy

> "Test behavior, not implementation. Aim for 80%+ coverage. Integration tests are as important as unit tests."

## Test Structure

```
tests/
├── unit/                  # Fast, isolated unit tests
│   ├── test_parser.py
│   ├── test_extractors.py
│   ├── test_matchers.py
│   └── ...
├── integration/           # End-to-end integration tests
│   ├── test_cli.py
│   └── test_workflows.py
├── fixtures/              # Shared test data
│   └── sample_logs/
└── conftest.py           # Shared fixtures and config
```

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
    log_content = "ERROR: Something failed\nWARNING: Be careful"

    lines = parser.parse(log_content)

    assert len(lines) == 2
    assert lines[0].content == "ERROR: Something failed"
    assert lines[1].content == "WARNING: Be careful"
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
    assert "Connection failed" in errors[0].message
```

## Writing Integration Tests

Test complete workflows:

```python
from typer.testing import CliRunner
from logsift.cli import app

runner = CliRunner()

def test_monitor_command_end_to_end():
    """Test complete monitor workflow."""
    result = runner.invoke(
        app,
        ['monitor', '--format=json', '--', 'echo', 'test']
    )

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
    result = parser.parse("")
    assert result == []

# ✗ BAD - Test implementation
def test_parser_calls_internal_method():
    parser = Parser()
    assert parser._internal_method() is called
```

### 2. Use Descriptive Names

```python
# ✓ GOOD
def test_extract_errors_from_python_traceback():
    ...

# ✗ BAD
def test_extractor():
    ...
```

### 3. One Assertion Per Concept

```python
# ✓ GOOD
def test_error_has_correct_message():
    error = extract_first_error(log)
    assert error.message == "Expected message"

def test_error_has_correct_line_number():
    error = extract_first_error(log)
    assert error.line_number == 42

# ✗ BAD
def test_error():
    error = extract_first_error(log)
    assert error.message == "Expected message"
    assert error.line_number == 42
    assert error.severity == "error"
    # Too many unrelated assertions
```

### 4. Test Edge Cases

```python
def test_parser_handles_edge_cases():
    parser = Parser()

    # Empty input
    assert parser.parse("") == []

    # Single line
    assert len(parser.parse("one line")) == 1

    # Very long line
    long_line = "x" * 10000
    assert len(parser.parse(long_line)) == 1

    # Unicode
    assert len(parser.parse("日本語")) == 1
```

## Mocking

Use pytest-mock for mocking:

```python
def test_process_monitor_handles_command_failure(mocker):
    """Test that ProcessMonitor handles failed commands."""
    # Mock subprocess.run to return failure
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = mocker.Mock(
        returncode=1,
        stdout="",
        stderr="Command failed"
    )

    monitor = ProcessMonitor(['false'])
    result = monitor.run()

    assert result['success'] is False
    assert result['exit_code'] == 1
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

Create fixtures for real-world logs:

```
tests/fixtures/sample_logs/
├── python_traceback.log
├── npm_build_error.log
├── cargo_compile_error.log
└── pytest_failure.log
```

Use in tests:

```python
from pathlib import Path

def test_analyze_real_python_traceback():
    """Test analyzing real Python traceback."""
    fixture_path = Path(__file__).parent.parent / 'fixtures' / 'sample_logs' / 'python_traceback.log'
    log_content = fixture_path.read_text()

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert result['stats']['total_errors'] > 0
    assert any('Traceback' in e['message'] for e in result['errors'])
```

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
