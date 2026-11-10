"""Tests for fzf integration utilities."""

from unittest.mock import MagicMock
from unittest.mock import patch

from logsift.utils.fzf import is_fzf_available
from logsift.utils.fzf import select_log_file


def test_is_fzf_available_when_installed():
    """Test fzf availability check when fzf is installed."""
    with patch('shutil.which', return_value='/usr/bin/fzf'):
        assert is_fzf_available() is True


def test_is_fzf_available_when_not_installed():
    """Test fzf availability check when fzf is not installed."""
    with patch('shutil.which', return_value=None):
        assert is_fzf_available() is False


def test_select_log_file_when_fzf_not_available():
    """Test select_log_file returns None when fzf is not available."""
    with patch('logsift.utils.fzf.is_fzf_available', return_value=False):
        result = select_log_file([], 'Test')
        assert result is None


def test_select_log_file_empty_list():
    """Test select_log_file with empty log list."""
    result = select_log_file([], 'Test')
    assert result is None


def test_select_log_file_user_cancels():
    """Test select_log_file when user cancels selection."""
    logs = [
        {
            'context': 'monitor',
            'name': 'test-20240101_120000_000000',
            'path': '/path/to/test.log',
            'size_bytes': 1024,
            'modified_iso': '2024-01-01T12:00:00',
        }
    ]

    mock_result = MagicMock()
    mock_result.returncode = 1  # User cancelled
    mock_result.stdout = ''

    with patch('logsift.utils.fzf.is_fzf_available', return_value=True), patch('subprocess.run', return_value=mock_result):
        result = select_log_file(logs, 'Test')
        assert result is None


def test_select_log_file_success():
    """Test successful log file selection."""
    logs = [
        {
            'context': 'monitor',
            'name': 'test-20240101_120000_000000',
            'path': '/path/to/test.log',
            'size_bytes': 1024,
            'modified_iso': '2024-01-01T12:00:00',
        }
    ]

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = 'monitor/test-20240101_120000_000000 (1.0KB) - 2024-01-01|/path/to/test.log\n'

    with patch('logsift.utils.fzf.is_fzf_available', return_value=True), patch('subprocess.run', return_value=mock_result):
        result = select_log_file(logs, 'Test')
        assert result == '/path/to/test.log'
