"""Unit tests for log file watching."""

import threading
import time

import pytest

from logsift.monitor.watcher import LogWatcher


def test_log_watcher_file_not_found(tmp_path):
    """Test that watcher raises error if file doesn't exist."""
    log_file = tmp_path / 'nonexistent.log'
    watcher = LogWatcher(log_file)

    with pytest.raises(FileNotFoundError, match='Log file not found'):
        watcher.watch(lambda lines: None)


def test_log_watcher_processes_new_lines(tmp_path):
    """Test that watcher processes newly added lines."""
    log_file = tmp_path / 'test.log'
    log_file.write_text('initial line\n')

    lines_received = []

    def callback(lines: list[str]) -> None:
        lines_received.extend(lines)
        # Stop once both new lines arrived
        if len(lines_received) >= 2:
            watcher.stop()

    watcher = LogWatcher(log_file, interval=0.1)

    # Start watching in a thread
    def watch_thread():
        watcher.watch(callback)

    thread = threading.Thread(target=watch_thread, daemon=True)
    thread.start()

    # Give watcher time to start
    time.sleep(0.2)

    # Append new lines
    with log_file.open('a') as f:
        f.write('new line 1\n')
        f.flush()
        time.sleep(0.15)
        f.write('new line 2\n')
        f.flush()

    # Wait for thread to process
    thread.join(timeout=2)

    # Should have received the new lines (not the initial line)
    assert 'new line 1' in lines_received
    assert 'new line 2' in lines_received


def test_log_watcher_stop(tmp_path):
    """Test stopping the watcher."""
    log_file = tmp_path / 'test.log'
    log_file.write_text('initial\n')

    watcher = LogWatcher(log_file, interval=0.1)
    lines: list[str] = []

    def watch_thread():
        watcher.watch(lines.extend)

    thread = threading.Thread(target=watch_thread, daemon=True)
    thread.start()

    time.sleep(0.2)

    # Stop watcher
    watcher.stop()

    # Wait for thread to finish
    thread.join(timeout=1)

    assert not thread.is_alive()


def test_log_watcher_batches_lines_without_newlines(tmp_path):
    """Lines appended together reach the callback as one batch, each without its trailing newline."""
    log_file = tmp_path / 'test.log'
    log_file.write_text('initial\n')

    batches: list[list[str]] = []

    def callback(lines: list[str]) -> None:
        batches.append(lines)
        watcher.stop()

    watcher = LogWatcher(log_file, interval=0.1)

    def watch_thread():
        watcher.watch(callback)

    thread = threading.Thread(target=watch_thread, daemon=True)
    thread.start()

    time.sleep(0.2)

    with log_file.open('a') as f:
        f.write('test line\nsecond line\n')
        f.flush()

    thread.join(timeout=1)

    assert batches == [['test line', 'second line']]
