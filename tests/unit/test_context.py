"""Unit tests for the context extraction system."""

import pytest

from logsift.core.context import ContextExtractor

# Initialization Tests


def test_context_extractor_initialization():
    """Test that context extractor can be initialized."""
    extractor = ContextExtractor()
    assert extractor is not None
    assert extractor.context_lines == 2


def test_context_extractor_custom_context_lines():
    """Test initialization with custom context lines."""
    extractor = ContextExtractor(context_lines=5)
    assert extractor.context_lines == 5


# Basic Context Extraction Tests


def test_extract_context_basic():
    """Test extracting basic context around an error."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'Line 2', 'line_number': 2},
        {'message': 'ERROR: Something failed', 'line_number': 3},
        {'message': 'Line 4', 'line_number': 4},
        {'message': 'Line 5', 'line_number': 5},
    ]
    extractor = ContextExtractor(context_lines=2)
    context = extractor.extract_context(log_entries, error_index=2)

    assert context is not None
    assert 'context_before' in context
    assert 'context_after' in context
    assert len(context['context_before']) == 2
    assert len(context['context_after']) == 2
    assert context['context_before'][0]['message'] == 'Line 1'
    assert context['context_before'][1]['message'] == 'Line 2'
    assert context['context_after'][0]['message'] == 'Line 4'
    assert context['context_after'][1]['message'] == 'Line 5'


def test_extract_context_at_beginning():
    """Test extracting context when error is at the beginning."""
    log_entries = [
        {'message': 'ERROR: Something failed', 'line_number': 1},
        {'message': 'Line 2', 'line_number': 2},
        {'message': 'Line 3', 'line_number': 3},
    ]
    extractor = ContextExtractor(context_lines=2)
    context = extractor.extract_context(log_entries, error_index=0)

    assert context is not None
    assert len(context['context_before']) == 0
    assert len(context['context_after']) == 2
    assert context['context_after'][0]['message'] == 'Line 2'
    assert context['context_after'][1]['message'] == 'Line 3'


def test_extract_context_at_end():
    """Test extracting context when error is at the end."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'Line 2', 'line_number': 2},
        {'message': 'ERROR: Something failed', 'line_number': 3},
    ]
    extractor = ContextExtractor(context_lines=2)
    context = extractor.extract_context(log_entries, error_index=2)

    assert context is not None
    assert len(context['context_before']) == 2
    assert len(context['context_after']) == 0
    assert context['context_before'][0]['message'] == 'Line 1'
    assert context['context_before'][1]['message'] == 'Line 2'


def test_extract_context_single_line_before():
    """Test extracting context when only one line before error."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'ERROR: Something failed', 'line_number': 2},
        {'message': 'Line 3', 'line_number': 3},
        {'message': 'Line 4', 'line_number': 4},
    ]
    extractor = ContextExtractor(context_lines=2)
    context = extractor.extract_context(log_entries, error_index=1)

    assert len(context['context_before']) == 1
    assert len(context['context_after']) == 2
    assert context['context_before'][0]['message'] == 'Line 1'


def test_extract_context_single_line_after():
    """Test extracting context when only one line after error."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'Line 2', 'line_number': 2},
        {'message': 'ERROR: Something failed', 'line_number': 3},
        {'message': 'Line 4', 'line_number': 4},
    ]
    extractor = ContextExtractor(context_lines=2)
    context = extractor.extract_context(log_entries, error_index=2)

    assert len(context['context_before']) == 2
    assert len(context['context_after']) == 1
    assert context['context_after'][0]['message'] == 'Line 4'


# Variable Context Lines Tests


def test_extract_context_with_larger_context():
    """Test extracting more context lines."""
    log_entries = [{'message': f'Line {i}', 'line_number': i} for i in range(1, 12)]
    extractor = ContextExtractor(context_lines=5)
    context = extractor.extract_context(log_entries, error_index=5)

    assert len(context['context_before']) == 5
    assert len(context['context_after']) == 5
    assert context['context_before'][0]['message'] == 'Line 1'
    assert context['context_after'][4]['message'] == 'Line 11'


def test_extract_context_zero_lines():
    """Test extracting with zero context lines."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'ERROR: Something failed', 'line_number': 2},
        {'message': 'Line 3', 'line_number': 3},
    ]
    extractor = ContextExtractor(context_lines=0)
    context = extractor.extract_context(log_entries, error_index=1)

    assert len(context['context_before']) == 0
    assert len(context['context_after']) == 0


def test_extract_context_one_line():
    """Test extracting with one context line."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'Line 2', 'line_number': 2},
        {'message': 'ERROR: Something failed', 'line_number': 3},
        {'message': 'Line 4', 'line_number': 4},
        {'message': 'Line 5', 'line_number': 5},
    ]
    extractor = ContextExtractor(context_lines=1)
    context = extractor.extract_context(log_entries, error_index=2)

    assert len(context['context_before']) == 1
    assert len(context['context_after']) == 1
    assert context['context_before'][0]['message'] == 'Line 2'
    assert context['context_after'][0]['message'] == 'Line 4'


# Edge Cases


def test_extract_context_single_entry():
    """Test extracting context when there's only the error entry."""
    log_entries = [
        {'message': 'ERROR: Something failed', 'line_number': 1},
    ]
    extractor = ContextExtractor(context_lines=2)
    context = extractor.extract_context(log_entries, error_index=0)

    assert len(context['context_before']) == 0
    assert len(context['context_after']) == 0


def test_extract_context_invalid_index_negative():
    """Test handling negative error index."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'Line 2', 'line_number': 2},
    ]
    extractor = ContextExtractor(context_lines=2)

    with pytest.raises((IndexError, ValueError)):
        extractor.extract_context(log_entries, error_index=-1)


def test_extract_context_invalid_index_out_of_bounds():
    """Test handling out of bounds error index."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'Line 2', 'line_number': 2},
    ]
    extractor = ContextExtractor(context_lines=2)

    with pytest.raises((IndexError, ValueError)):
        extractor.extract_context(log_entries, error_index=10)


def test_extract_context_empty_log_entries():
    """Test handling empty log entries list."""
    log_entries = []
    extractor = ContextExtractor(context_lines=2)

    with pytest.raises((IndexError, ValueError)):
        extractor.extract_context(log_entries, error_index=0)


# Field Preservation Tests


def test_extract_context_preserves_all_fields():
    """Test that context extraction preserves all fields from log entries."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1, 'level': 'INFO', 'timestamp': '2025-11-28T10:00:00Z'},
        {'message': 'ERROR: Failed', 'line_number': 2, 'level': 'ERROR', 'timestamp': '2025-11-28T10:00:01Z'},
        {'message': 'Line 3', 'line_number': 3, 'level': 'INFO', 'timestamp': '2025-11-28T10:00:02Z'},
    ]
    extractor = ContextExtractor(context_lines=1)
    context = extractor.extract_context(log_entries, error_index=1)

    assert context['context_before'][0]['level'] == 'INFO'
    assert context['context_before'][0]['timestamp'] == '2025-11-28T10:00:00Z'
    assert context['context_after'][0]['level'] == 'INFO'
    assert context['context_after'][0]['timestamp'] == '2025-11-28T10:00:02Z'


# Integration Tests


def test_extract_context_realistic_scenario():
    """Test context extraction with realistic log scenario."""
    log_entries = [
        {'message': 'Starting application', 'line_number': 1, 'level': 'INFO'},
        {'message': 'Loading configuration', 'line_number': 2, 'level': 'INFO'},
        {'message': 'Connecting to database', 'line_number': 3, 'level': 'INFO'},
        {'message': 'Database connected successfully', 'line_number': 4, 'level': 'INFO'},
        {'message': 'Starting web server', 'line_number': 5, 'level': 'INFO'},
        {'message': 'ERROR: Port 8080 already in use', 'line_number': 6, 'level': 'ERROR'},
        {'message': 'Failed to start web server', 'line_number': 7, 'level': 'ERROR'},
        {'message': 'Application shutdown initiated', 'line_number': 8, 'level': 'INFO'},
    ]
    extractor = ContextExtractor(context_lines=2)
    context = extractor.extract_context(log_entries, error_index=5)

    # Should get 2 lines before and 2 lines after the error
    assert len(context['context_before']) == 2
    assert len(context['context_after']) == 2
    assert context['context_before'][0]['message'] == 'Database connected successfully'
    assert context['context_before'][1]['message'] == 'Starting web server'
    assert context['context_after'][0]['message'] == 'Failed to start web server'
    assert context['context_after'][1]['message'] == 'Application shutdown initiated'


def test_extract_context_multiple_errors():
    """Test extracting context for multiple errors independently."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'ERROR: First error', 'line_number': 2},
        {'message': 'Line 3', 'line_number': 3},
        {'message': 'Line 4', 'line_number': 4},
        {'message': 'ERROR: Second error', 'line_number': 5},
        {'message': 'Line 6', 'line_number': 6},
    ]
    extractor = ContextExtractor(context_lines=1)

    # Extract context for first error
    context1 = extractor.extract_context(log_entries, error_index=1)
    assert context1['context_before'][0]['message'] == 'Line 1'
    assert context1['context_after'][0]['message'] == 'Line 3'

    # Extract context for second error
    context2 = extractor.extract_context(log_entries, error_index=4)
    assert context2['context_before'][0]['message'] == 'Line 4'
    assert context2['context_after'][0]['message'] == 'Line 6'
