"""Plain text formatter for fallback output.

Generates simple plain text output without colors or formatting.
"""

from typing import Any


def format_plain(analysis_result: dict[str, Any]) -> str:
    """Format analysis results as plain text.

    Args:
        analysis_result: Analysis results dictionary

    Returns:
        Plain text string without formatting
    """
    raise NotImplementedError('Plain formatter not yet implemented')
