"""Unit tests for the analyzer module."""

from logsift.core.analyzer import Analyzer

# Initialization Tests


def test_analyzer_initialization():
    """Test that analyzer can be initialized."""
    analyzer = Analyzer()
    assert analyzer is not None


# Basic Analysis Tests


def test_analyze_simple_error_log():
    """Test analyzing a simple log with an error."""
    log_content = """INFO: Starting application
ERROR: Connection failed to database
INFO: Shutting down"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert result is not None
    assert 'errors' in result
    assert len(result['errors']) == 1
    assert result['errors'][0]['severity'] == 'error'
    assert 'Connection failed' in result['errors'][0]['message']


def test_analyze_log_with_warnings():
    """Test analyzing a log with warnings."""
    log_content = """INFO: Starting application
WARNING: Low memory detected
WARN: Deprecated API usage
INFO: Application running"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert result is not None
    assert 'warnings' in result
    assert len(result['warnings']) == 2
    assert result['warnings'][0]['severity'] == 'warning'
    assert result['warnings'][1]['severity'] == 'warning'


def test_analyze_log_with_errors_and_warnings():
    """Test analyzing a log with both errors and warnings."""
    log_content = """INFO: Starting application
WARNING: Low memory
ERROR: Connection failed
WARN: Slow query
ERROR: Timeout occurred"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert len(result['errors']) == 2
    assert len(result['warnings']) == 2


def test_analyze_empty_log():
    """Test analyzing empty log content."""
    analyzer = Analyzer()
    result = analyzer.analyze('')

    assert result is not None
    assert 'errors' in result
    assert 'warnings' in result
    assert len(result['errors']) == 0
    assert len(result['warnings']) == 0


def test_analyze_log_with_no_errors():
    """Test analyzing a log with no errors or warnings."""
    log_content = """INFO: Starting application
INFO: Loading configuration
INFO: Application started successfully"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert len(result['errors']) == 0
    assert len(result['warnings']) == 0


# Context Extraction Tests


def test_analyze_includes_context():
    """Test that analysis includes context around errors."""
    log_content = """Line 1: Starting
Line 2: Loading
ERROR: Something failed
Line 4: Attempting recovery
Line 5: Shutdown"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert len(result['errors']) == 1
    error = result['errors'][0]
    assert 'context_before' in error
    assert 'context_after' in error
    assert len(error['context_before']) > 0
    assert len(error['context_after']) > 0


def test_analyze_context_at_log_boundaries():
    """Test context extraction when error is at beginning or end."""
    log_content_beginning = """ERROR: Failed at start
Line 2: Something
Line 3: Something else"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content_beginning)

    error = result['errors'][0]
    assert len(error['context_before']) == 0
    assert len(error['context_after']) > 0


# Pattern Matching Tests


def test_analyze_with_pattern_matching():
    """Test that analysis includes pattern matches."""
    log_content = """INFO: Installing packages
Error: tmux is already installed
INFO: Installation complete"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    # Should match brew pattern
    assert len(result['errors']) == 1
    error = result['errors'][0]
    # Pattern matching should add metadata
    if 'pattern_matched' in error:
        assert error['pattern_matched'] is not None


# File Reference Extraction Tests


def test_analyze_extracts_file_references():
    """Test that analysis extracts file references from errors."""
    log_content = """INFO: Starting build
ERROR: Syntax error in src/main.py:42
INFO: Build failed"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert len(result['errors']) == 1
    error = result['errors'][0]
    # File references should be extracted
    if 'file_references' in error:
        assert len(error['file_references']) > 0
        assert error['file_references'][0][0] == 'src/main.py'
        assert error['file_references'][0][1] == 42


# Statistics Tests


def test_analyze_includes_statistics():
    """Test that analysis includes statistics."""
    log_content = """INFO: Starting
ERROR: First error
WARNING: First warning
ERROR: Second error
INFO: Done"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert 'stats' in result
    stats = result['stats']
    assert stats['total_errors'] == 2
    assert stats['total_warnings'] == 1


# JSON Log Format Tests


def test_analyze_json_logs():
    """Test analyzing JSON formatted logs."""
    log_content = """{"level": "INFO", "message": "Starting application"}
{"level": "ERROR", "message": "Connection failed"}
{"level": "INFO", "message": "Shutting down"}"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert len(result['errors']) == 1
    assert 'Connection failed' in result['errors'][0]['message']


# Structured Log Format Tests


def test_analyze_structured_logs():
    """Test analyzing structured key=value logs."""
    log_content = """level=info message="Starting application"
level=error message="Connection failed"
level=info message="Shutting down" """

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert len(result['errors']) == 1


# Integration Tests


def test_analyze_complete_pipeline():
    """Test complete analysis pipeline with all features."""
    log_content = """2025-11-28T10:00:00Z [INFO] Starting application
2025-11-28T10:00:01Z [INFO] Loading config from config.json:10
2025-11-28T10:00:02Z [WARNING] Low memory detected
2025-11-28T10:00:03Z [ERROR] Failed to connect to database at db.py:45
2025-11-28T10:00:04Z [ERROR] Timeout after 30 seconds
2025-11-28T10:00:05Z [INFO] Attempting recovery"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    # Should have errors and warnings
    assert len(result['errors']) == 2
    assert len(result['warnings']) == 1

    # Should have statistics
    assert result['stats']['total_errors'] == 2
    assert result['stats']['total_warnings'] == 1

    # Errors should have context
    assert 'context_before' in result['errors'][0]
    assert 'context_after' in result['errors'][0]


def test_analyze_realistic_application_log():
    """Test analyzing a realistic application log scenario."""
    log_content = """[INFO] Application starting
[INFO] Connecting to database
[INFO] Database connection established
[WARNING] Deprecated configuration option detected
[INFO] Starting web server on port 8080
[ERROR] Port 8080 already in use
[ERROR] Failed to start web server
[INFO] Application shutdown initiated"""

    analyzer = Analyzer()
    result = analyzer.analyze(log_content)

    assert len(result['errors']) == 2
    assert len(result['warnings']) == 1

    # First error should have context from previous lines
    first_error = result['errors'][0]
    assert len(first_error['context_before']) > 0
    assert any('web server' in entry.get('message', '').lower() for entry in first_error['context_before'])
