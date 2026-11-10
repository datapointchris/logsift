"""The cache directory: each run's raw log and its saved analyses.

Every read, listing and deletion under the cache directory goes through CacheManager, so the name
rule, what counts as latest and what counts as stale are each defined once, here.
"""

import datetime as dt
import enum
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from logsift import xdg_dirs
from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown
from logsift.output.toon_formatter import format_toon

# A saved file's stem is its run's UTC start time in this format, a hyphen, then the run's name.
STAMP_FORMAT = '%Y-%m-%dT%H:%M:%S'
STAMP_LENGTH = len('2025-01-01T00:00:00')


class SavedKind(enum.StrEnum):
    """One kind of file a run saves, named as its directory under the cache."""

    RAW = 'raw'
    JSON = 'json'
    TOON = 'toon'
    MD = 'md'


SUFFIXES = {SavedKind.RAW: '.log', SavedKind.JSON: '.json', SavedKind.TOON: '.toon', SavedKind.MD: '.md'}
ANALYSIS_RENDERERS = {SavedKind.JSON: format_json, SavedKind.TOON: format_toon, SavedKind.MD: format_markdown}


def sanitize_name(name: str) -> str:
    """The run name as a file name carries it: slashes become hyphens, any other unsafe character an underscore."""
    return re.sub(r'[^\w\-.]', '_', name.lstrip('/').replace('/', '-'))


def run_name(path: Path) -> str:
    """The run name a saved file's stem carries after its start time."""
    return path.stem[STAMP_LENGTH + 1 :]


class CacheManager:
    """Every operation on the cache directory."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Use cache_dir, else $XDG_CACHE_HOME/logsift, else ~/.cache/logsift, creating a directory per kind."""
        self.cache_dir = cache_dir or xdg_dirs.cache_dir()
        for kind in SavedKind:
            self.directory(kind).mkdir(parents=True, exist_ok=True)

    def directory(self, kind: SavedKind) -> Path:
        return self.cache_dir / kind

    def create_paths(self, name: str) -> dict[SavedKind, Path]:
        """One path per kind for a run starting now, all sharing one stem."""
        stem = f'{dt.datetime.now(tz=dt.UTC).strftime(STAMP_FORMAT)}-{sanitize_name(name)}'
        return {kind: self.directory(kind) / f'{stem}{SUFFIXES[kind]}' for kind in SavedKind}

    def save_analysis(self, analysis: dict[str, Any], stem: str) -> list[str]:
        """Write the analysis under stem as each analysis kind.

        Returns:
            One line per file that could not be written, naming it and the reason
        """
        failures = []
        for kind, render in ANALYSIS_RENDERERS.items():
            path = self.directory(kind) / f'{stem}{SUFFIXES[kind]}'
            try:
                path.write_text(render(analysis), encoding='utf-8')
            except OSError as fault:
                failures.append(f'{path}: {fault.strerror or fault}')
        return failures

    def files(self, kind: SavedKind) -> list[Path]:
        """Every saved file of kind, newest first: by modification time, then by name."""
        found = [path for path in self.directory(kind).glob(f'*{SUFFIXES[kind]}') if path.is_file()]
        return sorted(found, key=lambda path: (path.stat().st_mtime, path.name), reverse=True)

    def listing(self, kind: SavedKind) -> list[dict[str, str | int]]:
        """Each saved file of kind with its size and modification time, newest first."""
        rows: list[dict[str, str | int]] = []
        for path in self.files(kind):
            stat = path.stat()
            rows.append(
                {
                    'path': str(path),
                    'name': path.name,
                    'context': '',
                    'size_bytes': stat.st_size,
                    'modified_timestamp': int(stat.st_mtime),
                    'modified_iso': dt.datetime.fromtimestamp(stat.st_mtime, tz=dt.UTC).isoformat(),
                }
            )
        return rows

    def latest(self, kind: SavedKind, name: str | None = None) -> Path | None:
        """The newest file of kind, or the newest whose run name contains name."""
        wanted = sanitize_name(name) if name else ''
        return next((path for path in self.files(kind) if wanted in run_name(path)), None)

    def latest_run(self, name: str) -> Path | None:
        """The newest raw log of the run named exactly name, which `monitor --append` adds to."""
        wanted = sanitize_name(name)
        return next((path for path in self.files(SavedKind.RAW) if run_name(path) == wanted), None)

    def stale(self, kinds: Iterable[SavedKind], days: int) -> list[Path]:
        """Every file of kinds last modified more than days ago."""
        cutoff = (dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=days)).timestamp()
        return [path for kind in kinds for path in self.files(kind) if path.stat().st_mtime < cutoff]

    def delete(self, paths: Iterable[Path]) -> list[str]:
        """Delete each path.

        Returns:
            One line per file that could not be deleted, naming it and the reason
        """
        failures = []
        for path in paths:
            try:
                path.unlink()
            except OSError as fault:
                failures.append(f'{path}: {fault.strerror or fault}')
        return failures
