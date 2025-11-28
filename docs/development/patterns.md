# Code Patterns and Standards

Code style and architecture patterns for logsift.

## Code Style

### Type Hints

Use Python 3.13+ modern syntax:

```python
# ✓ GOOD - Modern syntax
def parse(log_content: str) -> list[LogLine]:
    ...

def get_config(key: str) -> str | None:
    ...

# ✗ BAD - Old syntax
from typing import List, Optional

def parse(log_content: str) -> List[LogLine]:
    ...

def get_config(key: str) -> Optional[str]:
    ...
```

### Fail Fast

No defensive coding with inline defaults:

```python
# ✓ GOOD - Fail fast
value = config.key  # Raises AttributeError if missing

# ✗ BAD - Hides misconfiguration
value = getattr(config, 'key', 'default')
```

Configuration validation happens once at startup in `config/validator.py`. Business logic should assume valid configuration.

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
    raise FileNotFoundError(f"Log file not found: {log_file}")

# ✗ BAD - Generic exception
if not log_file.exists():
    raise Exception(f"File not found: {log_file}")
```

## Architecture Patterns

### Dataclasses

Use dataclasses for data structures:

```python
from dataclasses import dataclass, field

@dataclass
class Error:
    id: int
    severity: str
    message: str
    file: str | None = None
    file_line: int | None = None
    tags: list[str] = field(default_factory=list)
```

### Composition Over Inheritance

```python
# ✓ GOOD - Composition
class Analyzer:
    def __init__(self):
        self.parser = Parser()
        self.extractor = Extractor()
        self.matcher = Matcher()

    def analyze(self, log: str) -> dict:
        lines = self.parser.parse(log)
        errors = self.extractor.extract(lines)
        return self.matcher.match(errors)

# ✗ BAD - Deep inheritance
class SpecificAnalyzer(BaseAnalyzer):
    ...
```

### Dependency Injection

Pass dependencies explicitly:

```python
# ✓ GOOD - Explicit dependencies
def format_json(analysis: dict, output_path: Path | None = None) -> str:
    ...

# ✗ BAD - Hidden dependencies
def format_json(analysis: dict) -> str:
    output_path = get_global_config().output_path
    ...
```

## Testing Patterns

### Arrange-Act-Assert

```python
def test_parser_extracts_errors():
    # Arrange
    log_content = "ERROR: Something failed"
    parser = Parser()

    # Act
    result = parser.parse(log_content)

    # Assert
    assert len(result) == 1
    assert "failed" in result[0].message
```

### Fixtures for Reusability

```python
@pytest.fixture
def sample_error_log():
    return """
    ERROR: Connection failed at host:port
    File "app.py", line 42
    """

def test_extract_file_reference(sample_error_log):
    errors = extract_errors(sample_error_log)
    assert errors[0].file == "app.py"
    assert errors[0].file_line == 42
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

from logsift.core.parser import Parser

# Constants
DEFAULT_CONTEXT_LINES = 2

# Classes
class Analyzer:
    ...

# Functions
def analyze_log(log_path: Path) -> dict:
    ...

# Main guard
if __name__ == "__main__":
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

from logsift.core.parser import Parser
from logsift.utils.tty import detect_output_format

# ✗ BAD - Mixed order
from logsift.core.parser import Parser
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

```python
from pathlib import Path

def load_config(config_path: Path | str | None = None) -> dict:
    """Load configuration from file."""
    if config_path is None:
        config_path = Path.home() / '.config' / 'logsift' / 'config.toml'
    else:
        config_path = Path(config_path)

    # Expand tilde
    config_path = config_path.expanduser()

    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    return load_toml(config_path)
```

### TTY Detection

```python
import sys

def detect_output_format() -> str:
    """Detect optimal output format based on TTY."""
    if sys.stdout.isatty():
        return 'markdown'  # Terminal - human readable
    else:
        return 'json'  # Piped/redirected - machine readable
```

## Anti-Patterns to Avoid

### 1. Global State

```python
# ✗ BAD
GLOBAL_CONFIG = load_config()

def analyze(log: str) -> dict:
    context_lines = GLOBAL_CONFIG.context_lines
    ...

# ✓ GOOD
def analyze(log: str, context_lines: int = 2) -> dict:
    ...
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
