"""Unit tests for the extractor system."""

from logsift.core.extractors import FileReferenceExtractor
from logsift.core.extractors import IssueExtractor
from logsift.patterns.loader import PatternLoader

# IssueExtractor Tests


def test_issue_extractor_initialization():
    """Test that issue extractor can be initialized."""
    extractor = IssueExtractor()
    assert extractor is not None


def test_extract_errors_from_log_entries():
    """Test extracting errors from parsed log entries."""
    log_entries = [
        {'level': 'INFO', 'message': 'Starting process', 'line_number': 1},
        {'level': 'ERROR', 'message': 'Failed to connect', 'line_number': 2},
        {'level': 'ERROR', 'message': 'Timeout occurred', 'line_number': 3},
    ]
    extractor = IssueExtractor()
    patterns = {}  # Empty patterns for basic level-based extraction
    errors, warnings = extractor.extract_issues(log_entries, patterns)

    assert len(errors) == 2
    assert len(warnings) == 0
    assert errors[0]['severity'] == 'error'
    assert errors[0]['message'] == 'Failed to connect'
    assert errors[0]['line_in_log'] == 2
    assert errors[1]['message'] == 'Timeout occurred'
    assert errors[1]['line_in_log'] == 3


def test_extract_warnings_from_log_entries():
    """Test extracting warnings from parsed log entries."""
    log_entries = [
        {'level': 'INFO', 'message': 'Starting process', 'line_number': 1},
        {'level': 'WARNING', 'message': 'Deprecated API', 'line_number': 2},
        {'level': 'WARN', 'message': 'Low memory', 'line_number': 3},
    ]
    extractor = IssueExtractor()
    patterns = {}
    errors, warnings = extractor.extract_issues(log_entries, patterns)

    assert len(errors) == 0
    assert len(warnings) == 2
    assert warnings[0]['severity'] == 'warning'
    assert warnings[0]['message'] == 'Deprecated API'
    assert warnings[1]['message'] == 'Low memory'


def test_extract_errors_case_insensitive():
    """Test that error extraction is case insensitive."""
    log_entries = [
        {'level': 'error', 'message': 'Lower case error', 'line_number': 1},
        {'level': 'ERROR', 'message': 'Upper case error', 'line_number': 2},
        {'level': 'Error', 'message': 'Mixed case error', 'line_number': 3},
    ]
    extractor = IssueExtractor()
    patterns = {}
    errors, warnings = extractor.extract_issues(log_entries, patterns)

    assert len(errors) == 3


def test_extract_from_empty_list():
    """Test extracting from empty log list."""
    extractor = IssueExtractor()
    patterns = {}
    errors, warnings = extractor.extract_issues([], patterns)

    assert errors == []
    assert warnings == []


def test_extract_when_none_exist():
    """Test extracting when no errors or warnings exist."""
    log_entries = [
        {'level': 'INFO', 'message': 'All good', 'line_number': 1},
        {'level': 'DEBUG', 'message': 'Debug info', 'line_number': 2},
    ]
    extractor = IssueExtractor()
    patterns = {}
    errors, warnings = extractor.extract_issues(log_entries, patterns)

    assert errors == []
    assert warnings == []


def test_extract_assigns_ids():
    """Test that issues are assigned sequential IDs."""
    log_entries = [
        {'level': 'ERROR', 'message': 'First error', 'line_number': 1},
        {'level': 'WARNING', 'message': 'First warning', 'line_number': 2},
        {'level': 'ERROR', 'message': 'Second error', 'line_number': 3},
        {'level': 'WARNING', 'message': 'Second warning', 'line_number': 4},
    ]
    extractor = IssueExtractor()
    patterns = {}
    errors, warnings = extractor.extract_issues(log_entries, patterns)

    assert errors[0]['id'] == 1
    assert errors[1]['id'] == 2
    assert warnings[0]['id'] == 1
    assert warnings[1]['id'] == 2


def test_extract_preserves_all_fields():
    """Test that extraction preserves all fields from log entry."""
    log_entries = [
        {
            'level': 'ERROR',
            'message': 'Connection failed',
            'line_number': 42,
            'timestamp': '2025-11-28T10:30:00Z',
            'format': 'json',
        },
    ]
    extractor = IssueExtractor()
    patterns = {}
    errors, warnings = extractor.extract_issues(log_entries, patterns)

    assert errors[0]['message'] == 'Connection failed'
    assert errors[0]['line_in_log'] == 42
    assert errors[0]['timestamp'] == '2025-11-28T10:30:00Z'


def test_extract_with_toml_patterns():
    """Test that TOML patterns are used for detection."""
    log_entries = [
        {'level': 'INFO', 'message': 'bash: unzip: command not found', 'line_number': 1},
        {'level': 'INFO', 'message': '✗ test FAILED: assertion failed', 'line_number': 2},
    ]

    # Load actual patterns from TOML files
    pattern_loader = PatternLoader()
    patterns = pattern_loader.load_builtin_patterns()

    extractor = IssueExtractor()
    errors, warnings = extractor.extract_issues(log_entries, patterns)

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
    """Test that ERROR level entries aren't duplicated when they also match patterns."""
    log_entries = [
        {'level': 'ERROR', 'message': 'fatal error: file not found', 'line_number': 1},
    ]
    extractor = IssueExtractor()
    patterns = {}
    errors, warnings = extractor.extract_issues(log_entries, patterns)

    # Should only appear once (from ERROR level)
    assert len(errors) == 1
    assert errors[0]['line_in_log'] == 1


# FileReferenceExtractor Tests


def test_file_reference_extractor_initialization():
    """Test that file reference extractor can be initialized."""
    extractor = FileReferenceExtractor()
    assert extractor is not None


def test_extract_file_references_unix_format():
    """Test extracting file:line references in Unix format."""
    extractor = FileReferenceExtractor()
    text = 'Error in src/main.py:42 and lib/utils.js:100'
    refs = extractor.extract_references(text)

    assert len(refs) == 2
    assert refs[0] == ('src/main.py', 42)
    assert refs[1] == ('lib/utils.js', 100)


def test_extract_file_references_python_format():
    """Test extracting file references in Python stack trace format."""
    extractor = FileReferenceExtractor()
    text = 'File "/app/main.py", line 42, in function_name'
    refs = extractor.extract_references(text)

    assert len(refs) == 1
    assert refs[0] == ('/app/main.py', 42)


def test_extract_file_references_with_column_numbers():
    """Test extracting file references with column numbers."""
    extractor = FileReferenceExtractor()
    text = 'Error at src/file.py:42:10'
    refs = extractor.extract_references(text)

    assert len(refs) == 1
    assert refs[0] == ('src/file.py', 42)  # Column number is ignored


def test_extract_file_references_from_empty_string():
    """Test extracting file references from empty string."""
    extractor = FileReferenceExtractor()
    refs = extractor.extract_references('')

    assert refs == []


def test_extract_file_references_when_none_exist():
    """Test extracting file references when none exist in text."""
    extractor = FileReferenceExtractor()
    text = 'This is just a normal message with no file references'
    refs = extractor.extract_references(text)

    assert refs == []
