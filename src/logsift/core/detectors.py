"""Detect errors, warnings, and file references from logs.

Provides detection strategies for identifying important information in log files.
"""

import re
from typing import Any


class IssueDetector:
    """Detect errors and warnings from log entries using TOML patterns.

    Handles two types of detection:
    1. Explicit levels from structured formats (JSON/structured logs with level fields)
    2. Pattern-based detection for plain text logs (using TOML patterns)
    """

    def detect_issues(
        self, log_entries: list[dict[str, Any]], patterns: dict[str, list[dict[str, Any]]]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Detect errors and warnings from parsed log data.

        Uses two detection methods in a single pass:
        1. Explicit levels from structured formats (JSON, structured logs with level= field)
        2. TOML pattern matching for plain text logs

        IMPORTANT: For plain text, parser does NOT detect levels - patterns do.
        For JSON/structured, the level field is explicit data in the log format.

        Args:
            log_entries: List of normalized log entry dictionaries
            patterns: Dictionary of patterns organized by category (from TOML files)

        Returns:
            Tuple of (errors, warnings) lists with metadata
        """
        errors = []
        warnings = []
        error_id = 1
        warning_id = 1

        # Flatten patterns for easier iteration
        all_patterns = []
        for category_patterns in patterns.values():
            all_patterns.extend(category_patterns)

        # Single pass through all log entries
        for entry in log_entries:
            format_type = entry.get('format', 'plain')
            level = entry.get('level', '').upper()
            line_number = entry.get('line_number')

            if line_number is None:
                continue

            # Method 1: Explicit levels from JSON/structured formats
            if format_type in ('json', 'structured'):
                if level == 'ERROR':
                    error = self._build_issue(entry, 'error', error_id)
                    errors.append(error)
                    error_id += 1
                    continue  # Don't try pattern matching

                if level in ('WARNING', 'WARN'):
                    warning = self._build_issue(entry, 'warning', warning_id)
                    warnings.append(warning)
                    warning_id += 1
                    continue  # Don't try pattern matching

            # Method 2: Pattern-based detection (for plain text or additional detection)
            message = entry.get('message', '')
            for pattern in all_patterns:
                regex = pattern.get('regex', '')
                if not regex:
                    continue

                try:
                    if re.search(regex, message):
                        severity = pattern.get('severity', 'error')

                        # Build issue with pattern metadata
                        if severity == 'error':
                            issue = self._build_issue(entry, 'error', error_id, pattern)
                            errors.append(issue)
                            error_id += 1
                        elif severity == 'warning':
                            issue = self._build_issue(entry, 'warning', warning_id, pattern)
                            warnings.append(issue)
                            warning_id += 1

                        break  # Only match first pattern per line
                except re.error:
                    # Skip invalid regex patterns
                    continue

        return errors, warnings

    def _build_issue(
        self,
        entry: dict[str, Any],
        severity: str,
        issue_id: int,
        pattern: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build an issue dictionary from a log entry.

        Args:
            entry: Log entry dictionary
            severity: 'error' or 'warning'
            issue_id: ID for this issue
            pattern: Optional pattern metadata if matched via TOML pattern

        Returns:
            Issue dictionary with all metadata
        """
        issue = {
            'id': issue_id,
            'severity': severity,
            'message': entry.get('message', ''),
            'line_in_log': entry.get('line_number'),
        }

        # Add pattern metadata if available
        if pattern:
            issue['pattern_name'] = pattern.get('name', 'unknown')
            issue['description'] = pattern.get('description', '')
            issue['tags'] = pattern.get('tags', [])

            # Add suggestion if available
            if 'suggestion' in pattern:
                issue['suggestion'] = pattern['suggestion']

            # Add context_lines_after if specified (for multi-line error extraction)
            if 'context_lines_after' in pattern:
                issue['pattern_context_lines_after'] = pattern['context_lines_after']

        # Preserve additional fields from original entry
        for key in ('timestamp', 'format', 'file', 'file_line'):
            if key in entry:
                issue[key] = entry[key]

        return issue


class FileReferenceDetector:
    """Detect file:line references from log entries."""

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
    WINDOWS_PATH_PATTERN = re.compile(r'([A-Za-z]:[\\/][\w\\/.-]+\.\w+):(\d+)(?::\d+)?')

    def detect_references(self, text: str) -> list[tuple[str, int]]:
        """Detect file:line references from text.

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
