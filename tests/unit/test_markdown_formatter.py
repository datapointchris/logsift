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


def test_format_markdown_with_errors():
    """Test Markdown output formats errors correctly."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Connection failed',
                'context_before': [],
                'context_after': [],
            }
        ],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_markdown(analysis_result)

    assert 'ERROR' in output or 'error' in output.lower()
    assert 'Connection failed' in output
    assert '10' in output  # line number


def test_format_markdown_with_warnings():
    """Test Markdown output formats warnings correctly."""
    analysis_result = {
        'errors': [],
        'warnings': [
            {
                'id': 1,
                'severity': 'warning',
                'line_in_log': 5,
                'message': 'Low memory detected',
                'context_before': [],
                'context_after': [],
            }
        ],
        'stats': {'total_errors': 0, 'total_warnings': 1},
    }

    output = format_markdown(analysis_result)

    assert 'WARNING' in output or 'warning' in output.lower()
    assert 'Low memory detected' in output


def test_format_markdown_with_file_references():
    """Test Markdown output includes file references."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Failed at db.py:45',
                'file_references': [('db.py', 45)],
                'context_before': [],
                'context_after': [],
            }
        ],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_markdown(analysis_result)

    assert 'db.py' in output
    assert '45' in output


def test_format_markdown_with_pattern_match():
    """Test Markdown output includes pattern match metadata."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Connection failed',
                'pattern_name': 'connection_error',
                'description': 'Connection error detected',
                'tags': ['network', 'connection'],
                'context_before': [],
                'context_after': [],
            }
        ],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_markdown(analysis_result)

    assert 'connection_error' in output or 'Connection error detected' in output


def test_format_markdown_with_context():
    """Test Markdown output includes context lines."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Connection failed',
                'context_before': [
                    {'message': 'Line before 1', 'line_number': 8},
                    {'message': 'Line before 2', 'line_number': 9},
                ],
                'context_after': [
                    {'message': 'Line after 1', 'line_number': 11},
                    {'message': 'Line after 2', 'line_number': 12},
                ],
            }
        ],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_markdown(analysis_result)

    assert 'Line before 1' in output
    assert 'Line after 1' in output


def test_format_markdown_with_suggestion():
    """Test Markdown output includes suggestions when available."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Package not found',
                'suggestion': 'Install the missing package',
                'context_before': [],
                'context_after': [],
            }
        ],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_markdown(analysis_result)

    assert 'Install the missing package' in output or 'suggestion' in output.lower()


def test_format_markdown_with_stats():
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

    # Should show counts somewhere
    assert '2' in output  # error count
    assert '1' in output  # warning count


def test_format_markdown_empty_result():
    """Test Markdown output handles empty analysis results."""
    analysis_result = {'errors': [], 'warnings': [], 'stats': {'total_errors': 0, 'total_warnings': 0}}

    output = format_markdown(analysis_result)

    assert isinstance(output, str)
    # Should indicate no errors/warnings found
    assert '0' in output or 'no' in output.lower() or 'clean' in output.lower()


def test_format_markdown_multiple_errors():
    """Test Markdown output handles multiple errors."""
    analysis_result = {
        'errors': [
            {'id': 1, 'severity': 'error', 'line_in_log': 10, 'message': 'Error 1', 'context_before': [], 'context_after': []},
            {'id': 2, 'severity': 'error', 'line_in_log': 20, 'message': 'Error 2', 'context_before': [], 'context_after': []},
            {'id': 3, 'severity': 'error', 'line_in_log': 30, 'message': 'Error 3', 'context_before': [], 'context_after': []},
        ],
        'warnings': [],
        'stats': {'total_errors': 3, 'total_warnings': 0},
    }

    output = format_markdown(analysis_result)

    assert 'Error 1' in output
    assert 'Error 2' in output
    assert 'Error 3' in output


def test_format_markdown_contains_markdown_elements():
    """Test Markdown output uses markdown formatting."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Connection failed',
                'context_before': [],
                'context_after': [],
            }
        ],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_markdown(analysis_result)

    # Should contain markdown elements like headers, code blocks, or lists
    markdown_indicators = ['#', '```', '-', '*', '**', '__']
    assert any(indicator in output for indicator in markdown_indicators)


def test_format_markdown_with_tags():
    """Test Markdown output includes tags when available."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Connection failed',
                'tags': ['network', 'connection', 'fixable'],
                'context_before': [],
                'context_after': [],
            }
        ],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_markdown(analysis_result)

    # Tags should appear in some form
    assert 'network' in output or 'connection' in output or 'fixable' in output
