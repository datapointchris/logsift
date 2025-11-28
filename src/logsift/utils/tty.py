"""TTY detection for auto-format selection.

Detects whether output is going to an interactive terminal or being piped.
"""

import sys


def is_interactive() -> bool:
    """Check if running in an interactive terminal.

    Returns:
        True if interactive, False if headless/piped
    """
    return sys.stdout.isatty()


def detect_output_format() -> str:
    """Auto-detect appropriate output format based on terminal.

    Returns:
        'markdown' for interactive terminals, 'json' for headless
    """
    return 'markdown' if is_interactive() else 'json'
