"""Tests for desktop notifications."""

import subprocess

import pytest

from logsift import process_runner
from logsift.utils import notifications
from logsift.utils.notifications import notify_command_complete
from logsift.utils.notifications import send_notification


@pytest.fixture
def posted(monkeypatch):
    """Every notifier is installed, and each argv the runner is handed is recorded."""
    calls: list[list[str]] = []

    def record(argv, **kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(notifications.shutil, 'which', lambda program: f'/usr/bin/{program}')
    monkeypatch.setattr(process_runner, 'run', record)
    return calls


def test_macos_posts_through_osascript_with_quotes_escaped(posted):
    assert send_notification('Say "hi"', 'Got "it"', sound=True, platform='darwin') is True
    assert posted == [['osascript', '-e', 'display notification "Got \\"it\\"" with title "Say \\"hi\\"" sound name "default"']]


def test_linux_posts_through_notify_send(posted):
    assert send_notification('Title', 'Body', platform='linux') is True
    assert posted == [['notify-send', 'Title', 'Body']]


def test_no_notifier_posts_nothing(posted, monkeypatch):
    monkeypatch.setattr(notifications.shutil, 'which', lambda program: None)
    assert send_notification('Title', 'Body', platform='linux') is False
    assert send_notification('Title', 'Body', platform='win32') is False
    assert posted == []


def test_a_notifier_that_cannot_start_reports_failure(posted, monkeypatch):
    def vanished(argv, **kwargs):
        raise FileNotFoundError(argv[0])

    monkeypatch.setattr(process_runner, 'run', vanished)
    assert send_notification('Title', 'Body', platform='linux') is False


@pytest.mark.parametrize(
    ('errors', 'warnings', 'duration', 'body'),
    [
        (3, 5, 12.5, '3 errors, 5 warnings (12.5s)'),
        (1, 0, 0.5, '1 error'),
        (0, 0, 0, 'No issues found'),
    ],
)
def test_completion_names_the_command_and_counts(posted, errors, warnings, duration, body):
    notify_command_complete(
        'npm install', success=errors == 0, errors=errors, warnings=warnings, duration_seconds=duration, platform='linux'
    )
    status = '✓' if errors == 0 else '✗'
    assert posted == [['notify-send', f'logsift {status} npm install', body]]
