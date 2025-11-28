"""Context extraction around errors and warnings.

Extracts surrounding lines (±N lines) around errors to provide context.
"""

from typing import Any


class ContextExtractor:
    """Extract context lines around errors and warnings."""

    def __init__(self, context_lines: int = 2) -> None:
        """Initialize the context extractor.

        Args:
            context_lines: Number of lines to extract before and after
        """
        self.context_lines = context_lines

    def extract_context(
        self,
        log_entries: list[dict[str, Any]],
        error_index: int,
    ) -> dict[str, Any]:
        """Extract context around an error entry.

        Args:
            log_entries: List of all log entries
            error_index: Index of the error in log_entries

        Returns:
            Dictionary with before, error, and after context
        """
        raise NotImplementedError('Context extraction not yet implemented')
