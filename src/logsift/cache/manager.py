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

        # New directory structure: raw/, json/, toon/, md/
        self.raw_dir = self.cache_dir / 'raw'
        self.json_dir = self.cache_dir / 'json'
        self.toon_dir = self.cache_dir / 'toon'
        self.md_dir = self.cache_dir / 'md'

        # Legacy directories for migration
        self.logs_dir = self.cache_dir / 'logs'
        self.analyzed_dir = self.cache_dir / 'analyzed'

        # Create new subdirectories
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.json_dir.mkdir(parents=True, exist_ok=True)
        self.toon_dir.mkdir(parents=True, exist_ok=True)
        self.md_dir.mkdir(parents=True, exist_ok=True)

        # Migrate from old structure if needed
        self._migrate_to_new_structure()

    def create_paths(self, name: str) -> dict[str, Path]:
        """Create paths for all output formats.

        Args:
            name: Name for this log session

        Returns:
            Dictionary with keys: 'raw', 'json', 'toon', 'md' and Path values
        """
        # Sanitize name (replace slashes with dashes, other invalid chars with underscores)
        sanitized_name = name.lstrip('/')
        sanitized_name = sanitized_name.replace('/', '-')
        sanitized_name = re.sub(r'[^\w\-.]', '_', sanitized_name)

        # Create ISO8601 timestamp (prefix)
        timestamp = datetime.now(tz=UTC).strftime('%Y-%m-%dT%H:%M:%S')

        # Build filename stem (same across all formats)
        stem = f'{timestamp}-{sanitized_name}'

        # Return paths for all 4 formats
        return {
            'raw': self.raw_dir / f'{stem}.log',
            'json': self.json_dir / f'{stem}.json',
            'toon': self.toon_dir / f'{stem}.toon',
            'md': self.md_dir / f'{stem}.md',
        }

    def get_all_formats(self, stem: str) -> dict[str, Path | None]:
        """Find all format files for a given timestamp-name stem.

        Args:
            stem: The timestamp-name stem (e.g., "2025-01-15T10:30:00-install-deps")

        Returns:
            Dictionary with keys: 'raw', 'json', 'toon', 'md' and Path or None values
        """
        return {
            'raw': self._find_file(self.raw_dir, stem, '.log'),
            'json': self._find_file(self.json_dir, stem, '.json'),
            'toon': self._find_file(self.toon_dir, stem, '.toon'),
            'md': self._find_file(self.md_dir, stem, '.md'),
        }

    def _find_file(self, directory: Path, stem: str, extension: str) -> Path | None:
        """Find a file with given stem and extension in a directory.

        Args:
            directory: Directory to search
            stem: Filename stem
            extension: File extension (including dot)

        Returns:
            Path to file or None if not found
        """
        target = directory / f'{stem}{extension}'
        return target if target.exists() else None

    def create_log_path(self, name: str) -> Path:
        """Create a path for a new raw log file.

        Deprecated: Use create_paths() instead for new code.
        This method is kept for backward compatibility.

        Args:
            name: Name for this log

        Returns:
            Path to the raw log file
        """
        return self.create_paths(name)['raw']

    def get_latest_log(self, name: str) -> Path | None:
        """Get the latest raw log file for a given name.

        Args:
            name: Name of the log

        Returns:
            Path to latest raw log file or None if not found
        """
        return self._get_latest_in_dir(self.raw_dir, name, '.log')

    def get_absolute_latest_log(self) -> Path | None:
        """Get the absolute latest raw log file across all logs.

        Returns:
            Path to the most recent raw log file, or None if no logs exist
        """
        return self._get_absolute_latest_in_dir(self.raw_dir, '.log')

    def list_all_logs(self) -> list[dict[str, str | int]]:
        """List all cached raw log files with metadata.

        Returns:
            List of dictionaries with log file metadata
        """
        return self._list_all_in_dir(self.raw_dir, '.log')

    def get_latest_analyzed(self, name: str) -> Path | None:
        """Get the latest JSON analyzed result for a given name.

        Args:
            name: Name of the analyzed result

        Returns:
            Path to latest JSON analyzed result or None if not found
        """
        return self._get_latest_in_dir(self.json_dir, name, '.json')

    def get_absolute_latest_analyzed(self) -> Path | None:
        """Get the absolute latest JSON analyzed result across all analyses.

        Returns:
            Path to the most recent JSON analyzed result, or None if none exist
        """
        return self._get_absolute_latest_in_dir(self.json_dir, '.json')

    def list_all_analyzed(self) -> list[dict[str, str | int]]:
        """List all JSON analyzed results with metadata.

        Returns:
            List of dictionaries with analyzed result metadata
        """
        return self._list_all_in_dir(self.json_dir, '.json')

    def list_all_in_format(self, format_name: str) -> list[dict[str, str | int]]:
        """List all files in a specific format directory.

        Args:
            format_name: Format name ('raw', 'json', 'toon', or 'md')

        Returns:
            List of dictionaries with file metadata
        """
        dir_map = {
            'raw': (self.raw_dir, '.log'),
            'json': (self.json_dir, '.json'),
            'toon': (self.toon_dir, '.toon'),
            'md': (self.md_dir, '.md'),
        }

        if format_name not in dir_map:
            msg = f'Invalid format: {format_name}. Must be one of: {", ".join(dir_map.keys())}'
            raise ValueError(msg)

        directory, extension = dir_map[format_name]
        return self._list_all_in_dir(directory, extension)

    def _get_latest_in_dir(self, directory: Path, name: str, extension: str) -> Path | None:
        """Get the latest file in a directory matching name and extension.

        Args:
            directory: Directory to search
            name: Name pattern to match
            extension: File extension

        Returns:
            Path to latest matching file or None
        """
        # Sanitize inputs the same way as create_paths
        sanitized_name = name.lstrip('/')
        sanitized_name = sanitized_name.replace('/', '-')
        sanitized_name = re.sub(r'[^\w\-.]', '_', sanitized_name)

        if not directory.exists():
            return None

        # Find all files matching the name pattern (substring match)
        pattern = f'*{sanitized_name}*{extension}'
        matching_files = sorted(directory.glob(pattern))

        if not matching_files:
            return None

        # Return the last one (most recent due to ISO8601 timestamp sorting)
        return matching_files[-1]

    def _get_absolute_latest_in_dir(self, directory: Path, extension: str) -> Path | None:
        """Get the absolute latest file in a directory with given extension.

        Args:
            directory: Directory to search
            extension: File extension

        Returns:
            Path to most recent file or None
        """
        if not directory.exists():
            return None

        # Get all files and sort by name (ISO8601 timestamp prefix)
        all_files = sorted(directory.glob(f'*{extension}'))

        if not all_files:
            return None

        # Return the most recent (last in sorted list)
        return all_files[-1]

    def _list_all_in_dir(self, directory: Path, extension: str) -> list[dict[str, str | int]]:
        """List all files in a directory with given extension.

        Args:
            directory: Directory to search
            extension: File extension

        Returns:
            List of file metadata dictionaries
        """
        results: list[dict[str, str | int]] = []

        if not directory.exists():
            return results

        # List all files with extension
        for file_path in sorted(directory.glob(f'*{extension}')):
            if file_path.is_file():
                stat = file_path.stat()
                results.append(
                    {
                        'path': str(file_path),
                        'name': file_path.name,
                        'context': '',
                        'size_bytes': stat.st_size,
                        'modified_timestamp': int(stat.st_mtime),
                        'modified_iso': datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                    }
                )

        # Sort by modification time (newest first)
        results.sort(key=itemgetter('modified_timestamp'), reverse=True)

        return results

    def _migrate_to_new_structure(self) -> None:
        """Migrate existing logs from old structure to new format-based structure.

        Old structure: logs/*.log, analyzed/*.json
        New structure: raw/*.log, json/*.json, toon/*.toon, md/*.md

        This is called automatically during __init__ to handle migration.
        """
        if not self.cache_dir.exists():
            return

        # Migrate logs/ → raw/
        if self.logs_dir.exists():
            old_logs = [f for f in self.logs_dir.glob('*.log') if f.is_file()]
            for old_log in old_logs:
                new_path = self.raw_dir / old_log.name
                if not new_path.exists():
                    old_log.rename(new_path)

            # Remove logs/ directory if empty
            if not list(self.logs_dir.iterdir()):
                self.logs_dir.rmdir()

        # Migrate analyzed/ → json/
        if self.analyzed_dir.exists():
            old_analyzed = [f for f in self.analyzed_dir.glob('*.json') if f.is_file()]
            for old_analyzed_file in old_analyzed:
                new_path = self.json_dir / old_analyzed_file.name
                if not new_path.exists():
                    old_analyzed_file.rename(new_path)

            # Remove analyzed/ directory if empty
            if not list(self.analyzed_dir.iterdir()):
                self.analyzed_dir.rmdir()

        # Migrate any .log files in root cache directory (very old structure)
        old_root_logs = [f for f in self.cache_dir.glob('*.log') if f.is_file()]
        for old_log in old_root_logs:
            new_path = self.raw_dir / old_log.name
            if not new_path.exists():
                old_log.rename(new_path)

    def create_analyzed_path(self, log_path: Path) -> Path:
        """Create a path for a JSON analyzed result based on a log file path.

        Deprecated: Use create_paths() instead for new code.
        This method is kept for backward compatibility.

        Args:
            log_path: Path to the log file

        Returns:
            Path to the JSON analyzed result file
        """
        # Get just the stem (filename without extension) and add .json
        analyzed_name = log_path.stem + '.json'
        return self.json_dir / analyzed_name
