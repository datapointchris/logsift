"""Tests for analyze command."""

import json
import tempfile
from pathlib import Path

from logsift.commands.analyze import analyze_log


def test_analyze_log_basic():
    """Test analyzing a basic log file."""
    log_content = """INFO: Starting application
ERROR: Connection failed
INFO: Shutting down"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_path = f.name

    try:
        # Should not raise
        analyze_log(log_path, output_format='json')
    finally:
        Path(log_path).unlink()


def test_analyze_log_with_json_format():
    """Test analyzing log with JSON output format."""
    log_content = """ERROR: Test error"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_path = f.name

    try:
        # Should not raise
        analyze_log(log_path, output_format='json')
    finally:
        Path(log_path).unlink()


def test_analyze_log_with_markdown_format():
    """Test analyzing log with Markdown output format."""
    log_content = """ERROR: Test error"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_path = f.name

    try:
        # Should not raise
        analyze_log(log_path, output_format='markdown')
    finally:
        Path(log_path).unlink()


def test_analyze_log_with_auto_format():
    """Test analyzing log with auto format detection."""
    log_content = """ERROR: Test error"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_path = f.name

    try:
        # Should not raise
        analyze_log(log_path, output_format='auto')
    finally:
        Path(log_path).unlink()


def test_analyze_log_with_multiple_errors(capsys):
    """Test analyzing log with multiple errors."""
    log_content = """INFO: Starting
ERROR: Error 1
ERROR: Error 2
WARNING: Warning 1"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_path = f.name

    try:
        analyze_log(log_path, output_format='json')
        captured = capsys.readouterr()

        # Should produce valid JSON
        data = json.loads(captured.out)
        assert 'errors' in data
    finally:
        Path(log_path).unlink()


def test_analyze_log_empty_file(capsys):
    """Test analyzing an empty log file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        # Write nothing
        log_path = f.name

    try:
        analyze_log(log_path, output_format='json')
        captured = capsys.readouterr()

        # Should still produce valid output
        data = json.loads(captured.out)
        assert data['stats']['total_errors'] == 0
    finally:
        Path(log_path).unlink()


def test_analyze_log_with_file_references(capsys):
    """Test analyzing log with file references."""
    log_content = """ERROR: Failed at src/main.py:45"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_path = f.name

    try:
        analyze_log(log_path, output_format='json')
        captured = capsys.readouterr()

        data = json.loads(captured.out)
        assert len(data['errors']) == 1
        # File references should be extracted
    finally:
        Path(log_path).unlink()


def test_analyze_log_nonexistent_file():
    """Test analyzing a nonexistent file raises appropriate error."""
    from contextlib import suppress

    with suppress(FileNotFoundError, SystemExit):
        analyze_log('/nonexistent/path.log', output_format='json')
        raise AssertionError('Should have raised an error')


def test_analyze_log_with_context(capsys):
    """Test analyzing log includes context lines."""
    log_content = """Line 1
Line 2
ERROR: Test error
Line 4
Line 5"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_path = f.name

    try:
        analyze_log(log_path, output_format='json')
        captured = capsys.readouterr()

        data = json.loads(captured.out)
        error = data['errors'][0]
        # Should have context
        assert 'context_before' in error or 'context_after' in error
    finally:
        Path(log_path).unlink()


def test_analyze_log_with_real_fixture(capsys):
    """Test analyzing the build_error.log fixture."""
    fixture_path = Path(__file__).parent.parent / 'fixtures' / 'sample_logs' / 'build_error.log'

    if fixture_path.exists():
        analyze_log(str(fixture_path), output_format='json')
        captured = capsys.readouterr()

        data = json.loads(captured.out)
        assert data['stats']['total_errors'] >= 2


def test_analyze_log_output_is_valid_json(capsys):
    """Test that JSON output is valid and parseable."""
    log_content = """ERROR: Test error"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_path = f.name

    try:
        analyze_log(log_path, output_format='json')
        captured = capsys.readouterr()

        # Should not raise exception
        data = json.loads(captured.out)
        assert isinstance(data, dict)
    finally:
        Path(log_path).unlink()


def test_analyze_log_markdown_output_is_string(capsys):
    """Test that Markdown output is a string."""
    log_content = """ERROR: Test error"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write(log_content)
        log_path = f.name

    try:
        analyze_log(log_path, output_format='markdown')
        captured = capsys.readouterr()

        # Should have output
        assert len(captured.out) > 0
        assert isinstance(captured.out, str)
    finally:
        Path(log_path).unlink()
