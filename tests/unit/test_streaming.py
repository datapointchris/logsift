"""Unit tests for dual output streaming."""

import json
from io import StringIO

from logsift.output.streaming import write_both_to_stdout
from logsift.output.streaming import write_dual_output
from logsift.output.streaming import write_stream_mode


def test_write_dual_output_to_files(tmp_path):
    """Test writing both JSON and Markdown to separate files."""
    json_path = tmp_path / 'output.json'
    markdown_path = tmp_path / 'output.md'

    result = {
        'summary': {'status': 'failed', 'exit_code': 1},
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'message': 'Test error',
                'line_number': 10,
                'context_before': [],
                'context_after': [],
            }
        ],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    write_dual_output(result, json_path=json_path, markdown_path=markdown_path)

    # Check JSON was written
    assert json_path.exists()
    json_data = json.loads(json_path.read_text())
    assert json_data['summary']['status'] == 'failed'
    assert len(json_data['errors']) == 1

    # Check Markdown was written
    assert markdown_path.exists()
    markdown_content = markdown_path.read_text()
    assert '**Errors:** 1' in markdown_content
    assert 'Test error' in markdown_content


def test_write_dual_output_to_streams():
    """Test writing to stream objects."""
    json_stream = StringIO()
    markdown_stream = StringIO()

    result = {
        'summary': {'status': 'success', 'exit_code': 0},
        'errors': [],
        'warnings': [],
        'stats': {'total_errors': 0, 'total_warnings': 0},
    }

    write_dual_output(result, json_stream=json_stream, markdown_stream=markdown_stream)

    # Check JSON stream
    json_output = json_stream.getvalue()
    assert json_output  # Not empty
    json_data = json.loads(json_output)
    assert json_data['summary']['status'] == 'success'

    # Check Markdown stream
    markdown_output = markdown_stream.getvalue()
    assert markdown_output  # Not empty
    assert 'Clean' in markdown_output


def test_write_dual_output_json_to_file_markdown_to_stream(tmp_path):
    """Test writing JSON to file and Markdown to stream (stream mode)."""
    json_path = tmp_path / 'output.json'
    markdown_stream = StringIO()

    result = {
        'summary': {'status': 'failed', 'exit_code': 1},
        'errors': [{'id': 1, 'severity': 'error', 'message': 'Error', 'line_number': 5, 'context_before': [], 'context_after': []}],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    write_dual_output(result, json_path=json_path, markdown_stream=markdown_stream)

    # JSON saved to file
    assert json_path.exists()
    json_data = json.loads(json_path.read_text())
    assert json_data['summary']['status'] == 'failed'

    # Markdown written to stream
    markdown_output = markdown_stream.getvalue()
    assert '**Errors:** 1' in markdown_output
    assert 'Error' in markdown_output


def test_write_stream_mode(tmp_path):
    """Test stream mode helper function."""
    json_path = tmp_path / 'cache' / 'output.json'

    result = {
        'summary': {'status': 'success', 'exit_code': 0},
        'errors': [],
        'warnings': [],
        'stats': {'total_errors': 0, 'total_warnings': 0},
    }

    # Redirect stdout to capture markdown
    import sys
    from io import StringIO

    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        write_stream_mode(result, json_path)
        markdown_output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    # JSON saved to file
    assert json_path.exists()
    json_data = json.loads(json_path.read_text())
    assert json_data['summary']['status'] == 'success'

    # Markdown written to stdout
    assert 'Clean' in markdown_output


def test_write_both_to_stdout():
    """Test writing both outputs to stdout with separator."""
    import sys
    from io import StringIO

    result = {
        'summary': {'status': 'failed', 'exit_code': 1},
        'errors': [{'id': 1, 'severity': 'error', 'message': 'Test', 'line_number': 1, 'context_before': [], 'context_after': []}],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        write_both_to_stdout(result)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    # Should have both sections
    assert '=== JSON OUTPUT ===' in output
    assert '=== MARKDOWN OUTPUT ===' in output

    # Should have content from both
    assert '"status": "failed"' in output  # JSON
    assert '**Errors:** 1' in output  # Markdown


def test_write_dual_output_creates_parent_directories(tmp_path):
    """Test that parent directories are created if they don't exist."""
    json_path = tmp_path / 'nested' / 'dir' / 'output.json'
    markdown_path = tmp_path / 'other' / 'nested' / 'output.md'

    result = {
        'summary': {'status': 'success', 'exit_code': 0},
        'errors': [],
        'warnings': [],
        'stats': {'total_errors': 0, 'total_warnings': 0},
    }

    write_dual_output(result, json_path=json_path, markdown_path=markdown_path)

    # Both files should exist with their parent directories created
    assert json_path.exists()
    assert markdown_path.exists()


def test_write_dual_output_no_destinations():
    """Test that function handles no output destinations gracefully."""
    result = {
        'summary': {'status': 'success', 'exit_code': 0},
        'errors': [],
        'warnings': [],
        'stats': {'total_errors': 0, 'total_warnings': 0},
    }

    # Should not raise an error even with no destinations
    write_dual_output(result)


def test_stream_manager_class(tmp_path):
    """Test StreamManager class wrapper."""
    from logsift.output.streaming import StreamManager

    manager = StreamManager()

    json_path = tmp_path / 'output.json'
    markdown_path = tmp_path / 'output.md'

    result = {
        'summary': {'status': 'failed', 'exit_code': 1},
        'errors': [{'id': 1, 'severity': 'error', 'message': 'Error', 'line_number': 1, 'context_before': [], 'context_after': []}],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    manager.write_dual(result, json_path=str(json_path), markdown_path=str(markdown_path))

    # Check files were written
    assert json_path.exists()
    assert markdown_path.exists()
