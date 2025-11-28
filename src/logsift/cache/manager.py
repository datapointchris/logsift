"""Cache directory management.

Manages the ~/.cache/logsift directory structure and log file storage.
"""

import re
from datetime import UTC
from datetime import datetime
from pathlib import Path


class CacheManager:
    """Manage cache directory and log file storage."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize the cache manager.

        Args:
            cache_dir: Optional cache directory path (defaults to ~/.cache/logsift)
        """
        self.cache_dir = cache_dir or Path.home() / '.cache' / 'logsift'

    def create_log_path(self, name: str, context: str = 'default') -> Path:
        """Create a path for a new log file.

        Args:
            name: Name for this log
            context: Context/category for organization

        Returns:
            Path to the log file
        """
        # Sanitize name (replace invalid filesystem characters)
        sanitized_name = re.sub(r'[^\w\-_.]', '_', name)

        # Sanitize context (replace slashes and invalid chars)
        sanitized_context = re.sub(r'[^\w\-_.]', '_', context)

        # Create timestamp
        timestamp = datetime.now(tz=UTC).strftime('%Y%m%d_%H%M%S_%f')

        # Build path: cache_dir/context/name-timestamp.log
        log_dir = self.cache_dir / sanitized_context
        log_dir.mkdir(parents=True, exist_ok=True)

        log_path = log_dir / f'{sanitized_name}-{timestamp}.log'

        return log_path

    def get_latest_log(self, name: str, context: str = 'default') -> Path | None:
        """Get the latest log file for a given name.

        Args:
            name: Name of the log
            context: Context/category

        Returns:
            Path to latest log file or None if not found
        """
        # Sanitize inputs
        sanitized_name = re.sub(r'[^\w\-_.]', '_', name)
        sanitized_context = re.sub(r'[^\w\-_.]', '_', context)

        # Build log directory path
        log_dir = self.cache_dir / sanitized_context

        if not log_dir.exists():
            return None

        # Find all log files matching the name pattern
        pattern = f'{sanitized_name}-*.log'
        matching_logs = sorted(log_dir.glob(pattern))

        if not matching_logs:
            return None

        # Return the last one (most recent due to timestamp sorting)
        return matching_logs[-1]
