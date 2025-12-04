"""Unit tests for the parser module."""

from logsift.core.parser import LogParser


def test_parser_initialization():
    """Test that parser can be initialized."""
    parser = LogParser()
    assert parser is not None


# Format Detection Tests


def test_detect_format_json():
    """Test detection of JSON log format."""
    parser = LogParser()
    json_log = '{"timestamp": "2025-11-27T14:30:22Z", "level": "INFO", "message": "Test"}'
    assert parser.detect_format(json_log) == 'json'


def test_detect_format_structured():
    """Test detection of structured log format (key=value)."""
    parser = LogParser()
    structured_log = '2025-11-27T14:30:22Z level=INFO message="Starting installation"'
    assert parser.detect_format(structured_log) == 'structured'


def test_detect_format_syslog():
    """Test detection of syslog format."""
    parser = LogParser()
    syslog = '<134>Nov 27 14:30:22 hostname app[1234]: Test message'
    assert parser.detect_format(syslog) == 'syslog'


def test_detect_format_plain():
    """Test detection of plain text format (fallback)."""
    parser = LogParser()
    plain_log = '2025-11-27T14:30:22Z [INFO] Starting installation'
    assert parser.detect_format(plain_log) == 'plain'


# JSON Parsing Tests


def test_parse_json_entries():
    """Test parsing JSON log entries with explicit levels."""
    parser = LogParser()
    json_log = """\
{"timestamp": "2025-11-27T14:30:22Z", "level": "INFO", "message": "First"}
{"timestamp": "2025-11-27T14:30:23Z", "level": "ERROR", "message": "Second"}"""
    entries = parser.parse(json_log)

    assert len(entries) == 2
    assert entries[0]['level'] == 'INFO'
    assert entries[1]['level'] == 'ERROR'
    assert entries[0]['format'] == 'json'


def test_parse_json_with_extra_fields():
    """Test parsing JSON with additional fields."""
    parser = LogParser()
    json_log = '{"timestamp": "2025-11-27T14:30:22Z", "level": "INFO", "message": "Test", "user": "alice", "request_id": "123"}'
    entries = parser.parse(json_log)

    assert len(entries) == 1
    assert entries[0]['user'] == 'alice'
    assert entries[0]['request_id'] == '123'


# Structured Format Parsing Tests


def test_parse_structured_key_value():
    """Test parsing structured logs with key=value format."""
    parser = LogParser()
    structured_log = '2025-11-27T14:30:22Z level=INFO message="Starting installation" phase=1'
    entries = parser.parse(structured_log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'INFO'
    assert entries[0]['message'] == 'Starting installation'
    assert entries[0]['phase'] == '1'
    assert entries[0]['format'] == 'structured'


# Plain Text Parsing Tests


def test_parse_plain_text_preserves_message():
    """Test parsing plain text logs.

    IMPORTANT: Parser does NOT detect levels - it preserves full message.
    Level detection happens in IssueDetector via TOML patterns.
    """
    parser = LogParser()
    plain_log = """\
2025-11-27T14:30:22Z [INFO] Starting installation
2025-11-27T14:30:23Z [ERROR] Package tmux already installed
2025-11-27T14:30:24Z [WARNING] Deprecated flag used"""
    entries = parser.parse(plain_log)

    assert len(entries) == 3
    # Parser always sets level to INFO - TOML patterns will detect actual levels
    assert entries[0]['level'] == 'INFO'
    assert entries[1]['level'] == 'INFO'
    assert entries[2]['level'] == 'INFO'
    # Parser preserves full message including level markers
    assert entries[0]['message'] == '[INFO] Starting installation'
    assert entries[1]['message'] == '[ERROR] Package tmux already installed'
    assert entries[2]['message'] == '[WARNING] Deprecated flag used'


def test_parse_plain_text_with_ansi_codes():
    """Test parsing plain text with ANSI color codes.

    Parser removes ANSI codes but preserves level markers in message.
    """
    parser = LogParser()
    plain_log = '2025-11-27T14:30:22Z \x1b[31m[ERROR]\x1b[0m Failed to install'
    entries = parser.parse(plain_log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'INFO'  # Parser doesn't detect levels
    # ANSI codes removed, but level marker preserved
    assert entries[0]['message'] == '[ERROR] Failed to install'


def test_parse_mkdocs_format_messages():
    """Test parsing mkdocs-style log lines (preserves level indicators)."""
    parser = LogParser()
    log = """\
INFO    -  Cleaning site directory
WARNING -  Excluding 'archive/README.md' from the site
ERROR   -  Failed to build"""

    entries = parser.parse(log)

    assert len(entries) == 3
    # Parser sets all to INFO - TOML patterns will detect actual levels
    for entry in entries:
        assert entry['level'] == 'INFO'

    # Messages preserve the level indicators
    assert 'INFO' in entries[0]['message']
    assert 'WARNING' in entries[1]['message']
    assert 'ERROR' in entries[2]['message']


# Edge Cases


def test_parse_empty_string():
    """Test parsing empty string returns empty list."""
    parser = LogParser()
    assert parser.parse('') == []


def test_parse_malformed_json_falls_back():
    """Test that malformed JSON falls back to plain text parsing."""
    parser = LogParser()
    malformed = '{"timestamp": "2025-11-27T14:30:22Z", "level": "INFO"'  # Missing closing brace
    entries = parser.parse(malformed)

    assert len(entries) > 0
    assert entries[0]['format'] == 'plain'


def test_parse_preserves_line_numbers():
    """Test that parsed entries include original line numbers."""
    parser = LogParser()
    log_content = """\
Line 1: First entry
Line 2: Second entry
Line 3: Third entry"""
    entries = parser.parse(log_content)

    assert len(entries) == 3
    assert entries[0]['line_number'] == 1
    assert entries[1]['line_number'] == 2
    assert entries[2]['line_number'] == 3
