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


def test_detect_format_json_multiline():
    """Test detection of JSON format with multiple lines."""
    parser = LogParser()
    json_log = """\
{"timestamp": "2025-11-27T14:30:22Z", "level": "INFO", "message": "Test"}
{"timestamp": "2025-11-27T14:30:23Z", "level": "ERROR", "message": "Error"}"""
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


def test_parse_json_single_entry():
    """Test parsing a single JSON log entry."""
    parser = LogParser()
    json_log = '{"timestamp": "2025-11-27T14:30:22Z", "level": "INFO", "message": "Test message"}'
    entries = parser.parse(json_log)

    assert len(entries) == 1
    assert entries[0]['timestamp'] == '2025-11-27T14:30:22Z'
    assert entries[0]['level'] == 'INFO'
    assert entries[0]['message'] == 'Test message'
    assert entries[0]['format'] == 'json'


def test_parse_json_multiple_entries():
    """Test parsing multiple JSON log entries."""
    parser = LogParser()
    json_log = """\
{"timestamp": "2025-11-27T14:30:22Z", "level": "INFO", "message": "First"}
{"timestamp": "2025-11-27T14:30:23Z", "level": "ERROR", "message": "Second"}"""
    entries = parser.parse(json_log)

    assert len(entries) == 2
    assert entries[0]['level'] == 'INFO'
    assert entries[1]['level'] == 'ERROR'


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


def test_parse_structured_multiple_lines():
    """Test parsing multiple structured log lines."""
    parser = LogParser()
    structured_log = """\
2025-11-27T14:30:22Z level=INFO message="First"
2025-11-27T14:30:23Z level=ERROR message="Second" """
    entries = parser.parse(structured_log)

    assert len(entries) == 2


# Plain Text Parsing Tests


def test_parse_plain_text_with_level_markers():
    """Test parsing plain text logs with [LEVEL] markers."""
    parser = LogParser()
    plain_log = """\
2025-11-27T14:30:22Z [INFO] Starting installation
2025-11-27T14:30:23Z [ERROR] Package tmux already installed
2025-11-27T14:30:24Z [WARNING] Deprecated flag used"""
    entries = parser.parse(plain_log)

    assert len(entries) == 3
    assert entries[0]['level'] == 'INFO'
    assert entries[1]['level'] == 'ERROR'
    assert entries[2]['level'] == 'WARNING'
    assert 'tmux already installed' in entries[1]['message']


def test_parse_plain_text_no_level():
    """Test parsing plain text without explicit level markers."""
    parser = LogParser()
    plain_log = """\
2025-11-27T14:30:22Z Starting installation
2025-11-27T14:30:23Z Installation complete"""
    entries = parser.parse(plain_log)

    assert len(entries) == 2
    assert entries[0]['level'] == 'INFO'  # Default level


def test_parse_plain_text_with_ansi_codes():
    """Test parsing plain text with ANSI color codes."""
    parser = LogParser()
    plain_log = '2025-11-27T14:30:22Z \x1b[31m[ERROR]\x1b[0m Failed to install'
    entries = parser.parse(plain_log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'ERROR'
    assert 'Failed to install' in entries[0]['message']


# Edge Cases


def test_parse_empty_string():
    """Test parsing empty string returns empty list."""
    parser = LogParser()
    assert parser.parse('') == []


def test_parse_whitespace_only():
    """Test parsing whitespace-only string returns empty list."""
    parser = LogParser()
    assert parser.parse('   \n\n  \t  ') == []


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


def test_parse_handles_mixed_formats():
    """Test that parser handles logs with mixed formats gracefully."""
    parser = LogParser()
    mixed_log = """\
2025-11-27T14:30:22Z [INFO] Plain text entry
{"timestamp": "2025-11-27T14:30:23Z", "level": "ERROR", "message": "JSON entry"}
2025-11-27T14:30:24Z level=WARNING message="Structured entry" """
    entries = parser.parse(mixed_log)

    # Should parse all entries, detecting format per line
    assert len(entries) == 3


# Universal Log Level Detection Tests


def test_parse_level_colon_format():
    """Test parsing LEVEL: format."""
    parser = LogParser()
    log = 'WARNING: This is a warning message'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'WARNING'
    assert entries[0]['message'] == 'This is a warning message'


def test_parse_level_dash_format():
    """Test parsing LEVEL - format (mkdocs style)."""
    parser = LogParser()
    log = 'WARNING -  Excluding "archive/README.md" from the site'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'WARNING'
    assert entries[0]['message'] == 'Excluding "archive/README.md" from the site'


def test_parse_level_pipe_format():
    """Test parsing LEVEL | format."""
    parser = LogParser()
    log = 'ERROR | Database connection failed'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'ERROR'
    assert entries[0]['message'] == 'Database connection failed'


def test_parse_level_bracket_format():
    """Test parsing [LEVEL] format."""
    parser = LogParser()
    log = '[WARNING] Deprecated API usage detected'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'WARNING'
    assert entries[0]['message'] == 'Deprecated API usage detected'


def test_parse_level_warn_variant():
    """Test parsing WARN as WARNING."""
    parser = LogParser()
    log = 'WARN - Short form warning'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'WARN'
    assert entries[0]['message'] == 'Short form warning'


def test_parse_level_with_extra_spaces():
    """Test parsing level with extra spaces."""
    parser = LogParser()
    log = '  WARNING  :  Message with spaces'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'WARNING'
    assert entries[0]['message'] == 'Message with spaces'


def test_parse_level_case_insensitive():
    """Test parsing level is case insensitive."""
    parser = LogParser()
    log1 = 'warning: lowercase'
    log2 = 'Warning: titlecase'
    log3 = 'WARNING: uppercase'

    entries1 = parser.parse(log1)
    entries2 = parser.parse(log2)
    entries3 = parser.parse(log3)

    assert entries1[0]['level'] == 'WARNING'
    assert entries2[0]['level'] == 'WARNING'
    assert entries3[0]['level'] == 'WARNING'


def test_parse_multiple_mkdocs_warnings():
    """Test parsing multiple mkdocs-style warnings."""
    parser = LogParser()
    log = """\
INFO    -  Cleaning site directory
INFO    -  Building documentation to directory: /path/to/site
WARNING -  Excluding 'archive/README.md' from the site because it conflicts
WARNING -  A reference to 'material/cog' is not found
ERROR   -  Failed to build"""

    entries = parser.parse(log)

    assert len(entries) == 5
    assert entries[0]['level'] == 'INFO'
    assert entries[1]['level'] == 'INFO'
    assert entries[2]['level'] == 'WARNING'
    assert entries[3]['level'] == 'WARNING'
    assert entries[4]['level'] == 'ERROR'


def test_parse_debug_level():
    """Test parsing DEBUG level."""
    parser = LogParser()
    log = 'DEBUG - Verbose debugging information'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'DEBUG'


def test_parse_fatal_level():
    """Test parsing FATAL level."""
    parser = LogParser()
    log = 'FATAL: Critical system failure'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'FATAL'


def test_parse_info_level_dash():
    """Test parsing INFO level with dash separator."""
    parser = LogParser()
    log = 'INFO - Application started'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'INFO'
    assert entries[0]['message'] == 'Application started'


def test_parse_level_not_in_middle_of_line():
    """Test that level keyword in middle of line doesn't match."""
    parser = LogParser()
    log = 'This line contains WARNING in the middle'
    entries = parser.parse(log)

    assert len(entries) == 1
    assert entries[0]['level'] == 'INFO'  # Should default to INFO
    assert 'WARNING' in entries[0]['message']  # WARNING should be in message
