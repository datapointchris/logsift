"""Extract errors, warnings, and file references from logs.

Provides various extraction strategies for identifying important information in log files.
"""

import re
from typing import Any


class ErrorExtractor:
    """Extract error messages from log entries."""

    # Shell and system error patterns that indicate failures
    # These are critical errors that often don't have explicit ERROR log levels
    SHELL_ERROR_PATTERNS = [
        # Command execution errors
        (r': command not found\s*$', 'Command not found'),
        (r': not found\s*$', 'Command not found'),
        (r'bash: .+: command not found', 'Bash command not found'),
        (r'sh: .+: command not found', 'Shell command not found'),
        (r'zsh:\d+: .+: command not found', 'Zsh command not found'),
        (r'zsh:\d+: .+: not found', 'Zsh command not found'),
        # File system errors
        (r': No such file or directory', 'File or directory not found'),
        (r': cannot find .+', 'Cannot find file'),
        (r': Permission denied', 'Permission denied'),
        (r'cannot access .+: No such file or directory', 'File not found'),
        # Compilation/build errors
        (r'fatal error:', 'Fatal error'),
        (r'compilation terminated', 'Compilation failed'),
        (r'collect2: error:', 'Linker error'),
        (r'cannot find -l\w+', 'Missing library'),
        (r'undefined reference to', 'Undefined reference'),
        # Runtime errors
        (r'Segmentation fault', 'Segmentation fault'),
        (r'core dumped', 'Core dumped'),
        (r'Aborted', 'Process aborted'),
        (r'Killed', 'Process killed'),
        # Package manager errors
        (r'E: Unable to locate package', 'Package not found'),
        (r'Error: Package .+ not found', 'Package not found'),
        (r'npm ERR!', 'NPM error'),
        (r'error: failed to .+', 'Operation failed'),
    ]

    def extract_errors(self, log_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extract error entries from parsed log data.

        Extracts errors from two sources:
        1. Explicit ERROR level log entries
        2. Shell/system error patterns (command not found, permission denied, etc.)

        Args:
            log_entries: List of normalized log entry dictionaries

        Returns:
            List of error dictionaries with metadata
        """
        errors = []
        error_id = 1
        seen_lines: set[int] = set()  # Track processed lines to avoid duplicates

        # First pass: Extract explicit ERROR level entries
        for entry in log_entries:
            level = entry.get('level', '').upper()
            line_number = entry.get('line_number')

            if level == 'ERROR' and line_number is not None and line_number not in seen_lines:
                error = {
                    'id': error_id,
                    'severity': 'error',
                    'message': entry.get('message', ''),
                    'line_in_log': line_number,
                }

                # Preserve additional fields from original entry
                for key in ('timestamp', 'format', 'file', 'file_line'):
                    if key in entry:
                        error[key] = entry[key]

                errors.append(error)
                seen_lines.add(line_number)
                error_id += 1

        # Second pass: Pattern-based error detection for shell/system errors
        for entry in log_entries:
            message = entry.get('message', '')
            line_number = entry.get('line_number')

            # Skip if we already extracted this line as an error
            if line_number is None or line_number in seen_lines:
                continue

            # Check against shell error patterns
            for pattern, description in self.SHELL_ERROR_PATTERNS:
                if re.search(pattern, message, re.IGNORECASE):
                    error = {
                        'id': error_id,
                        'severity': 'error',
                        'message': message,
                        'line_in_log': line_number,
                        'pattern_name': 'shell_error',
                        'description': description,
                        'tags': ['shell', 'system_error'],
                    }

                    # Preserve additional fields from original entry
                    for key in ('timestamp', 'format', 'file', 'file_line'):
                        if key in entry:
                            error[key] = entry[key]

                    errors.append(error)
                    seen_lines.add(line_number)
                    error_id += 1
                    break  # Only match first pattern per line

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
