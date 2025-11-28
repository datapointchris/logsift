"""Timestamp parsing and formatting utilities.

Handles parsing timestamps from various formats using python-dateutil.
"""

from datetime import datetime

from dateutil import parser


def parse_timestamp(timestamp_str: str) -> datetime | None:
    """Parse a timestamp string in any common format.

    Args:
        timestamp_str: Timestamp string to parse

    Returns:
        datetime object or None if parsing fails
    """
    try:
        return parser.parse(timestamp_str)
    except (ValueError, parser.ParserError):
        return None


def format_timestamp(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format a datetime object as a string.

    Args:
        dt: datetime object to format
        format_str: strftime format string

    Returns:
        Formatted timestamp string
    """
    return dt.strftime(format_str)


def format_duration(seconds: float) -> str:
    """Format a duration in seconds to human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration string (e.g., "3m 42s")
    """
    if seconds < 60:
        return f'{seconds:.0f}s'
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f'{minutes}m {secs}s'
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f'{hours}h {minutes}m'
