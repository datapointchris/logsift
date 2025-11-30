"""Tests for TTY detection."""

from unittest.mock import patch

from logsift.utils.tty import detect_output_format
from logsift.utils.tty import is_interactive


def test_is_interactive_when_tty():
    """Test is_interactive returns True when stdout is a TTY."""
    with patch('sys.stdout.isatty', return_value=True):
        assert is_interactive() is True


def test_is_interactive_when_not_tty():
    """Test is_interactive returns False when stdout is not a TTY."""
    with patch('sys.stdout.isatty', return_value=False):
        assert is_interactive() is False


def test_detect_output_format_interactive():
    """Test detect_output_format returns 'markdown' for interactive terminals."""
    with patch('sys.stdout.isatty', return_value=True):
        assert detect_output_format() == 'markdown'


def test_detect_output_format_headless():
    """Test detect_output_format returns 'toon' for headless/piped output."""
    with patch('sys.stdout.isatty', return_value=False):
        assert detect_output_format() == 'toon'


def test_is_interactive_direct_call():
    """Test is_interactive can be called without mocking (actual behavior)."""
    # This will return False in test environment (pytest captures stdout)
    result = is_interactive()
    assert isinstance(result, bool)


def test_detect_output_format_direct_call():
    """Test detect_output_format can be called without mocking (actual behavior)."""
    # This will return 'toon' in test environment (pytest captures stdout)
    result = detect_output_format()
    assert result in ('toon', 'markdown')
