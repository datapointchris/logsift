# Code Patterns and Standards

Code style and architecture patterns for logsift.

## Code Style

### Type Hints

Use Python 3.13+ modern syntax:

```python
# ✓ GOOD - Modern syntax
def parse(log_content: str) -> list[dict[str, Any]]: ...


def get_config(key: str) -> str | None: ...


# ✗ BAD - Old syntax
from typing import Dict, List, Optional


def parse(log_content: str) -> List[Dict[str, Any]]: ...


def get_config(key: str) -> Optional[str]: ...
```

### Fail Fast

No defensive coding with inline defaults:

```python
# ✓ GOOD - Fail fast
value = config.key  # Raises AttributeError if missing

# ✗ BAD - Hides misconfiguration
value = getattr(config, 'key', 'default')
```

`config.toml` is read and validated once, in the CLI's root callback, by `config/loader.py`. Business logic should assume valid configuration.

### Docstrings

Use Google-style docstrings:

```python
def analyze(log_content: str) -> dict[str, Any]:
    """Analyze log content and extract errors.

    Args:
        log_content: Raw log text to analyze.

    Returns:
        Analysis result with errors, warnings, and suggestions.

    Raises:
        ValueError: If log_content is empty.
    """
    ...
```

### Error Handling

Be specific with exceptions:

```python
# ✓ GOOD - Specific exception
if not log_file.exists():
    raise FileNotFoundError(f'Log file not found: {log_file}')

# ✗ BAD - Generic exception
if not log_file.exists():
    raise Exception(f'File not found: {log_file}')
```

## Architecture Patterns

### Dictionaries Between Stages

Log entries, issues and the analysis result are plain dictionaries, because a JSON log line's own
fields ride along on its entry and the result is written straight to JSON.
`schemas/analysis.schema.json` is the shape a result takes in the output, so a new field goes there
in the same change.

### Composition Over Inheritance

```python
# ✓ GOOD - Composition, as core/analyzer.py does it
class Analyzer:
    def __init__(self, context_lines: int = 2) -> None:
        self.parser = LogParser()
        self.pattern_loader = PatternLoader()
        self.issue_detector = IssueDetector()
        self.file_reference_detector = FileReferenceDetector()

    def analyze(self, log_content: str) -> dict[str, Any]:
        log_entries = self.parser.parse(log_content)
        errors, warnings = self.issue_detector.detect_issues(log_entries, self.patterns)
        ...


# ✗ BAD - Deep inheritance
class SpecificAnalyzer(BaseAnalyzer): ...
```

### Dependency Injection

Pass dependencies explicitly:

```python
# ✓ GOOD - Explicit dependencies
def format_json(analysis: dict, output_path: Path | None = None) -> str: ...


# ✗ BAD - Hidden dependencies
def format_json(analysis: dict) -> str:
    output_path = get_global_config().output_path
    ...
```

## Testing Patterns

### Arrange-Act-Assert

```python
def test_parser_keeps_the_message():
    # Arrange
    log_content = 'ERROR: Something failed'
    parser = LogParser()

    # Act
    result = parser.parse(log_content)

    # Assert
    assert len(result) == 1
    assert 'failed' in result[0]['message']
```

### Fixtures for Reusability

```python
@pytest.fixture
def sample_error_log():
    return """
    Error: failed to load config at app.py:42
    """


def test_extract_file_reference(sample_error_log):
    errors = Analyzer().analyze(sample_error_log)['errors']
    assert errors[0]['file_references'] == [('app.py', 42)]
```

## File Organization

### Module Structure

```python
# module.py
"""Module docstring explaining purpose."""

# Imports - stdlib, third-party, local
import sys
from pathlib import Path

import typer

from logsift.core.parser import LogParser

# Constants
DEFAULT_CONTEXT_LINES = 2


# Classes
class Analyzer: ...


# Functions
def analyze_log(log_path: Path) -> dict: ...


# Main guard
if __name__ == '__main__':
    ...
```

### Import Order

1. Standard library
2. Third-party packages
3. Local imports

```python
# ✓ GOOD
import sys
from pathlib import Path

import typer
from rich.console import Console

from logsift.core.parser import LogParser
from logsift.output.analysis_format import render_analysis

# ✗ BAD - Mixed order
from logsift.core.parser import LogParser
import sys
import typer
from pathlib import Path
```

## Common Patterns

### Pattern Validation

```python
def validate_pattern(pattern: dict[str, Any]) -> None:
    """Validate pattern dictionary."""
    required_fields = ['name', 'regex', 'severity', 'description', 'tags']

    for field in required_fields:
        if field not in pattern:
            raise ValueError(f"Pattern missing required field: '{field}'")

    # Validate regex compiles
    try:
        re.compile(pattern['regex'])
    except re.error as e:
        raise ValueError(f'Invalid regex pattern: {e}') from e
```

### File Path Handling

Resolve a config or cache path through its XDG variable, as `xdg_dirs.py` does, rather than
hardcoding `~/.config`:

```python
import os
from pathlib import Path


def config_dir() -> Path:
    value = os.environ.get('XDG_CONFIG_HOME', '')
    base = Path(value) if value and Path(value).is_absolute() else Path.home() / '.config'
    return base / 'logsift'
```

### TTY Detection

`output/analysis_format.py` resolves `--format auto` against the stream the analysis is printed
to, which a test passes in rather than patching `sys.stdout`.

## Anti-Patterns to Avoid

### 1. Global State

```python
# ✗ BAD
GLOBAL_CONFIG = load_config()


def analyze(log: str) -> dict:
    context_lines = GLOBAL_CONFIG.context_lines
    ...


# ✓ GOOD
def analyze(log: str, context_lines: int = 2) -> dict: ...
```

### 2. Defensive Coding

```python
# ✗ BAD
return data.get('field', [])

# ✓ GOOD
return data['field']  # Let it fail if malformed
```

### 3. Magic Values

```python
# ✗ BAD
if severity == 1:
    ...

# ✓ GOOD
SEVERITY_ERROR = 1
if severity == SEVERITY_ERROR:
    ...

# Even better - use strings
if severity == 'error':
    ...
```

## See Also

- [Development Setup](setup.md) - Environment setup
- [Testing Guide](testing.md) - Testing best practices
