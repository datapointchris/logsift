"""Log rotation and cleanup.

Handles cleanup of old log files based on retention policies.
"""

from datetime import UTC
from datetime import datetime
from datetime import timedelta
from pathlib import Path


def clean_old_logs(cache_dir: Path, retention_days: int = 90) -> int:
    """Clean up log files older than retention period.

    Args:
        cache_dir: Cache directory path
        retention_days: Number of days to retain

    Returns:
        Number of files deleted
    """
    if not cache_dir.exists():
        return 0

    # Calculate cutoff time
    cutoff_time = datetime.now(tz=UTC) - timedelta(days=retention_days)
    cutoff_timestamp = cutoff_time.timestamp()

    deleted_count = 0

    # Recursively find all .log files
    for log_file in cache_dir.rglob('*.log'):
        if log_file.is_file():
            # Get file modification time
            mtime = log_file.stat().st_mtime

            # Delete if older than cutoff
            if mtime < cutoff_timestamp:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except OSError:
                    # Skip files we can't delete
                    continue

    return deleted_count
