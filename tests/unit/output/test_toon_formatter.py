"""Tests for TOON formatter."""

import json

import pytest

from logsift.output.toon_formatter import _compact_error
from logsift.output.toon_formatter import _prepare_for_toon
from logsift.output.toon_formatter import _strip_nulls
from logsift.output.toon_formatter import format_toon


@pytest.fixture
def sample_analysis_result():
    """Sample analysis result with full metadata."""
    return {
        'summary': {
            'status': 'failed',
            'exit_code': 127,
            'duration_seconds': 0.01,
            'command': 'bash test.sh',
            'log_file': '/tmp/test.log',
        },
        'stats': {
            'total_errors': 1,
            'total_warnings': 1,
        },
        'errors': [
            {
                'id': 1,
                'severity': 'error',
                'line_in_log': 218,
                'message': 'bash: unzip: command not found',
                'file': None,
                'file_line': None,
                'context_before': [
                    {'line_number': 216, 'message': 'Downloading package...'},
                    {'line_number': 217, 'message': 'Download complete'},
                ],
                'context_after': [
                    {'line_number': 219, 'message': 'Installation failed'},
                    {'line_number': 220, 'message': 'Exiting'},
                ],
                'suggestion': 'Install unzip package',
                'pattern_matched': 'shell_error',
                'description': 'Command not found',
                'tags': ['shell', 'system_error'],
            }
        ],
        'warnings': [
            {
                'id': 2,
                'severity': 'warning',
                'line_in_log': 100,
                'message': 'deprecated function used',
                'file': 'test.py',
                'file_line': 42,
                'context_before': [],
                'context_after': [],
                'suggestion': None,
                'pattern_matched': 'deprecation',
                'description': 'Deprecation warning',
                'tags': ['deprecation'],
            }
        ],
    }


@pytest.fixture
def sample_analysis_result_minimal():
    """Minimal analysis result for success case."""
    return {
        'summary': {
            'status': 'success',
            'exit_code': 0,
            'duration_seconds': 1.23,
            'command': 'echo hello',
        },
        'stats': {
            'total_errors': 0,
            'total_warnings': 0,
        },
        'errors': [],
        'warnings': [],
    }


class TestFormatToon:
    """Tests for format_toon()."""

    def test_format_toon_basic(self, sample_analysis_result):
        """Test basic TOON formatting."""
        result = format_toon(sample_analysis_result)

        # Should return a string
        assert isinstance(result, str)

        # Should contain key sections
        assert 'summary:' in result
        assert 'stats:' in result
        assert 'errors' in result
        assert 'warnings' in result

        # Should contain error message
        assert 'bash: unzip: command not found' in result

        # Should NOT contain stripped metadata
        assert 'pattern_matched' not in result
        assert 'shell_error' not in result
        assert 'description' not in result
        assert 'Command not found' not in result
        assert 'tags' not in result
        assert 'context_before' not in result
        assert 'context_after' not in result

    def test_format_toon_minimal(self, sample_analysis_result_minimal):
        """Test TOON formatting with minimal/success data."""
        result = format_toon(sample_analysis_result_minimal)

        assert isinstance(result, str)
        assert 'summary:' in result
        assert 'status: success' in result
        assert 'exit_code: 0' in result

    def test_token_reduction_vs_json(self, sample_analysis_result):
        """Test that TOON achieves significant token reduction vs JSON."""
        toon_output = format_toon(sample_analysis_result)
        json_output = json.dumps(sample_analysis_result, indent=2)

        toon_size = len(toon_output)
        json_size = len(json_output)

        # TOON should be significantly smaller (at least 20% reduction)
        reduction_percent = (1 - toon_size / json_size) * 100
        assert reduction_percent >= 20, f'Expected >= 20% reduction, got {reduction_percent:.1f}%'


class TestPrepareForToon:
    """Tests for _prepare_for_toon()."""

    def test_prepare_strips_metadata(self, sample_analysis_result):
        """Test that preparation strips pattern metadata from errors."""
        result = _prepare_for_toon(sample_analysis_result)

        # Summary and stats should be preserved
        assert 'summary' in result
        assert 'stats' in result

        # Errors should exist
        assert 'errors' in result
        assert len(result['errors']) == 1

        # Error should NOT have metadata fields
        error = result['errors'][0]
        assert 'pattern_matched' not in error
        assert 'description' not in error
        assert 'tags' not in error
        assert 'context_before' not in error
        assert 'context_after' not in error

        # Error SHOULD have actionable fields
        assert 'id' in error
        assert 'severity' in error
        assert 'line_in_log' in error
        assert 'message' in error
        assert 'suggestion' in error

    def test_prepare_strips_nulls(self, sample_analysis_result):
        """Test that preparation strips null fields."""
        result = _prepare_for_toon(sample_analysis_result)

        # Error has file=None and file_line=None, should be stripped
        error = result['errors'][0]
        assert 'file' not in error
        assert 'file_line' not in error

        # Warning has suggestion=None, should be stripped
        warning = result['warnings'][0]
        assert 'suggestion' not in warning

    def test_prepare_preserves_non_null_values(self, sample_analysis_result):
        """Test that non-null actionable fields are preserved."""
        result = _prepare_for_toon(sample_analysis_result)

        # Warning has file and file_line, should be kept
        warning = result['warnings'][0]
        assert warning['file'] == 'test.py'
        assert warning['file_line'] == 42


class TestCompactError:
    """Tests for _compact_error()."""

    def test_compact_error_keeps_actionable_fields(self):
        """Test that compact_error keeps only actionable fields."""
        error = {
            'id': 1,
            'severity': 'error',
            'line_in_log': 100,
            'message': 'test error',
            'file': 'test.py',
            'file_line': 42,
            'suggestion': 'fix it',
            'pattern_matched': 'some_pattern',
            'description': 'some description',
            'tags': ['tag1', 'tag2'],
            'context_before': ['line1', 'line2'],
            'context_after': ['line3', 'line4'],
        }

        result = _compact_error(error)

        # Should have actionable fields
        assert result['id'] == 1
        assert result['severity'] == 'error'
        assert result['line_in_log'] == 100
        assert result['message'] == 'test error'
        assert result['file'] == 'test.py'
        assert result['file_line'] == 42
        assert result['suggestion'] == 'fix it'

        # Should NOT have metadata fields
        assert 'pattern_matched' not in result
        assert 'description' not in result
        assert 'tags' not in result
        assert 'context_before' not in result
        assert 'context_after' not in result

    def test_compact_error_strips_nulls(self):
        """Test that compact_error strips null fields."""
        error = {
            'id': 1,
            'severity': 'error',
            'line_in_log': 100,
            'message': 'test error',
            'file': None,
            'file_line': None,
            'suggestion': None,
        }

        result = _compact_error(error)

        # Should have non-null fields
        assert result['id'] == 1
        assert result['severity'] == 'error'
        assert result['line_in_log'] == 100
        assert result['message'] == 'test error'

        # Should NOT have null fields
        assert 'file' not in result
        assert 'file_line' not in result
        assert 'suggestion' not in result


class TestStripNulls:
    """Tests for _strip_nulls()."""

    def test_strip_nulls_removes_none_values(self):
        """Test that strip_nulls removes None values."""
        data = {
            'a': 1,
            'b': None,
            'c': 'value',
            'd': None,
        }

        result = _strip_nulls(data)

        assert result == {'a': 1, 'c': 'value'}

    def test_strip_nulls_preserves_empty_strings(self):
        """Test that strip_nulls preserves empty strings (only removes None)."""
        data = {
            'a': '',
            'b': None,
            'c': 0,
            'd': False,
        }

        result = _strip_nulls(data)

        # Empty string, 0, and False should be preserved (not None)
        assert result == {'a': '', 'c': 0, 'd': False}

    def test_strip_nulls_empty_dict(self):
        """Test strip_nulls with empty dict."""
        result = _strip_nulls({})
        assert result == {}
