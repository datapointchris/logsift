"""Live log file watching and tailing.

Monitors log files in real-time and provides live analysis.
"""

import time
from collections.abc import Callable
from pathlib import Path


class LogWatcher:
    """Watch a log file in real-time."""

    def __init__(self, log_file: Path, interval: int = 1) -> None:
        """Initialize the log watcher.

        Args:
            log_file: Path to log file to watch
            interval: Update interval in seconds
        """
        self.log_file = log_file
        self.interval = interval
        self._stop = False

    def watch(self, callback: Callable[[str], None]) -> None:
        """Start watching the log file.

        Args:
            callback: Function to call for each new line

        Raises:
            FileNotFoundError: If log file doesn't exist
        """
        if not self.log_file.exists():
            raise FileNotFoundError(f'Log file not found: {self.log_file}')

        # Open file and seek to end
        with self.log_file.open('r', encoding='utf-8') as f:
            # Go to end of file
            f.seek(0, 2)

            while not self._stop:
                line = f.readline()

                if line:
                    # New line available - process it
                    callback(line.rstrip('\n'))
                else:
                    # No new data - wait before checking again
                    time.sleep(self.interval)

    def stop(self) -> None:
        """Stop watching the log file."""
        self._stop = True


def watch_file(
    file_path: Path,
    callback: Callable[[str], None],
    interval: int = 1,
) -> LogWatcher:
    """Watch a file and call callback for each new line.

    Args:
        file_path: Path to file to watch
        callback: Function to call with each new line
        interval: Check interval in seconds

    Returns:
        LogWatcher instance (already started)

    Example:
        def process_line(line: str) -> None:
            print(f"New line: {line}")

        watcher = watch_file(Path('/var/log/app.log'), process_line)
        # ... later ...
        watcher.stop()
    """
    watcher = LogWatcher(file_path, interval)
    watcher.watch(callback)
    return watcher


def tail_file(file_path: Path, num_lines: int = 10) -> list[str]:
    """Get the last N lines from a file (like tail -n).

    Args:
        file_path: Path to file
        num_lines: Number of lines to return

    Returns:
        List of last N lines

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f'File not found: {file_path}')

    lines = file_path.read_text(encoding='utf-8').splitlines()
    return lines[-num_lines:] if len(lines) > num_lines else lines
