"""Apply patterns to log content.

Matches log entries against pattern rules and extracts metadata.
"""

import re
from typing import Any


def match_patterns(log_entry: dict[str, Any], patterns: dict[str, Any]) -> dict[str, Any] | None:
    """Match a log entry against available patterns.

    Args:
        log_entry: Normalized log entry dictionary
        patterns: Dictionary of available patterns

    Returns:
        Match result with pattern metadata if found, None otherwise
    """
    # Check if log entry has a message field
    message = log_entry.get('message')
    if not message:
        return None

    # If no patterns provided, return None
    if not patterns:
        return None

    # Iterate through each category of patterns
    for pattern_list in patterns.values():
        if not isinstance(pattern_list, list):
            continue

        # Try each pattern in the category
        for pattern in pattern_list:
            try:
                regex = pattern.get('regex')
                if not regex:
                    continue

                # Try to match the pattern against the message
                if re.search(regex, message):
                    # Build the match result with pattern metadata
                    match_result = {
                        'pattern_name': pattern['name'],
                        'severity': pattern['severity'],
                        'description': pattern['description'],
                        'tags': pattern['tags'],
                    }

                    # Include suggestion if present
                    if 'suggestion' in pattern:
                        match_result['suggestion'] = pattern['suggestion']

                    return match_result

            except (KeyError, re.error):
                # Skip malformed patterns or regex errors
                continue

    # No match found
    return None
