"""Cache directory management.

Manages the ~/.cache/logsift directory structure and log file storage.
"""

import re
from datetime import UTC
from datetime import datetime
from operator import itemgetter
from pathlib import Path


class CacheManager:
    """Manage cache directory and log file storage."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize the cache manager.

        Args:
            cache_dir: Optional cache directory path (defaults to ~/.cache/logsift)
        """
        self.cache_dir = cache_dir or Path.home() / '.cache' / 'logsift'
        self.logs_dir = self.cache_dir / 'logs'
        self.analyzed_dir = self.cache_dir / 'analyzed'

        # Create subdirectories
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.analyzed_dir.mkdir(parents=True, exist_ok=True)

        # Migrate existing logs from flat structure to logs/ subdirectory
        self._migrate_logs()

    def create_log_path(self, name: str) -> Path:
        """Create a path for a new log file.

        Args:
            name: Name for this log

        Returns:
            Path to the log file
        """
        # Sanitize name (replace slashes with dashes, other invalid chars with underscores)
        # Remove leading slash if present
        sanitized_name = name.lstrip('/')
        # Replace remaining slashes with dashes
        sanitized_name = sanitized_name.replace('/', '-')
        # Replace any other invalid filesystem characters with underscores
        sanitized_name = re.sub(r'[^\w\-.]', '_', sanitized_name)

        # Create ISO8601 timestamp (prefix)
        timestamp = datetime.now(tz=UTC).strftime('%Y-%m-%dT%H:%M:%S')

        # Build path: logs_dir/timestamp-name.log
        log_path = self.logs_dir / f'{timestamp}-{sanitized_name}.log'

        return log_path

    def get_latest_log(self, name: str) -> Path | None:
        """Get the latest log file for a given name.

        Args:
            name: Name of the log

        Returns:
            Path to latest log file or None if not found
        """
        # Sanitize inputs the same way as create_log_path
        sanitized_name = name.lstrip('/')
        sanitized_name = sanitized_name.replace('/', '-')
        sanitized_name = re.sub(r'[^\w\-.]', '_', sanitized_name)

        if not self.logs_dir.exists():
            return None

        # Find all log files matching the name pattern (substring match)
        pattern = f'*{sanitized_name}*.log'
        matching_logs = sorted(self.logs_dir.glob(pattern))

        if not matching_logs:
            return None

        # Return the last one (most recent due to ISO8601 timestamp sorting)
        return matching_logs[-1]

    def get_absolute_latest_log(self) -> Path | None:
        """Get the absolute latest log file across all logs.

        Returns:
            Path to the most recent log file, or None if no logs exist
        """
        if not self.logs_dir.exists():
            return None

        # Get all log files and sort by name (ISO8601 timestamp prefix)
        all_logs = sorted(self.logs_dir.glob('*.log'))

        if not all_logs:
            return None

        # Return the most recent (last in sorted list)
        return all_logs[-1]

    def list_all_logs(self) -> list[dict[str, str | int]]:
        """List all cached log files with metadata.

        Returns:
            List of dictionaries with log file metadata
        """
        results: list[dict[str, str | int]] = []

        if not self.logs_dir.exists():
            return results

        # List all log files in logs/ subdirectory
        for log_file in sorted(self.logs_dir.glob('*.log')):
            if log_file.is_file():
                stat = log_file.stat()
                results.append(
                    {
                        'path': str(log_file),
                        'name': log_file.stem,
                        'context': '',  # No context directories anymore
                        'size_bytes': stat.st_size,
                        'modified_timestamp': int(stat.st_mtime),
                        'modified_iso': datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                    }
                )

        # Sort by modification time (newest first)
        results.sort(key=itemgetter('modified_timestamp'), reverse=True)

        return results

    def _migrate_logs(self) -> None:
        """Migrate existing logs from flat structure to logs/ subdirectory.

        This is called automatically during __init__ to handle migration
        from the old flat directory structure to the new subdirectory structure.
        """
        if not self.cache_dir.exists():
            return

        # Find all .log files in the root cache directory (not in subdirectories)
        old_logs = [f for f in self.cache_dir.glob('*.log') if f.is_file()]

        if not old_logs:
            return

        # Move each log file to logs/ subdirectory
        for old_log in old_logs:
            new_path = self.logs_dir / old_log.name
            # Only move if target doesn't exist (avoid overwriting)
            if not new_path.exists():
                old_log.rename(new_path)

    def create_analyzed_path(self, log_path: Path) -> Path:
        """Create a path for an analyzed result based on a log file path.

        Args:
            log_path: Path to the log file

        Returns:
            Path to the analyzed result file (.json)
        """
        # Get just the stem (filename without extension) and add .json
        analyzed_name = log_path.stem + '.json'
        return self.analyzed_dir / analyzed_name

    def get_latest_analyzed(self, name: str) -> Path | None:
        """Get the latest analyzed result for a given name.

        Args:
            name: Name of the analyzed result

        Returns:
            Path to latest analyzed result or None if not found
        """
        # Sanitize inputs the same way as logs
        sanitized_name = name.lstrip('/')
        sanitized_name = sanitized_name.replace('/', '-')
        sanitized_name = re.sub(r'[^\w\-.]', '_', sanitized_name)

        if not self.analyzed_dir.exists():
            return None

        # Find all analyzed files matching the name pattern (substring match)
        pattern = f'*{sanitized_name}*.json'
        matching_analyzed = sorted(self.analyzed_dir.glob(pattern))

        if not matching_analyzed:
            return None

        # Return the last one (most recent due to ISO8601 timestamp sorting)
        return matching_analyzed[-1]

    def get_absolute_latest_analyzed(self) -> Path | None:
        """Get the absolute latest analyzed result across all analyses.

        Returns:
            Path to the most recent analyzed result, or None if none exist
        """
        if not self.analyzed_dir.exists():
            return None

        # Get all analyzed files and sort by name (ISO8601 timestamp prefix)
        all_analyzed = sorted(self.analyzed_dir.glob('*.json'))

        if not all_analyzed:
            return None

        # Return the most recent (last in sorted list)
        return all_analyzed[-1]

    def list_all_analyzed(self) -> list[dict[str, str | int]]:
        """List all analyzed results with metadata.

        Returns:
            List of dictionaries with analyzed result metadata
        """
        results: list[dict[str, str | int]] = []

        if not self.analyzed_dir.exists():
            return results

        # List all analyzed files in analyzed/ subdirectory
        for analyzed_file in sorted(self.analyzed_dir.glob('*.json')):
            if analyzed_file.is_file():
                stat = analyzed_file.stat()
                results.append(
                    {
                        'path': str(analyzed_file),
                        'name': analyzed_file.stem,
                        'context': '',
                        'size_bytes': stat.st_size,
                        'modified_timestamp': int(stat.st_mtime),
                        'modified_iso': datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                    }
                )

        # Sort by modification time (newest first)
        results.sort(key=itemgetter('modified_timestamp'), reverse=True)

        return results
