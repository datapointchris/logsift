"""Unit tests for the detector system."""

from logsift.core.detectors import FileReferenceDetector
from logsift.core.detectors import IssueDetector
from logsift.patterns.loader import PatternLoader

# IssueDetector Tests


def test_issue_detector_initialization():
    """Test that issue detector can be initialized."""
    detector = IssueDetector()
    assert detector is not None


def test_extract_errors_from_log_entries():
    """Test detecting errors from parsed log entries using TOML patterns.

    IMPORTANT: Detector relies on TOML patterns, not parser-detected levels.
    Messages must contain level indicators that patterns can match.
    """
    log_entries = [
        {'level': 'INFO', 'message': 'Starting process', 'line_number': 1, 'format': 'plain'},
        {'level': 'INFO', 'message': 'ERROR: Failed to connect', 'line_number': 2, 'format': 'plain'},
        {'level': 'INFO', 'message': '[ERROR] Timeout occurred', 'line_number': 3, 'format': 'plain'},
    ]

    # Load actual patterns that can detect ERROR indicators
    pattern_loader = PatternLoader()
    patterns = pattern_loader.load_builtin_patterns()

    detector = IssueDetector()
    errors, warnings = detector.detect_issues(log_entries, patterns)

    assert len(errors) == 2
    assert len(warnings) == 0
    assert errors[0]['severity'] == 'error'
    assert 'Failed to connect' in errors[0]['message']
    assert errors[0]['line_in_log'] == 2
    assert 'Timeout occurred' in errors[1]['message']
    assert errors[1]['line_in_log'] == 3


def test_extract_warnings_from_log_entries():
    """Test extracting warnings from parsed log entries using TOML patterns."""
    log_entries = [
        {'level': 'INFO', 'message': 'Starting process', 'line_number': 1, 'format': 'plain'},
        {'level': 'INFO', 'message': 'WARNING: Deprecated API', 'line_number': 2, 'format': 'plain'},
        {'level': 'INFO', 'message': 'WARN - Low memory', 'line_number': 3, 'format': 'plain'},
    ]

    # Load actual patterns
    pattern_loader = PatternLoader()
    patterns = pattern_loader.load_builtin_patterns()

    detector = IssueDetector()
    errors, warnings = detector.detect_issues(log_entries, patterns)

    assert len(errors) == 0
    assert len(warnings) == 2
    assert warnings[0]['severity'] == 'warning'
    assert 'Deprecated API' in warnings[0]['message']
    assert 'Low memory' in warnings[1]['message']


def test_extract_errors_case_insensitive():
    """Test that error extraction is case insensitive (via TOML patterns)."""
    log_entries = [
        {'level': 'INFO', 'message': 'error: Lower case error', 'line_number': 1, 'format': 'plain'},
        {'level': 'INFO', 'message': 'ERROR: Upper case error', 'line_number': 2, 'format': 'plain'},
        {'level': 'INFO', 'message': 'Error: Mixed case error', 'line_number': 3, 'format': 'plain'},
    ]

    # Load patterns (common.toml has case-insensitive error patterns)
    pattern_loader = PatternLoader()
    patterns = pattern_loader.load_builtin_patterns()

    detector = IssueDetector()
    errors, warnings = detector.detect_issues(log_entries, patterns)

    assert len(errors) == 3


def test_extract_from_empty_list():
    """Test extracting from empty log list."""
    detector = IssueDetector()
    patterns = {}
    errors, warnings = detector.detect_issues([], patterns)

    assert errors == []
    assert warnings == []


def test_extract_when_none_exist():
    """Test extracting when no errors or warnings exist."""
    log_entries = [
        {'level': 'INFO', 'message': 'All good', 'line_number': 1},
        {'level': 'DEBUG', 'message': 'Debug info', 'line_number': 2},
    ]
    detector = IssueDetector()
    patterns = {}
    errors, warnings = detector.detect_issues(log_entries, patterns)

    assert errors == []
    assert warnings == []


def test_extract_assigns_ids():
    """Test that issues are assigned sequential IDs."""
    log_entries = [
        {'level': 'INFO', 'message': 'ERROR: First error', 'line_number': 1, 'format': 'plain'},
        {'level': 'INFO', 'message': 'WARNING: First warning', 'line_number': 2, 'format': 'plain'},
        {'level': 'INFO', 'message': '[ERROR] Second error', 'line_number': 3, 'format': 'plain'},
        {'level': 'INFO', 'message': '[WARNING] Second warning', 'line_number': 4, 'format': 'plain'},
    ]

    # Load patterns
    pattern_loader = PatternLoader()
    patterns = pattern_loader.load_builtin_patterns()

    detector = IssueDetector()
    errors, warnings = detector.detect_issues(log_entries, patterns)

    assert errors[0]['id'] == 1
    assert errors[1]['id'] == 2
    assert warnings[0]['id'] == 1
    assert warnings[1]['id'] == 2


def test_extract_preserves_all_fields():
    """Test that extraction preserves all fields from log entry."""
    log_entries = [
        {
            'level': 'INFO',
            'message': 'ERROR: Connection failed',
            'line_number': 42,
            'timestamp': '2025-11-28T10:30:00Z',
            'format': 'json',
        },
    ]

    # Load patterns
    pattern_loader = PatternLoader()
    patterns = pattern_loader.load_builtin_patterns()

    detector = IssueDetector()
    errors, warnings = detector.detect_issues(log_entries, patterns)

    assert 'Connection failed' in errors[0]['message']
    assert errors[0]['line_in_log'] == 42
    assert errors[0]['timestamp'] == '2025-11-28T10:30:00Z'


def test_extract_with_toml_patterns():
    """Test that TOML patterns are used for detection."""
    log_entries = [
        {'level': 'INFO', 'message': 'bash: unzip: command not found', 'line_number': 1, 'format': 'plain'},
        {'level': 'INFO', 'message': '✗ test FAILED: assertion failed', 'line_number': 2, 'format': 'plain'},
    ]

    # Load actual patterns from TOML files
    pattern_loader = PatternLoader()
    patterns = pattern_loader.load_builtin_patterns()

    detector = IssueDetector()
    errors, warnings = detector.detect_issues(log_entries, patterns)

    # Should detect shell error and test failure
    assert len(errors) >= 2

    # Find the bash command not found error
    bash_error = next((e for e in errors if 'bash: unzip' in e['message']), None)
    assert bash_error is not None
    assert bash_error['severity'] == 'error'
    assert 'pattern_name' in bash_error
    assert 'description' in bash_error
    assert 'tags' in bash_error

    # Find the test failure
    test_error = next((e for e in errors if '✗ test FAILED' in e['message']), None)
    assert test_error is not None


def test_extract_no_duplicates():
    """Test that log entries matching multiple patterns only appear once."""
    log_entries = [
        {'level': 'INFO', 'message': 'ERROR: fatal error: file not found', 'line_number': 1, 'format': 'plain'},
    ]

    # Load patterns - this line matches both level_error_any_format and generic_error
    pattern_loader = PatternLoader()
    patterns = pattern_loader.load_builtin_patterns()

    detector = IssueDetector()
    errors, warnings = detector.detect_issues(log_entries, patterns)

    # Should only appear once (first matching pattern wins, line marked as seen)
    assert len(errors) == 1
    assert errors[0]['line_in_log'] == 1


# FileReferenceDetector Tests


def test_file_reference_extractor_initialization():
    """Test that file reference detector can be initialized."""
    detector = FileReferenceDetector()
    assert detector is not None


def test_extract_file_references_unix_format():
    """Test extracting file:line references in Unix format."""
    detector = FileReferenceDetector()
    text = 'Error in src/main.py:42 and lib/utils.js:100'
    refs = detector.detect_references(text)

    assert len(refs) == 2
    assert refs[0] == ('src/main.py', 42)
    assert refs[1] == ('lib/utils.js', 100)


def test_extract_file_references_python_format():
    """Test extracting file references in Python stack trace format."""
    detector = FileReferenceDetector()
    text = 'File "/app/main.py", line 42, in function_name'
    refs = detector.detect_references(text)

    assert len(refs) == 1
    assert refs[0] == ('/app/main.py', 42)


def test_extract_file_references_with_column_numbers():
    """Test extracting file references with column numbers."""
    detector = FileReferenceDetector()
    text = 'Error at src/file.py:42:10'
    refs = detector.detect_references(text)

    assert len(refs) == 1
    assert refs[0] == ('src/file.py', 42)  # Column number is ignored


def test_extract_file_references_from_empty_string():
    """Test extracting file references from empty string."""
    detector = FileReferenceDetector()
    refs = detector.detect_references('')

    assert refs == []


def test_extract_file_references_when_none_exist():
    """Test extracting file references when none exist in text."""
    detector = FileReferenceDetector()
    text = 'This is just a normal message with no file references'
    refs = detector.detect_references(text)

    assert refs == []
