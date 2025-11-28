"""Validate pattern file format and syntax.

Ensures pattern files conform to the expected schema and regex is valid.
"""

import re
from typing import Any


def validate_pattern(pattern: dict[str, Any]) -> None:
    """Validate a single pattern dictionary.

    Args:
        pattern: Pattern dictionary to validate

    Raises:
        ValueError: If pattern is invalid
    """
    # Check required fields
    required_fields = ['name', 'regex', 'severity', 'description', 'tags']
    for field in required_fields:
        if field not in pattern:
            raise ValueError(f"Pattern missing required field: '{field}'")

    # Validate severity
    valid_severities = ['error', 'warning', 'info']
    if pattern['severity'] not in valid_severities:
        raise ValueError(f"Invalid severity '{pattern['severity']}'. Must be one of: {valid_severities}")

    # Validate regex
    try:
        re.compile(pattern['regex'])
    except re.error as e:
        raise ValueError(f'Invalid regex pattern: {e}') from e

    # Validate tags is non-empty list
    if not isinstance(pattern['tags'], list) or len(pattern['tags']) == 0:
        raise ValueError('Pattern tags must be a non-empty list')

    # Optional fields are allowed (like 'suggestion')


def validate_pattern_file(pattern_file: dict[str, Any]) -> None:
    """Validate a pattern file structure.

    Args:
        pattern_file: Parsed TOML pattern file as dictionary

    Raises:
        ValueError: If pattern file is invalid
    """
    # Check for 'patterns' key
    if 'patterns' not in pattern_file:
        raise ValueError("Pattern file must have a 'patterns' key")

    # Check patterns is a list
    if not isinstance(pattern_file['patterns'], list):
        raise ValueError("'patterns' must be a list")

    # Check patterns is not empty
    if len(pattern_file['patterns']) == 0:
        raise ValueError('Pattern file must contain at least one pattern (patterns list is empty)')

    # Validate each pattern
    pattern_names = set()
    for idx, pattern in enumerate(pattern_file['patterns']):
        try:
            validate_pattern(pattern)
        except ValueError as e:
            raise ValueError(f'Invalid pattern at index {idx}: {e}') from e

        # Check for duplicate names
        name = pattern['name']
        if name in pattern_names:
            raise ValueError(f"Duplicate pattern name: '{name}'")
        pattern_names.add(name)
