"""Test file with mypy type violations."""


def add_numbers(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


# Type mismatch - passing string to int parameter
result = add_numbers('hello', 5)


# Incompatible return type
def get_name() -> str:
    """Get name."""
    return 123


# Missing annotation
def process_data(x):
    """Process data."""
    return x * 2
