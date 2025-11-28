"""Cross-platform desktop notifications.

Provides notification support for macOS and Linux systems.
"""

import subprocess  # nosec B404
import sys


def is_notification_available() -> bool:
    """Check if notification support is available on this system.

    Returns:
        True if notifications are supported, False otherwise
    """
    if sys.platform == 'darwin':
        # macOS - osascript is always available
        return True
    elif sys.platform == 'linux':
        # Linux - check for notify-send
        try:
            subprocess.run(  # nosec B603 B607
                ['which', 'notify-send'],
                capture_output=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    else:
        # Unsupported platform
        return False


def send_notification(
    title: str,
    message: str,
    sound: bool = True,
) -> bool:
    """Send a desktop notification.

    Args:
        title: Notification title
        message: Notification message body
        sound: Whether to play a sound (macOS only)

    Returns:
        True if notification was sent successfully, False otherwise

    Example:
        send_notification(
            title='Build Complete',
            message='Build succeeded with 2 warnings',
            sound=True
        )
    """
    if not is_notification_available():
        return False

    try:
        if sys.platform == 'darwin':
            return _send_macos_notification(title, message, sound)
        elif sys.platform == 'linux':
            return _send_linux_notification(title, message)
        else:
            return False
    except Exception:
        # Silently fail - notifications are not critical
        return False


def _send_macos_notification(title: str, message: str, sound: bool) -> bool:
    """Send notification on macOS using osascript.

    Args:
        title: Notification title
        message: Notification message
        sound: Whether to play a sound

    Returns:
        True if successful
    """
    # Escape quotes in title and message
    title = title.replace('"', '\\"')
    message = message.replace('"', '\\"')

    # Build AppleScript command
    sound_clause = 'sound name "default"' if sound else ''
    script = f'display notification "{message}" with title "{title}" {sound_clause}'

    result = subprocess.run(  # nosec B603 B607
        ['osascript', '-e', script],
        capture_output=True,
        text=True,
        check=False,
    )

    return result.returncode == 0


def _send_linux_notification(title: str, message: str) -> bool:
    """Send notification on Linux using notify-send.

    Args:
        title: Notification title
        message: Notification message

    Returns:
        True if successful
    """
    result = subprocess.run(  # nosec B603 B607
        ['notify-send', title, message],
        capture_output=True,
        check=False,
    )

    return result.returncode == 0


def notify_command_complete(
    command: str,
    success: bool,
    errors: int = 0,
    warnings: int = 0,
    duration_seconds: float = 0,
) -> bool:
    """Send notification about command completion.

    Args:
        command: The command that was run
        success: Whether the command succeeded
        errors: Number of errors found
        warnings: Number of warnings found
        duration_seconds: How long the command took

    Returns:
        True if notification was sent successfully

    Example:
        notify_command_complete(
            command='npm install',
            success=False,
            errors=3,
            warnings=5,
            duration_seconds=12.5
        )
    """
    # Build title
    status = '✓' if success else '✗'
    title = f'logsift {status} {command}'

    # Build message
    parts = []
    if errors > 0:
        parts.append(f'{errors} error{"s" if errors != 1 else ""}')
    if warnings > 0:
        parts.append(f'{warnings} warning{"s" if warnings != 1 else ""}')

    if not parts:
        message = 'No issues found'
    else:
        message = ', '.join(parts)

    # Add duration if significant (>1 second)
    if duration_seconds >= 1:
        message += f' ({duration_seconds:.1f}s)'

    return send_notification(title, message, sound=not success)
