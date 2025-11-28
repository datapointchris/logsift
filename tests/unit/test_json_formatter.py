"""Tests for JSON output formatter."""

import json

from logsift.output.json_formatter import format_json


def test_format_json_basic_structure():
    """Test JSON output has required top-level structure."""
    analysis_result = {
        'errors': [],
        'warnings': [],
        'stats': {'total_errors': 0, 'total_warnings': 0},
    }

    output = format_json(analysis_result)
    data = json.loads(output)

    assert 'errors' in data
    assert 'warnings' in data
    assert 'stats' in data


def test_format_json_with_errors():
    """Test JSON output formats errors correctly."""
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

    output = format_json(analysis_result)
    data = json.loads(output)

    assert len(data['errors']) == 1
    assert data['errors'][0]['id'] == 1
    assert data['errors'][0]['severity'] == 'error'
    assert data['errors'][0]['message'] == 'Connection failed'


def test_format_json_with_warnings():
    """Test JSON output formats warnings correctly."""
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

    output = format_json(analysis_result)
    data = json.loads(output)

    assert len(data['warnings']) == 1
    assert data['warnings'][0]['severity'] == 'warning'


def test_format_json_with_file_references():
    """Test JSON output includes file references."""
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

    output = format_json(analysis_result)
    data = json.loads(output)

    assert 'file_references' in data['errors'][0]
    assert data['errors'][0]['file_references'] == [['db.py', 45]]


def test_format_json_with_pattern_match():
    """Test JSON output includes pattern match metadata."""
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

    output = format_json(analysis_result)
    data = json.loads(output)

    assert data['errors'][0]['pattern_name'] == 'connection_error'
    assert data['errors'][0]['description'] == 'Connection error detected'
    assert data['errors'][0]['tags'] == ['network', 'connection']


def test_format_json_with_context():
    """Test JSON output includes context lines."""
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

    output = format_json(analysis_result)
    data = json.loads(output)

    assert len(data['errors'][0]['context_before']) == 2
    assert len(data['errors'][0]['context_after']) == 2
    assert data['errors'][0]['context_before'][0]['message'] == 'Line before 1'


def test_format_json_with_suggestion():
    """Test JSON output includes suggestions when available."""
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

    output = format_json(analysis_result)
    data = json.loads(output)

    assert data['errors'][0]['suggestion'] == 'Install the missing package'


def test_format_json_with_stats():
    """Test JSON output includes statistics."""
    analysis_result = {
        'errors': [
            {'id': 1, 'severity': 'error', 'line_in_log': 10, 'message': 'Error 1', 'context_before': [], 'context_after': []},
            {'id': 2, 'severity': 'error', 'line_in_log': 20, 'message': 'Error 2', 'context_before': [], 'context_after': []},
        ],
        'warnings': [{'id': 1, 'severity': 'warning', 'line_in_log': 5, 'message': 'Warning 1', 'context_before': [], 'context_after': []}],
        'stats': {'total_errors': 2, 'total_warnings': 1},
    }

    output = format_json(analysis_result)
    data = json.loads(output)

    assert data['stats']['total_errors'] == 2
    assert data['stats']['total_warnings'] == 1


def test_format_json_empty_result():
    """Test JSON output handles empty analysis results."""
    analysis_result = {'errors': [], 'warnings': [], 'stats': {'total_errors': 0, 'total_warnings': 0}}

    output = format_json(analysis_result)
    data = json.loads(output)

    assert data['errors'] == []
    assert data['warnings'] == []
    assert data['stats']['total_errors'] == 0


def test_format_json_pretty_printed():
    """Test JSON output is pretty-printed (indented)."""
    analysis_result = {
        'errors': [{'id': 1, 'severity': 'error', 'line_in_log': 10, 'message': 'Test', 'context_before': [], 'context_after': []}],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_json(analysis_result)

    # Pretty-printed JSON should contain newlines and indentation
    assert '\n' in output
    assert '  ' in output or '\t' in output


def test_format_json_valid_json():
    """Test output is valid JSON that can be parsed."""
    analysis_result = {
        'errors': [{'id': 1, 'severity': 'error', 'line_in_log': 10, 'message': 'Test', 'context_before': [], 'context_after': []}],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_json(analysis_result)

    # Should not raise exception
    data = json.loads(output)
    assert isinstance(data, dict)


def test_format_json_preserves_all_fields():
    """Test JSON output preserves all fields from analysis result."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Test error',
                'pattern_name': 'test_pattern',
                'description': 'Test description',
                'tags': ['test'],
                'suggestion': 'Fix it',
                'file_references': [('file.py', 10)],
                'context_before': [{'message': 'before'}],
                'context_after': [{'message': 'after'}],
                'custom_field': 'custom_value',
            }
        ],
        'warnings': [],
        'stats': {'total_errors': 1, 'total_warnings': 0},
    }

    output = format_json(analysis_result)
    data = json.loads(output)

    error = data['errors'][0]
    assert error['id'] == 1
    assert error['pattern_name'] == 'test_pattern'
    assert error['custom_field'] == 'custom_value'
