"""Decide which log lines are errors and warnings: a structured log's level field, else the first TOML pattern to match."""

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

            # Method 2: the first TOML pattern to match the line decides it
            message = entry.get('message', '')
            for pattern in all_patterns:
                found = re.search(pattern['regex'], message)
                if not found:
                    continue
                match pattern['severity']:
                    case 'error':
                        errors.append(self._build_issue(entry, 'error', error_id, pattern, found))
                        error_id += 1
                    case 'warning':
                        warnings.append(self._build_issue(entry, 'warning', warning_id, pattern, found))
                        warning_id += 1
                    case 'info':
                        # An info pattern claims a line it knows is benign, so no later catch-all reports it.
                        pass
                    case other:
                        raise ValueError(f'pattern {pattern["name"]} has severity {other!r}, which validate_pattern refuses')
                break

        return errors, warnings

    def _build_issue(
        self,
        entry: dict[str, Any],
        severity: str,
        issue_id: int,
        pattern: dict[str, Any] | None = None,
        match: re.Match[str] | None = None,
    ) -> dict[str, Any]:
        """Build an issue dictionary from a log entry.

        Args:
            entry: Log entry dictionary
            severity: 'error' or 'warning'
            issue_id: ID for this issue
            pattern: Optional pattern metadata if matched via TOML pattern
            match: The pattern's match, whose `code` group, where the regex names one, is the issue's code

        Returns:
            Issue dictionary with all metadata
        """
        message = entry.get('message', '')
        issue = {
            'id': issue_id,
            'severity': severity,
            'message': message,
            'line_in_log': entry.get('line_number'),
        }

        if pattern:
            issue['pattern_name'] = pattern['name']
            issue['description'] = pattern['description']
            issue['tags'] = pattern['tags']
            if 'suggestion' in pattern:
                issue['suggestion'] = pattern['suggestion']
            if 'context_lines_after' in pattern:
                issue['pattern_context_lines_after'] = pattern['context_lines_after']

        code = match.groupdict().get('code') if match else None
        if code:
            issue['code'] = code

        # Preserve additional fields from original entry
        for key in ('timestamp', 'format', 'file', 'file_line'):
            if key in entry:
                issue[key] = entry[key]

        return issue
