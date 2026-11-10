"""Tests for how the cache names a run's files and which one `latest` finds."""

import os

from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind


def test_a_runs_files_share_one_stem_carrying_its_sanitized_name(tmp_path):
    paths = CacheManager(cache_dir=tmp_path).create_paths('/usr/bin/make build')

    assert {path.stem for path in paths.values()} == {paths[SavedKind.RAW].stem}
    assert paths[SavedKind.RAW].stem.endswith('-usr-bin-make_build')
    assert [path.suffix for path in paths.values()] == ['.log', '.json', '.toon', '.md']


def test_latest_is_the_newest_write_and_matches_on_the_run_name(tmp_path):
    cache = CacheManager(cache_dir=tmp_path)
    raw = cache.directory(SavedKind.RAW)
    for age, stem in enumerate(('2025-02-01T00:00:00-build', '2025-01-01T00:00:00-test', '2025-03-01T00:00:00-build')):
        path = raw / f'{stem}.log'
        path.write_text(stem)
        os.utime(path, (1_000_000 - age, 1_000_000 - age))

    assert cache.latest(SavedKind.RAW) == raw / '2025-02-01T00:00:00-build.log'
    assert cache.latest(SavedKind.RAW, 'test') == raw / '2025-01-01T00:00:00-test.log'
    assert cache.latest(SavedKind.RAW, '2025') is None
