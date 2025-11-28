"""Unit tests for the analyzer module."""

import pytest

from logsift.core.analyzer import Analyzer


def test_analyzer_initialization():
    """Test that analyzer can be initialized."""
    analyzer = Analyzer()
    assert analyzer is not None


def test_analyzer_analyze_not_implemented():
    """Test that analyze method raises NotImplementedError."""
    analyzer = Analyzer()
    with pytest.raises(NotImplementedError):
        analyzer.analyze('test log content')
