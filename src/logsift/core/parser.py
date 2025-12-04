"""Log parsing and format detection.

Handles auto-detection of log formats (JSON, structured, plain text) and normalization to internal representation.
"""

import json
import re
from typing import Any


class LogParser:
    """Parser for detecting and parsing various log formats."""

    # Regex patterns for log parsing
    ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')
    TIMESTAMP_ISO = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})?')
    LEVEL_MARKER = re.compile(r'\[(DEBUG|INFO|WARN|WARNING|ERROR|FATAL)\]', re.IGNORECASE)
    LEVEL_COLON = re.compile(r'(DEBUG|INFO|WARN|WARNING|ERROR|FATAL):', re.IGNORECASE)
    KEY_VALUE_PAIR = re.compile(r'(\w+)=("(?:[^"\\]|\\.)*"|\S+)')
    SYSLOG_PATTERN = re.compile(r'^<\d+>')

    def __init__(self) -> None:
        """Initialize the log parser."""
        pass

    def parse(self, log_content: str) -> list[dict[str, Any]]:
        """Parse log content and return normalized entries.

        Args:
            log_content: Raw log content to parse

        Returns:
            List of normalized log entry dictionaries
        """
        if not log_content or not log_content.strip():
            return []

        lines = log_content.splitlines()
        entries = []
        for line_num, line in enumerate(lines, start=1):
            if not line.strip():
                continue

            # Detect format per line for mixed format support
            line_format = self._detect_line_format(line)

            if line_format == 'json':
                entry = self._parse_json_line(line, line_num)
            elif line_format == 'structured':
                entry = self._parse_structured_line(line, line_num)
            elif line_format == 'syslog':
                entry = self._parse_syslog_line(line, line_num)
            else:
                entry = self._parse_plain_line(line, line_num)

            if entry:
                entries.append(entry)

        return entries

    def detect_format(self, log_content: str) -> str:
        """Detect the format of the log content.

        Args:
            log_content: Raw log content to analyze

        Returns:
            Detected format: 'json', 'structured', 'syslog', or 'plain'
        """
        if not log_content or not log_content.strip():
            return 'plain'

        # Get first non-empty line for format detection
        first_line = next((line for line in log_content.splitlines() if line.strip()), '')

        return self._detect_line_format(first_line)

    def _detect_line_format(self, line: str) -> str:
        """Detect format of a single line.

        Args:
            line: Single log line to analyze

        Returns:
            Detected format: 'json', 'structured', 'syslog', or 'plain'
        """
        line = line.strip()

        # Try JSON
        if line.startswith('{') and line.endswith('}'):
            try:
                json.loads(line)
                return 'json'
            except (json.JSONDecodeError, ValueError):
                pass

        # Try syslog
        if self.SYSLOG_PATTERN.match(line):
            return 'syslog'

        # Try structured (key=value format)
        # Look for at least 2 key=value pairs
        kv_matches = self.KEY_VALUE_PAIR.findall(line)
        if len(kv_matches) >= 2:
            return 'structured'

        # Default to plain text
        return 'plain'

    def _parse_json_line(self, line: str, line_num: int) -> dict[str, Any] | None:
        """Parse a JSON log line.

        Args:
            line: JSON log line
            line_num: Original line number

        Returns:
            Parsed entry dictionary or None if parsing fails
        """
        try:
            entry = json.loads(line)
            entry['format'] = 'json'
            entry['line_number'] = line_num

            # Ensure standard fields exist
            if 'level' not in entry:
                entry['level'] = 'INFO'
            if 'message' not in entry:
                entry['message'] = str(entry)

            return entry
        except (json.JSONDecodeError, ValueError):
            return None

    def _parse_structured_line(self, line: str, line_num: int) -> dict[str, Any]:
        """Parse a structured log line (key=value format).

        Args:
            line: Structured log line
            line_num: Original line number

        Returns:
            Parsed entry dictionary
        """
        entry: dict[str, Any] = {
            'format': 'structured',
            'line_number': line_num,
            'level': 'INFO',
            'message': '',
        }

        # Extract timestamp if present at start
        timestamp_match = self.TIMESTAMP_ISO.match(line)
        if timestamp_match:
            entry['timestamp'] = timestamp_match.group(0)

        # Extract key=value pairs
        for key, value in self.KEY_VALUE_PAIR.findall(line):
            # Remove quotes from quoted values
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            entry[key] = value

        # Normalize level field
        if 'level' in entry:
            entry['level'] = entry['level'].upper()

        return entry

    def _parse_syslog_line(self, line: str, line_num: int) -> dict[str, Any]:
        """Parse a syslog format line.

        Args:
            line: Syslog format line
            line_num: Original line number

        Returns:
            Parsed entry dictionary
        """
        entry: dict[str, Any] = {
            'format': 'syslog',
            'line_number': line_num,
            'level': 'INFO',
        }

        # Extract priority
        priority_match = re.match(r'^<(\d+)>', line)
        if priority_match:
            priority = int(priority_match.group(1))
            entry['priority'] = priority
            line = line[priority_match.end() :]

        # Extract remaining parts (simplified syslog parsing)
        parts = line.strip().split(':', 1)
        if len(parts) == 2:
            entry['message'] = parts[1].strip()
        else:
            entry['message'] = line.strip()

        return entry

    def _parse_plain_line(self, line: str, line_num: int) -> dict[str, Any]:
        """Parse a plain text log line.

        Args:
            line: Plain text log line
            line_num: Original line number

        Returns:
            Parsed entry dictionary
        """
        # Remove ANSI color codes
        clean_line = self.ANSI_ESCAPE.sub('', line)

        entry: dict[str, Any] = {
            'format': 'plain',
            'line_number': line_num,
            'level': 'INFO',
            'message': clean_line,
        }

        # Extract timestamp
        timestamp_match = self.TIMESTAMP_ISO.match(clean_line)
        if timestamp_match:
            entry['timestamp'] = timestamp_match.group(0)
            clean_line = clean_line[timestamp_match.end() :].strip()

        # Extract level - match level word at start of line with any separator
        # Matches: WARNING:, [WARNING], WARNING -, WARNING |, [ERROR], etc.
        # Note: Put WARNING before WARN to match the longer string first
        level_match = re.match(
            r'^\s*\[?\s*(DEBUG|INFO|WARNING|WARN|ERROR|FATAL)\s*\]?\s*[:\-\|\s]+',
            clean_line,
            re.IGNORECASE,
        )
        if level_match and level_match.group(1):
            entry['level'] = level_match.group(1).upper()
            # Remove level prefix from message
            clean_line = clean_line[level_match.end() :].strip()

        entry['message'] = clean_line.strip()

        return entry
