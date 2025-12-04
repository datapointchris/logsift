"""Unit tests for the context extraction system."""

import pytest

from logsift.core.analyzer import Analyzer

# Initialization Tests


def test_analyzer_initialization():
    """Test that analyzer can be initialized with context lines."""
    analyzer = Analyzer()
    assert analyzer is not None
    assert analyzer.context_lines == 2


def test_analyzer_custom_context_lines():
    """Test initialization with custom context lines."""
    analyzer = Analyzer(context_lines=5)
    assert analyzer.context_lines == 5


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
    analyzer = Analyzer(context_lines=2)
    context = analyzer._extract_context(log_entries, error_index=2)

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
    analyzer = Analyzer(context_lines=2)
    context = analyzer._extract_context(log_entries, error_index=0)

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
    analyzer = Analyzer(context_lines=2)
    context = analyzer._extract_context(log_entries, error_index=2)

    assert context is not None
    assert len(context['context_before']) == 2
    assert len(context['context_after']) == 0
    assert context['context_before'][0]['message'] == 'Line 1'
    assert context['context_before'][1]['message'] == 'Line 2'


def test_extract_context_invalid_index_negative():
    """Test handling negative error index."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'Line 2', 'line_number': 2},
    ]
    analyzer = Analyzer(context_lines=2)

    with pytest.raises((IndexError, ValueError)):
        analyzer._extract_context(log_entries, error_index=-1)


def test_extract_context_invalid_index_out_of_bounds():
    """Test handling out of bounds error index."""
    log_entries = [
        {'message': 'Line 1', 'line_number': 1},
        {'message': 'Line 2', 'line_number': 2},
    ]
    analyzer = Analyzer(context_lines=2)

    with pytest.raises((IndexError, ValueError)):
        analyzer._extract_context(log_entries, error_index=10)


def test_extract_context_empty_log_entries():
    """Test handling empty log entries list."""
    log_entries = []
    analyzer = Analyzer(context_lines=2)

    with pytest.raises((IndexError, ValueError)):
        analyzer._extract_context(log_entries, error_index=0)
