"""Extract errors, warnings, and file references from logs.

Provides various extraction strategies for identifying important information in log files.
"""

from typing import Any


class ErrorExtractor:
    """Extract error messages from log entries."""

    def extract_errors(self, log_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract error entries from parsed log data.

        Args:
            log_entries: List of normalized log entry dictionaries

        Returns:
            List of error dictionaries with metadata
        """
        raise NotImplementedError('Error extraction not yet implemented')


class WarningExtractor:
    """Extract warning messages from log entries."""

    def extract_warnings(self, log_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract warning entries from parsed log data.

        Args:
            log_entries: List of normalized log entry dictionaries

        Returns:
            List of warning dictionaries with metadata
        """
        raise NotImplementedError('Warning extraction not yet implemented')


class FileReferenceExtractor:
    """Extract file:line references from log entries."""

    def extract_references(self, text: str) -> list[tuple[str, int]]:
        """Extract file:line references from text.

        Args:
            text: Text to search for file references

        Returns:
            List of (filename, line_number) tuples
        """
        raise NotImplementedError('File reference extraction not yet implemented')
