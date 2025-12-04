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


def test_format_json_with_errors_and_warnings():
    """Test JSON output formats errors and warnings correctly."""
    analysis_result = {
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 10,
                'message': 'Connection failed',
                'pattern_name': 'connection_error',
                'tags': ['network'],
                'context_before': [],
                'context_after': [],
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

    output = format_json(analysis_result)
    data = json.loads(output)

    assert len(data['errors']) == 1
    assert data['errors'][0]['message'] == 'Connection failed'
    assert data['errors'][0]['pattern_name'] == 'connection_error'
    assert len(data['warnings']) == 1
    assert data['warnings'][0]['message'] == 'Low memory'
    assert data['stats']['total_errors'] == 1
    assert data['stats']['total_warnings'] == 1


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
