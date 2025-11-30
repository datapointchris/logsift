"""Unit tests for the extractor system."""

from logsift.core.extractors import ErrorExtractor
from logsift.core.extractors import FileReferenceExtractor
from logsift.core.extractors import WarningExtractor

# ErrorExtractor Tests


def test_error_extractor_initialization():
    """Test that error extractor can be initialized."""
    extractor = ErrorExtractor()
    assert extractor is not None


def test_extract_errors_from_log_entries():
    """Test extracting errors from parsed log entries."""
    log_entries = [
        {'level': 'INFO', 'message': 'Starting process', 'line_number': 1},
        {'level': 'ERROR', 'message': 'Failed to connect', 'line_number': 2},
        {'level': 'ERROR', 'message': 'Timeout occurred', 'line_number': 3},
    ]
    extractor = ErrorExtractor()
    errors = extractor.extract_errors(log_entries)

    assert len(errors) == 2
    assert errors[0]['severity'] == 'error'
    assert errors[0]['message'] == 'Failed to connect'
    assert errors[0]['line_in_log'] == 2
    assert errors[1]['message'] == 'Timeout occurred'
    assert errors[1]['line_in_log'] == 3


def test_extract_errors_case_insensitive():
    """Test that error extraction is case insensitive."""
    log_entries = [
        {'level': 'error', 'message': 'Lower case error', 'line_number': 1},
        {'level': 'ERROR', 'message': 'Upper case error', 'line_number': 2},
        {'level': 'Error', 'message': 'Mixed case error', 'line_number': 3},
    ]
    extractor = ErrorExtractor()
    errors = extractor.extract_errors(log_entries)

    assert len(errors) == 3


def test_extract_errors_from_empty_list():
    """Test extracting errors from empty log list."""
    extractor = ErrorExtractor()
    errors = extractor.extract_errors([])

    assert errors == []


def test_extract_errors_when_none_exist():
    """Test extracting errors when no errors are present."""
    log_entries = [
        {'level': 'INFO', 'message': 'All good', 'line_number': 1},
        {'level': 'DEBUG', 'message': 'Debug info', 'line_number': 2},
    ]
    extractor = ErrorExtractor()
    errors = extractor.extract_errors(log_entries)

    assert errors == []


def test_extract_errors_assigns_ids():
    """Test that errors are assigned sequential IDs."""
    log_entries = [
        {'level': 'ERROR', 'message': 'First error', 'line_number': 1},
        {'level': 'ERROR', 'message': 'Second error', 'line_number': 2},
        {'level': 'ERROR', 'message': 'Third error', 'line_number': 3},
    ]
    extractor = ErrorExtractor()
    errors = extractor.extract_errors(log_entries)

    assert errors[0]['id'] == 1
    assert errors[1]['id'] == 2
    assert errors[2]['id'] == 3


def test_extract_errors_preserves_all_fields():
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
    extractor = ErrorExtractor()
    errors = extractor.extract_errors(log_entries)

    assert errors[0]['message'] == 'Connection failed'
    assert errors[0]['line_in_log'] == 42
    assert errors[0]['timestamp'] == '2025-11-28T10:30:00Z'


def test_extract_shell_errors_command_not_found():
    """Test that shell error patterns are detected (command not found)."""
    log_entries = [
        {'level': 'INFO', 'message': 'Starting process', 'line_number': 1, 'format': 'plain'},
        {'level': 'INFO', 'message': 'bash: unzip: command not found', 'line_number': 2, 'format': 'plain'},
        {'level': 'INFO', 'message': 'zsh:1: no such file or directory: /path/file.sh', 'line_number': 3, 'format': 'plain'},
    ]
    extractor = ErrorExtractor()
    errors = extractor.extract_errors(log_entries)

    assert len(errors) == 2
    assert errors[0]['severity'] == 'error'
    assert errors[0]['message'] == 'bash: unzip: command not found'
    assert errors[0]['line_in_log'] == 2
    assert errors[0]['pattern_name'] == 'shell_error'
    assert errors[0]['description'] == 'Command not found'  # Matches ': command not found' pattern
    assert 'shell' in errors[0]['tags']

    assert errors[1]['message'] == 'zsh:1: no such file or directory: /path/file.sh'
    assert errors[1]['line_in_log'] == 3
    assert errors[1]['description'] == 'File or directory not found'


def test_extract_shell_errors_no_duplicates():
    """Test that ERROR level entries aren't duplicated when they also match patterns."""
    log_entries = [
        {'level': 'ERROR', 'message': 'fatal error: file not found', 'line_number': 1, 'format': 'plain'},
    ]
    extractor = ErrorExtractor()
    errors = extractor.extract_errors(log_entries)

    # Should only appear once (as ERROR level, not as pattern match)
    assert len(errors) == 1
    assert errors[0]['line_in_log'] == 1


def test_extract_shell_errors_package_manager():
    """Test that package manager errors are detected."""
    log_entries = [
        {'level': 'INFO', 'message': 'E: Unable to locate package foobar', 'line_number': 1, 'format': 'plain'},
        {'level': 'INFO', 'message': 'npm ERR! 404 Not Found', 'line_number': 2, 'format': 'plain'},
    ]
    extractor = ErrorExtractor()
    errors = extractor.extract_errors(log_entries)

    assert len(errors) == 2
    assert 'Package not found' in errors[0]['description']
    assert 'NPM error' in errors[1]['description']


# WarningExtractor Tests


def test_warning_extractor_initialization():
    """Test that warning extractor can be initialized."""
    extractor = WarningExtractor()
    assert extractor is not None


def test_extract_warnings_from_log_entries():
    """Test extracting warnings from parsed log entries."""
    log_entries = [
        {'level': 'INFO', 'message': 'Starting process', 'line_number': 1},
        {'level': 'WARNING', 'message': 'Low memory', 'line_number': 2},
        {'level': 'WARN', 'message': 'Deprecated API', 'line_number': 3},
    ]
    extractor = WarningExtractor()
    warnings = extractor.extract_warnings(log_entries)

    assert len(warnings) == 2
    assert warnings[0]['severity'] == 'warning'
    assert warnings[0]['message'] == 'Low memory'
    assert warnings[0]['line_in_log'] == 2
    assert warnings[1]['message'] == 'Deprecated API'


def test_extract_warnings_case_insensitive():
    """Test that warning extraction is case insensitive."""
    log_entries = [
        {'level': 'warning', 'message': 'Lower case', 'line_number': 1},
        {'level': 'WARNING', 'message': 'Upper case', 'line_number': 2},
        {'level': 'warn', 'message': 'Warn variant', 'line_number': 3},
        {'level': 'WARN', 'message': 'WARN variant upper', 'line_number': 4},
    ]
    extractor = WarningExtractor()
    warnings = extractor.extract_warnings(log_entries)

    assert len(warnings) == 4


def test_extract_warnings_from_empty_list():
    """Test extracting warnings from empty log list."""
    extractor = WarningExtractor()
    warnings = extractor.extract_warnings([])

    assert warnings == []


def test_extract_warnings_when_none_exist():
    """Test extracting warnings when no warnings are present."""
    log_entries = [
        {'level': 'INFO', 'message': 'All good', 'line_number': 1},
        {'level': 'ERROR', 'message': 'Error occurred', 'line_number': 2},
    ]
    extractor = WarningExtractor()
    warnings = extractor.extract_warnings(log_entries)

    assert warnings == []


def test_extract_warnings_assigns_ids():
    """Test that warnings are assigned sequential IDs."""
    log_entries = [
        {'level': 'WARNING', 'message': 'First warning', 'line_number': 1},
        {'level': 'WARNING', 'message': 'Second warning', 'line_number': 2},
    ]
    extractor = WarningExtractor()
    warnings = extractor.extract_warnings(log_entries)

    assert warnings[0]['id'] == 1
    assert warnings[1]['id'] == 2


# FileReferenceExtractor Tests


def test_file_reference_extractor_initialization():
    """Test that file reference extractor can be initialized."""
    extractor = FileReferenceExtractor()
    assert extractor is not None


def test_extract_simple_file_reference():
    """Test extracting a simple file:line reference."""
    text = 'Error in file.py:42'
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    assert len(references) == 1
    assert references[0] == ('file.py', 42)


def test_extract_absolute_path_reference():
    """Test extracting absolute path file references."""
    text = 'Error in /usr/local/lib/python3.13/site-packages/module.py:123'
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    assert len(references) == 1
    assert references[0] == ('/usr/local/lib/python3.13/site-packages/module.py', 123)


def test_extract_relative_path_reference():
    """Test extracting relative path file references."""
    text = 'Error in ./src/core/parser.py:67'
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    assert len(references) == 1
    assert references[0] == ('./src/core/parser.py', 67)


def test_extract_multiple_references():
    """Test extracting multiple file references from one text."""
    text = 'Called from main.py:10, then utils.py:25, then handler.py:50'
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    assert len(references) == 3
    assert references[0] == ('main.py', 10)
    assert references[1] == ('utils.py', 25)
    assert references[2] == ('handler.py', 50)


def test_extract_references_with_various_extensions():
    """Test extracting references with different file extensions."""
    text = 'Errors in app.js:100, styles.css:50, config.json:5, README.md:20'
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    assert len(references) == 4
    assert ('app.js', 100) in references
    assert ('styles.css', 50) in references
    assert ('config.json', 5) in references
    assert ('README.md', 20) in references


def test_extract_references_from_stack_trace():
    """Test extracting references from stack trace format."""
    text = """Traceback (most recent call last):
  File "/app/main.py", line 42, in main
  File "/app/utils/helper.py", line 15, in process
  File "/app/core/engine.py", line 88, in execute"""
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    assert len(references) == 3
    assert ('/app/main.py', 42) in references
    assert ('/app/utils/helper.py', 15) in references
    assert ('/app/core/engine.py', 88) in references


def test_extract_references_from_empty_text():
    """Test extracting references from empty text."""
    extractor = FileReferenceExtractor()
    references = extractor.extract_references('')

    assert references == []


def test_extract_references_when_none_exist():
    """Test extracting references from text with no file references."""
    text = 'This is just a regular log message with no file references'
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    assert references == []


def test_extract_references_with_windows_paths():
    """Test extracting Windows-style file paths."""
    text = r'Error in C:\Users\dev\project\src\main.py:100'
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    assert len(references) == 1
    assert references[0] == (r'C:\Users\dev\project\src\main.py', 100)


def test_extract_references_ignores_invalid_line_numbers():
    """Test that invalid line numbers are not extracted."""
    text = 'file.py:abc should not match, but file.py:123 should'
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    assert len(references) == 1
    assert references[0] == ('file.py', 123)


def test_extract_references_from_compile_error():
    """Test extracting from typical compiler error format."""
    text = 'src/main.rs:45:10: error: expected `;`, found `}`'
    extractor = FileReferenceExtractor()
    references = extractor.extract_references(text)

    # Should extract the file and first line number (column is separate)
    assert len(references) >= 1
    assert references[0][0] == 'src/main.rs'
    assert references[0][1] == 45
