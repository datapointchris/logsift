"""Live log file watching and tailing.

Monitors log files in real-time and provides live analysis.
"""

import os
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
        self._stop_requested = False

    def watch(self, callback: Callable[[str], None]) -> None:
        """Start watching the log file.

        Args:
            callback: Function to call for each new line

        Raises:
            FileNotFoundError: If log file doesn't exist
        """
        if not self.log_file.exists():
            raise FileNotFoundError(f'Log file not found: {self.log_file}')

        with self.log_file.open('r', encoding='utf-8') as f:
            f.seek(0, os.SEEK_END)

            while not self._stop_requested:
                line = f.readline()

                if line:
                    callback(line.rstrip('\n'))
                else:
                    time.sleep(self.interval)

    def stop(self) -> None:
        """Stop watching the log file."""
        self._stop_requested = True
