"""Extract errors, warnings, and file references from logs.

Provides various extraction strategies for identifying important information in log files.
"""

import re
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
        errors = []
        error_id = 1

        for entry in log_entries:
            level = entry.get('level', '').upper()
            if level == 'ERROR':
                error = {
                    'id': error_id,
                    'severity': 'error',
                    'message': entry.get('message', ''),
                    'line_in_log': entry.get('line_number'),
                }

                # Preserve additional fields from original entry
                for key in ('timestamp', 'format', 'file', 'file_line'):
                    if key in entry:
                        error[key] = entry[key]

                errors.append(error)
                error_id += 1

        return errors


class WarningExtractor:
    """Extract warning messages from log entries."""

    def extract_warnings(self, log_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract warning entries from parsed log data.

        Args:
            log_entries: List of normalized log entry dictionaries

        Returns:
            List of warning dictionaries with metadata
        """
        warnings = []
        warning_id = 1

        for entry in log_entries:
            level = entry.get('level', '').upper()
            if level in ('WARNING', 'WARN'):
                warning = {
                    'id': warning_id,
                    'severity': 'warning',
                    'message': entry.get('message', ''),
                    'line_in_log': entry.get('line_number'),
                }

                # Preserve additional fields from original entry
                for key in ('timestamp', 'format', 'file', 'file_line'):
                    if key in entry:
                        warning[key] = entry[key]

                warnings.append(warning)
                warning_id += 1

        return warnings


class FileReferenceExtractor:
    """Extract file:line references from log entries."""

    # Regex pattern to match file:line references (standard format)
    # Matches: file.py:42, /path/to/file.js:123, ./relative/path.py:67
    FILE_LINE_PATTERN = re.compile(
        r'(?:'  # Start non-capturing group for path prefix
        r'(?:[./]|/)?'  # Optional path separator or relative marker
        r'[\w/.-]*?'  # Path components (non-greedy)
        r')'  # End path prefix group
        r'([\w/.-]+\.\w+)'  # Filename with extension (capturing group 1)
        r':'  # Colon separator
        r'(\d+)'  # Line number (capturing group 2)
        r'(?::\d+)?'  # Optional column number (non-capturing)
    )

    # Regex pattern for Python stack trace format
    # Matches: File "/app/main.py", line 42, in function_name
    STACK_TRACE_PATTERN = re.compile(r'File\s+"([^"]+)",\s+line\s+(\d+)', re.IGNORECASE)

    # Regex pattern for Windows paths
    # Matches: C:\Users\dev\project\src\main.py:100
    WINDOWS_PATH_PATTERN = re.compile(r'([A-Za-z]:[\\\/][\w\\\/.-]+\.\w+):(\d+)(?::\d+)?')

    def extract_references(self, text: str) -> list[tuple[str, int]]:
        """Extract file:line references from text.

        Args:
            text: Text to search for file references

        Returns:
            List of (filename, line_number) tuples
        """
        if not text:
            return []

        references = []
        matched_ranges: list[tuple[int, int]] = []  # Track (start, end) positions of matched text

        # Helper function to check if a match overlaps with already matched ranges
        def is_overlapping(start: int, end: int) -> bool:
            return any(not (end <= matched_start or start >= matched_end) for matched_start, matched_end in matched_ranges)

        # Try Windows path pattern first (most specific)
        for match in self.WINDOWS_PATH_PATTERN.finditer(text):
            start, end = match.span()
            if not is_overlapping(start, end):
                file_path = match.group(1)
                line_number = int(match.group(2))
                references.append((file_path, line_number))
                matched_ranges.append((start, end))

        # Try stack trace pattern (Python format)
        for match in self.STACK_TRACE_PATTERN.finditer(text):
            start, end = match.span()
            if not is_overlapping(start, end):
                file_path = match.group(1)
                line_number = int(match.group(2))
                references.append((file_path, line_number))
                matched_ranges.append((start, end))

        # Try standard file:line pattern (Unix/Linux format)
        for match in self.FILE_LINE_PATTERN.finditer(text):
            start, end = match.span()
            if not is_overlapping(start, end):
                full_match = match.group(0)
                # Split on the last colon to separate file path from line number
                parts = full_match.rsplit(':', 2)  # Split on last 2 colons (handles column numbers)
                if len(parts) >= 2:
                    file_path = parts[0]
                    try:
                        line_number = int(parts[1])
                        references.append((file_path, line_number))
                        matched_ranges.append((start, end))
                    except ValueError:
                        # Skip if line number is not a valid integer
                        continue

        return references
