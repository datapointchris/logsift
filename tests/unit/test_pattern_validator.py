"""Tests for pattern validator."""

from logsift.patterns.validator import validate_pattern
from logsift.patterns.validator import validate_pattern_file


def test_validate_pattern_valid_minimal():
    """Test validating a minimal valid pattern."""
    pattern = {
        'name': 'test_pattern',
        'regex': 'ERROR: (.+)',
        'severity': 'error',
        'description': 'Test error pattern',
        'tags': ['test'],
    }

    # Should not raise
    validate_pattern(pattern)


def test_validate_pattern_valid_with_suggestion():
    """Test validating a pattern with optional suggestion field."""
    pattern = {
        'name': 'test_pattern',
        'regex': 'ERROR: (.+)',
        'severity': 'error',
        'description': 'Test error pattern',
        'tags': ['test'],
        'suggestion': 'Fix the error',
    }

    # Should not raise
    validate_pattern(pattern)


def test_validate_pattern_missing_required_field():
    """Test validating pattern with missing required field."""
    pattern = {
        'regex': 'ERROR: (.+)',
        'severity': 'error',
        'description': 'Test error pattern',
        'tags': ['test'],
    }

    try:
        validate_pattern(pattern)
        raise AssertionError('Should have raised ValueError')
    except ValueError as e:
        assert 'name' in str(e)


def test_validate_pattern_invalid_severity():
    """Test validating pattern with invalid severity."""
    pattern = {
        'name': 'test_pattern',
        'regex': 'ERROR: (.+)',
        'severity': 'invalid',
        'description': 'Test error pattern',
        'tags': ['test'],
    }

    try:
        validate_pattern(pattern)
        raise AssertionError('Should have raised ValueError')
    except ValueError as e:
        assert 'severity' in str(e)


def test_validate_pattern_invalid_regex():
    """Test validating pattern with invalid regex."""
    pattern = {
        'name': 'test_pattern',
        'regex': '[invalid(regex',
        'severity': 'error',
        'description': 'Test error pattern',
        'tags': ['test'],
    }

    try:
        validate_pattern(pattern)
        raise AssertionError('Should have raised ValueError')
    except ValueError as e:
        assert 'regex' in str(e)


def test_validate_pattern_empty_tags():
    """Test validating pattern with empty tags list."""
    pattern = {
        'name': 'test_pattern',
        'regex': 'ERROR: (.+)',
        'severity': 'error',
        'description': 'Test error pattern',
        'tags': [],
    }

    try:
        validate_pattern(pattern)
        raise AssertionError('Should have raised ValueError')
    except ValueError as e:
        assert 'tags' in str(e)


def test_validate_pattern_file_valid():
    """Test validating a valid pattern file structure."""
    pattern_file = {
        'patterns': [
            {
                'name': 'pattern1',
                'regex': 'ERROR: (.+)',
                'severity': 'error',
                'description': 'First pattern',
                'tags': ['test'],
            },
            {
                'name': 'pattern2',
                'regex': 'WARNING: (.+)',
                'severity': 'warning',
                'description': 'Second pattern',
                'tags': ['test'],
            },
        ]
    }

    # Should not raise
    validate_pattern_file(pattern_file)


def test_validate_pattern_file_missing_patterns_key():
    """Test validating pattern file without 'patterns' key."""
    pattern_file = {'other_key': []}

    try:
        validate_pattern_file(pattern_file)
        raise AssertionError('Should have raised ValueError')
    except ValueError as e:
        assert 'patterns' in str(e)


def test_validate_pattern_file_patterns_not_list():
    """Test validating pattern file where patterns is not a list."""
    pattern_file = {'patterns': 'not a list'}

    try:
        validate_pattern_file(pattern_file)
        raise AssertionError('Should have raised ValueError')
    except ValueError as e:
        assert 'list' in str(e)


def test_validate_pattern_file_empty_patterns():
    """Test validating pattern file with empty patterns list."""
    pattern_file = {'patterns': []}

    try:
        validate_pattern_file(pattern_file)
        raise AssertionError('Should have raised ValueError')
    except ValueError as e:
        assert 'empty' in str(e)


def test_validate_pattern_file_invalid_pattern():
    """Test validating pattern file with an invalid pattern."""
    pattern_file = {
        'patterns': [
            {
                'name': 'valid_pattern',
                'regex': 'ERROR: (.+)',
                'severity': 'error',
                'description': 'Valid pattern',
                'tags': ['test'],
            },
            {
                # Missing 'name' field
                'regex': 'WARNING: (.+)',
                'severity': 'warning',
                'description': 'Invalid pattern',
                'tags': ['test'],
            },
        ]
    }

    try:
        validate_pattern_file(pattern_file)
        raise AssertionError('Should have raised ValueError')
    except ValueError as e:
        assert 'name' in str(e)


def test_validate_pattern_duplicate_names():
    """Test validating pattern file with duplicate pattern names."""
    pattern_file = {
        'patterns': [
            {
                'name': 'duplicate',
                'regex': 'ERROR: (.+)',
                'severity': 'error',
                'description': 'First pattern',
                'tags': ['test'],
            },
            {
                'name': 'duplicate',
                'regex': 'WARNING: (.+)',
                'severity': 'warning',
                'description': 'Second pattern',
                'tags': ['test'],
            },
        ]
    }

    try:
        validate_pattern_file(pattern_file)
        raise AssertionError('Should have raised ValueError')
    except ValueError as e:
        assert 'duplicate' in str(e).lower()
