"""Unit tests for the parser module."""

import pytest

from logsift.core.parser import LogParser


def test_parser_initialization():
    """Test that parser can be initialized."""
    parser = LogParser()
    assert parser is not None


def test_parser_parse_not_implemented():
    """Test that parse method raises NotImplementedError."""
    parser = LogParser()
    with pytest.raises(NotImplementedError):
        parser.parse('test log content')


def test_parser_detect_format_not_implemented():
    """Test that detect_format method raises NotImplementedError."""
    parser = LogParser()
    with pytest.raises(NotImplementedError):
        parser.detect_format('test log content')
