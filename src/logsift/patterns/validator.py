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
    required_fields = ['name', 'regex', 'severity', 'description', 'tags']
    for field in required_fields:
        if field not in pattern:
            raise ValueError(f"Pattern missing required field: '{field}'")

    valid_severities = ['error', 'warning', 'info']
    if pattern['severity'] not in valid_severities:
        raise ValueError(f"Invalid severity '{pattern['severity']}'. Must be one of: {valid_severities}")

    try:
        re.compile(pattern['regex'])
    except re.error as e:
        raise ValueError(f'Invalid regex pattern: {e}') from e

    if not isinstance(pattern['tags'], list) or len(pattern['tags']) == 0:
        raise ValueError('Pattern tags must be a non-empty list')

    # The detector reads only suggestion and context_lines_after beyond these; any other key is ignored


def validate_pattern_file(pattern_file: dict[str, Any]) -> None:
    """Validate a pattern file structure.

    Args:
        pattern_file: Parsed TOML pattern file as dictionary

    Raises:
        ValueError: If pattern file is invalid
    """
    if 'patterns' not in pattern_file:
        raise ValueError("Pattern file must have a 'patterns' key")

    if not isinstance(pattern_file['patterns'], list):
        raise ValueError("'patterns' must be a list")

    if len(pattern_file['patterns']) == 0:
        raise ValueError('Pattern file must contain at least one pattern (patterns list is empty)')

    pattern_names = set()
    for idx, pattern in enumerate(pattern_file['patterns']):
        try:
            validate_pattern(pattern)
        except ValueError as e:
            raise ValueError(f'Invalid pattern at index {idx}: {e}') from e

        name = pattern['name']
        if name in pattern_names:
            raise ValueError(f"Duplicate pattern name: '{name}'")
        pattern_names.add(name)
