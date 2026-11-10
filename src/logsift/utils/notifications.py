"""Desktop notifications, through the notifier NOTIFIERS names for the platform."""

import shutil
import sys

from logsift import process_runner

# The program that posts a notification on each platform logsift supports.
NOTIFIERS = {'darwin': 'osascript', 'linux': 'notify-send'}


def notifier_for(platform: str) -> str | None:
    """Return the platform's notifier where it is installed, else None."""
    program = NOTIFIERS.get(platform)
    return program if program and shutil.which(program) else None


def send_notification(title: str, message: str, sound: bool = True, platform: str = sys.platform) -> bool:
    """Post a desktop notification, and return whether the notifier accepted it.

    Args:
        title: Notification title
        message: Notification message body
        sound: Whether to play a sound (macOS only)
        platform: The `sys.platform` value to post for
    """
    program = notifier_for(platform)
    if program is None:
        return False
    if program == 'osascript':
        argv = ['osascript', '-e', applescript_notification(title, message, sound)]
    else:
        argv = ['notify-send', title, message]
    try:
        return process_runner.run(argv, capture=True).returncode == 0
    except OSError:
        return False


def applescript_notification(title: str, message: str, sound: bool) -> str:
    """The AppleScript statement that posts title and message, quotes escaped."""
    title = title.replace('"', '\\"')
    message = message.replace('"', '\\"')
    sound_clause = ' sound name "default"' if sound else ''
    return f'display notification "{message}" with title "{title}"{sound_clause}'


def notify_command_complete(
    command: str,
    success: bool,
    errors: int = 0,
    warnings: int = 0,
    duration_seconds: float = 0,
    platform: str = sys.platform,
) -> bool:
    """Post a notification naming the command, its outcome and what the analysis found.

    Returns:
        True if the notifier accepted it
    """
    status = '✓' if success else '✗'
    title = f'logsift {status} {command}'

    parts = []
    if errors > 0:
        parts.append(f'{errors} error{"s" if errors != 1 else ""}')
    if warnings > 0:
        parts.append(f'{warnings} warning{"s" if warnings != 1 else ""}')
    message = ', '.join(parts) if parts else 'No issues found'

    if duration_seconds >= 1:
        message += f' ({duration_seconds:.1f}s)'

    return send_notification(title, message, sound=not success, platform=platform)
