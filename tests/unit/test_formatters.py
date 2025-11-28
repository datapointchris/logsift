"""Unit tests for output formatters."""

import pytest

from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown
from logsift.output.plain_formatter import format_plain


def test_json_formatter_not_implemented():
    """Test that JSON formatter raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        format_json({'test': 'data'})


def test_markdown_formatter_not_implemented():
    """Test that markdown formatter raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        format_markdown({'test': 'data'})


def test_plain_formatter_not_implemented():
    """Test that plain formatter raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        format_plain({'test': 'data'})
