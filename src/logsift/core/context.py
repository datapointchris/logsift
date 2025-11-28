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
        # Validate error_index
        if error_index < 0 or error_index >= len(log_entries):
            raise IndexError(f'Error index {error_index} out of bounds for log entries of length {len(log_entries)}')

        # Calculate start and end indices for context
        start_index = max(0, error_index - self.context_lines)
        end_index = min(len(log_entries), error_index + self.context_lines + 1)

        # Extract context before and after the error
        context_before = log_entries[start_index:error_index]
        context_after = log_entries[error_index + 1 : end_index]

        return {
            'context_before': context_before,
            'context_after': context_after,
        }
