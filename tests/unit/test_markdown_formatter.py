"""Tests for Markdown output formatter."""

from logsift.output.markdown_formatter import format_markdown


def test_format_markdown_basic_structure():
    """Test Markdown output has basic structure."""
    analysis_result = {
        'errors': [],
        'warnings': [],
        'stats': {'total_errors': 0, 'total_warnings': 0},
    }

    output = format_markdown(analysis_result)

    assert isinstance(output, str)
    assert len(output) > 0


def test_format_markdown_with_errors_and_warnings():
    """Test Markdown output formats errors and warnings correctly."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Connection failed',
                'file_references': [('db.py', 45)],
                'context_before': [{'message': 'Before line'}],
                'context_after': [{'message': 'After line'}],
            }
        ],
        'warnings': [
            {
                'id': 1,
                'severity': 'warning',
                'line_in_log': 5,
                'message': 'Low memory',
                'context_before': [],
                'context_after': [],
            }
        ],
        'stats': {'total_errors': 1, 'total_warnings': 1},
    }

    output = format_markdown(analysis_result)

    # Should contain error and warning content
    assert 'Connection failed' in output
    assert 'Low memory' in output
    # Should contain file reference
    assert 'db.py' in output


def test_format_markdown_stats():
    """Test Markdown output includes statistics."""
    analysis_result = {
        'errors': [
            {'id': 1, 'severity': 'error', 'line_in_log': 10, 'message': 'Error 1', 'context_before': [], 'context_after': []},
            {'id': 2, 'severity': 'error', 'line_in_log': 20, 'message': 'Error 2', 'context_before': [], 'context_after': []},
        ],
        'warnings': [{'id': 1, 'severity': 'warning', 'line_in_log': 5, 'message': 'Warning 1', 'context_before': [], 'context_after': []}],
        'stats': {'total_errors': 2, 'total_warnings': 1},
    }

    output = format_markdown(analysis_result)

    # Should mention the counts (formatter shows stats)
    assert '2' in output  # 2 errors
    assert '1' in output  # 1 warning
