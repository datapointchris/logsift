"""Tests for fzf integration utilities."""

import shutil
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from logsift.utils.fzf import browse_log_with_preview
from logsift.utils.fzf import is_fzf_available
from logsift.utils.fzf import search_in_logs
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


def test_select_log_file_formats_sizes_correctly():
    """Test that select_log_file formats file sizes correctly."""
    logs = [
        {'context': 'test', 'name': 'small', 'path': '/small.log', 'size_bytes': 500, 'modified_iso': '2024-01-01T12:00:00'},
        {'context': 'test', 'name': 'medium', 'path': '/medium.log', 'size_bytes': 5000, 'modified_iso': '2024-01-01T12:00:00'},
        {
            'context': 'test',
            'name': 'large',
            'path': '/large.log',
            'size_bytes': 5000000,
            'modified_iso': '2024-01-01T12:00:00',
        },
    ]

    with patch('logsift.utils.fzf.is_fzf_available', return_value=True), patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        select_log_file(logs, 'Test')

        # Check that subprocess.run was called with formatted entries
        call_args = mock_run.call_args
        input_text = call_args[1]['input']

        # Should contain formatted sizes
        assert '500B' in input_text
        assert 'KB' in input_text
        assert 'MB' in input_text


def test_browse_log_with_preview_when_fzf_not_available():
    """Test browse_log_with_preview returns False when fzf is not available."""
    with patch('logsift.utils.fzf.is_fzf_available', return_value=False):
        result = browse_log_with_preview(Path('/test.log'))
        assert result is False


def test_browse_log_with_preview_nonexistent_file():
    """Test browse_log_with_preview with non-existent file."""
    with patch('logsift.utils.fzf.is_fzf_available', return_value=True):
        result = browse_log_with_preview(Path('/nonexistent/file.log'))
        assert result is False


def test_browse_log_with_preview_success(tmp_path):
    """Test successful log browsing."""
    log_file = tmp_path / 'test.log'
    log_file.write_text('Line 1\nLine 2\nLine 3\n')

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch('logsift.utils.fzf.is_fzf_available', return_value=True), patch('subprocess.run', return_value=mock_result):
        result = browse_log_with_preview(log_file)
        assert result is True


def test_search_in_logs_when_fzf_not_available():
    """Test search_in_logs returns None when fzf is not available."""
    with patch('logsift.utils.fzf.is_fzf_available', return_value=False):
        result = search_in_logs([], 'error')
        assert result is None


def test_search_in_logs_empty_list():
    """Test search_in_logs with empty log list."""
    result = search_in_logs([], 'error')
    assert result is None


def test_search_in_logs_success(tmp_path):
    """Test successful log search."""
    log_file = tmp_path / 'test.log'
    log_file.write_text('INFO: Starting\nERROR: Failed\nINFO: Done\n')

    logs = [
        {
            'context': 'monitor',
            'name': 'test',
            'path': str(log_file),
            'size_bytes': 100,
            'modified_iso': '2024-01-01T12:00:00',
        }
    ]

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = 'test.log:2 | ERROR: Failed\n'

    with patch('logsift.utils.fzf.is_fzf_available', return_value=True), patch('subprocess.run', return_value=mock_result):
        result = search_in_logs(logs, 'error')
        assert result == 'test.log'


def test_search_in_logs_with_initial_query(tmp_path):
    """Test search_in_logs passes initial query to fzf."""
    log_file = tmp_path / 'test.log'
    log_file.write_text('Test content\n')

    logs = [{'context': 'test', 'name': 'test', 'path': str(log_file), 'size_bytes': 100, 'modified_iso': '2024-01-01T12:00:00'}]

    with patch('logsift.utils.fzf.is_fzf_available', return_value=True), patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        search_in_logs(logs, 'error')

        # Check that --query was passed
        call_args = mock_run.call_args[0][0]
        assert '--query' in call_args
        assert 'error' in call_args


def test_search_in_logs_skips_empty_lines(tmp_path):
    """Test that search_in_logs skips empty lines."""
    log_file = tmp_path / 'test.log'
    log_file.write_text('Line 1\n\n\nLine 2\n')

    logs = [{'context': 'test', 'name': 'test', 'path': str(log_file), 'size_bytes': 100, 'modified_iso': '2024-01-01T12:00:00'}]

    with patch('logsift.utils.fzf.is_fzf_available', return_value=True), patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        search_in_logs(logs, None)

        # Check input text doesn't have empty lines
        input_text = mock_run.call_args[1]['input']
        # Should have 2 non-empty lines
        assert input_text.count('\n') == 1  # 2 lines = 1 newline separator


def test_fzf_not_in_path():
    """Test behavior when fzf is truly not in PATH."""
    # This test uses the actual shutil.which function
    if shutil.which('nonexistent_command_12345') is not None:
        # Skip if somehow this command exists
        return

    # Test with a command that definitely doesn't exist
    with patch('shutil.which', return_value=None):
        assert is_fzf_available() is False
