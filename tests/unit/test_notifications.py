"""Tests for cross-platform notifications."""

import subprocess
from unittest.mock import MagicMock
from unittest.mock import patch

from logsift.utils.notifications import is_notification_available
from logsift.utils.notifications import notify_command_complete
from logsift.utils.notifications import send_notification


def test_is_notification_available_macos():
    """Test notification availability detection on macOS."""
    with patch('sys.platform', 'darwin'):
        assert is_notification_available() is True


def test_is_notification_available_linux_with_notify_send():
    """Test notification availability on Linux with notify-send installed."""
    with (
        patch('sys.platform', 'linux'),
        patch('subprocess.run') as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)
        assert is_notification_available() is True


def test_is_notification_available_linux_without_notify_send():
    """Test notification availability on Linux without notify-send."""
    with (
        patch('sys.platform', 'linux'),
        patch('subprocess.run', side_effect=subprocess.CalledProcessError(1, 'which')),
    ):
        assert is_notification_available() is False


def test_is_notification_available_unsupported_platform():
    """Test notification availability on unsupported platform."""
    with patch('sys.platform', 'win32'):
        assert is_notification_available() is False


def test_send_notification_macos():
    """Test sending notification on macOS."""
    with (
        patch('sys.platform', 'darwin'),
        patch('subprocess.run') as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        result = send_notification('Test Title', 'Test Message', sound=True)

        assert result is True
        mock_run.assert_called_once()

        # Check osascript was called
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'osascript'
        assert 'Test Title' in call_args[2]
        assert 'Test Message' in call_args[2]
        assert 'sound name' in call_args[2]


def test_send_notification_macos_no_sound():
    """Test sending notification on macOS without sound."""
    with (
        patch('sys.platform', 'darwin'),
        patch('subprocess.run') as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        result = send_notification('Test Title', 'Test Message', sound=False)

        assert result is True

        # Check sound is not in command
        call_args = mock_run.call_args[0][0]
        assert 'Test Title' in call_args[2]
        assert 'Test Message' in call_args[2]


def test_send_notification_linux():
    """Test sending notification on Linux."""
    with (
        patch('sys.platform', 'linux'),
        patch('subprocess.run') as mock_run,
    ):
        # First call for is_notification_available (which check)
        # Second call for actual notification
        mock_run.side_effect = [
            MagicMock(returncode=0),  # which notify-send
            MagicMock(returncode=0),  # notify-send
        ]

        result = send_notification('Test Title', 'Test Message')

        assert result is True

        # Check notify-send was called
        call_args = mock_run.call_args_list[1][0][0]
        assert call_args == ['notify-send', 'Test Title', 'Test Message']


def test_send_notification_escapes_quotes():
    """Test that quotes in title/message are properly escaped."""
    with (
        patch('sys.platform', 'darwin'),
        patch('subprocess.run') as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        send_notification('Test "Title"', 'Test "Message"', sound=False)

        # Check quotes are escaped
        call_args = mock_run.call_args[0][0]
        script = call_args[2]
        assert 'Test \\"Title\\"' in script
        assert 'Test \\"Message\\"' in script


def test_send_notification_unavailable():
    """Test sending notification on platform without support."""
    with patch('sys.platform', 'win32'):
        result = send_notification('Test', 'Message')
        assert result is False


def test_send_notification_fails_gracefully():
    """Test that notification failures are handled gracefully."""
    with (
        patch('sys.platform', 'darwin'),
        patch('subprocess.run', side_effect=Exception('Failed')),
    ):
        result = send_notification('Test', 'Message')
        assert result is False


def test_notify_command_complete_success():
    """Test notification for successful command."""
    with (
        patch('sys.platform', 'darwin'),
        patch('subprocess.run') as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        result = notify_command_complete(
            command='npm install',
            success=True,
            errors=0,
            warnings=0,
            duration_seconds=5.2,
        )

        assert result is True

        # Check notification content
        call_args = mock_run.call_args[0][0]
        script = call_args[2]
        assert 'npm install' in script
        assert 'No issues found' in script
        assert '5.2s' in script


def test_notify_command_complete_with_errors():
    """Test notification for command with errors."""
    with (
        patch('sys.platform', 'darwin'),
        patch('subprocess.run') as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        result = notify_command_complete(
            command='make build',
            success=False,
            errors=3,
            warnings=5,
            duration_seconds=12.8,
        )

        assert result is True

        # Check notification content
        call_args = mock_run.call_args[0][0]
        script = call_args[2]
        assert 'make build' in script
        assert '3 errors' in script
        assert '5 warnings' in script
        assert '12.8s' in script
        # Should have sound for failures
        assert 'sound name' in script


def test_notify_command_complete_singular_error():
    """Test notification uses singular form for single error/warning."""
    with (
        patch('sys.platform', 'darwin'),
        patch('subprocess.run') as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        notify_command_complete(
            command='test',
            success=False,
            errors=1,
            warnings=1,
        )

        # Check singular form
        call_args = mock_run.call_args[0][0]
        script = call_args[2]
        assert '1 error,' in script
        assert '1 warning' in script


def test_notify_command_complete_no_duration():
    """Test notification omits duration for quick commands."""
    with (
        patch('sys.platform', 'darwin'),
        patch('subprocess.run') as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        notify_command_complete(
            command='echo test',
            success=True,
            errors=0,
            warnings=0,
            duration_seconds=0.1,
        )

        # Duration should not be included
        call_args = mock_run.call_args[0][0]
        script = call_args[2]
        assert '0.1s' not in script


def test_notify_command_complete_warnings_only():
    """Test notification with only warnings."""
    with (
        patch('sys.platform', 'darwin'),
        patch('subprocess.run') as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0)

        notify_command_complete(
            command='lint',
            success=True,
            errors=0,
            warnings=2,
        )

        # Check only warnings shown
        call_args = mock_run.call_args[0][0]
        script = call_args[2]
        assert '2 warnings' in script
        assert 'error' not in script.lower()
