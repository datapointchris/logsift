"""Unit tests for the pattern system."""

import pytest

from logsift.patterns.loader import PatternLoader


def test_pattern_loader_initialization():
    """Test that pattern loader can be initialized."""
    loader = PatternLoader()
    assert loader is not None
    assert loader.patterns == {}


def test_pattern_loader_load_builtin_not_implemented():
    """Test that load_builtin_patterns raises NotImplementedError."""
    loader = PatternLoader()
    with pytest.raises(NotImplementedError):
        loader.load_builtin_patterns()
