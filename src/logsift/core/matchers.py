"""Pattern matching engine for error detection.

Applies loaded patterns to log content to identify known error types.
"""

from typing import Any

from logsift.patterns.matcher import match_patterns


class PatternMatcher:
    """Apply patterns to log content to detect known errors."""

    def __init__(self, patterns: dict[str, Any] | None = None) -> None:
        """Initialize the pattern matcher.

        Args:
            patterns: Optional dictionary of patterns to use
        """
        self.patterns = patterns or {}

    def match(self, log_entry: dict[str, Any]) -> dict[str, Any] | None:
        """Match a log entry against loaded patterns.

        Args:
            log_entry: Normalized log entry dictionary

        Returns:
            Match result with pattern metadata if found, None otherwise
        """
        return match_patterns(log_entry, self.patterns)
