"""Remote SSH monitoring (Phase 3).

Provides remote command execution and log streaming over SSH.
"""


class RemoteMonitor:
    """Monitor commands on remote systems via SSH."""

    def __init__(self, host: str, user: str) -> None:
        """Initialize the remote monitor.

        Args:
            host: Remote host address
            user: SSH username
        """
        self.host = host
        self.user = user

    def run_remote(self, command: list[str]) -> None:
        """Run a command on the remote system.

        Args:
            command: Command to run remotely
        """
        raise NotImplementedError('Remote monitoring not yet implemented (Phase 3)')
