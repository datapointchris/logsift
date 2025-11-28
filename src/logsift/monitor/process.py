"""Process monitoring using subprocess for clean command execution.

Provides wrappers around subprocess operations for monitoring commands.
"""

import subprocess  # nosec B404
import time
from typing import Any


class ProcessMonitor:
    """Monitor a running process and capture its output."""

    def __init__(self, command: list[str], timeout: int | None = None) -> None:
        """Initialize the process monitor.

        Args:
            command: Command to run as list of strings
            timeout: Optional timeout in seconds
        """
        self.command = command
        self.timeout = timeout

    def run(self) -> dict[str, Any]:
        """Run the command and capture output.

        Returns:
            Dictionary with command result, output, and exit code
        """
        start_time = time.time()

        try:
            result = subprocess.run(  # nosec B603
                self.command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            duration = time.time() - start_time

            # Combine stdout and stderr
            output = result.stdout
            if result.stderr:
                output += result.stderr

            return {
                'command': ' '.join(self.command),
                'exit_code': result.returncode,
                'success': result.returncode == 0,
                'output': output,
                'duration_seconds': duration,
            }

        except FileNotFoundError:
            # Command not found
            duration = time.time() - start_time
            return {
                'command': ' '.join(self.command),
                'exit_code': 127,  # Standard "command not found" exit code
                'success': False,
                'output': f'Command not found: {self.command[0]}',
                'duration_seconds': duration,
            }

        except subprocess.TimeoutExpired:
            # Command timed out
            duration = time.time() - start_time
            return {
                'command': ' '.join(self.command),
                'exit_code': 124,  # Standard timeout exit code
                'success': False,
                'output': f'Command timed out after {self.timeout} seconds',
                'duration_seconds': duration,
            }
