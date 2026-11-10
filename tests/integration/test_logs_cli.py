"""Integration tests for logs CLI commands."""

import json
import os
import time

from typer.testing import CliRunner

from logsift.cache.manager import SUFFIXES
from logsift.cache.manager import CacheManager
from logsift.cache.manager import SavedKind
from logsift.cli import app

runner = CliRunner()


class TestLogsListCommand:
    """Test the list commands every group shares."""

    def test_list_prints_newest_first_and_limit_keeps_the_newest(self):
        runner.invoke(app, ['monitor', '-n', 'older', '--format=json', '--', 'echo', 'one'])
        runner.invoke(app, ['monitor', '-n', 'newer', '--format=json', '--', 'echo', 'two'])

        listed = json.loads(runner.invoke(app, ['logs', 'list', '--format', 'json']).stdout)
        limited = json.loads(runner.invoke(app, ['raw', 'list', '-n', '1', '--format', 'json']).stdout)

        assert [row['name'][20:] for row in listed] == ['newer.log', 'older.log']
        assert limited == listed[:1]

    def test_an_empty_listing_prints_nothing_a_program_must_special_case(self):
        as_json = runner.invoke(app, ['analyzed', 'list', '--format', 'json'])
        as_plain = runner.invoke(app, ['logs', 'list', '--format', 'plain'])
        as_table = runner.invoke(app, ['logs', 'list'])

        assert json.loads(as_json.stdout) == []
        assert as_plain.stdout == ''
        assert as_table.stdout == ''


def make_saved_file(kind: SavedKind, stem: str, days_old: int):
    path = CacheManager().directory(kind) / f'{stem}{SUFFIXES[kind]}'
    path.write_text(stem)
    modified = time.time() - days_old * 24 * 60 * 60
    os.utime(path, (modified, modified))
    return path


class TestCleanCommands:
    """Test logs clean and analyzed clean."""

    def test_clean_deletes_only_its_own_kind_past_the_retention(self):
        old_log = make_saved_file(SavedKind.RAW, '2024-01-01T12:00:00-old', 60)
        recent_log = make_saved_file(SavedKind.RAW, '2024-01-01T12:00:00-recent', 20)
        old_analysis = make_saved_file(SavedKind.JSON, '2024-01-01T12:00:00-old', 60)

        logs_clean = runner.invoke(app, ['logs', 'clean', '--days', '30'])
        assert logs_clean.exit_code == 0
        assert [old_log.exists(), recent_log.exists(), old_analysis.exists()] == [False, True, True]

        analyzed_clean = runner.invoke(app, ['analyzed', 'clean', '--days', '30'])
        assert analyzed_clean.exit_code == 0
        assert not old_analysis.exists()

    def test_a_dry_run_names_each_file_it_would_delete_and_deletes_none(self):
        old_log = make_saved_file(SavedKind.RAW, '2024-01-01T12:00:00-old', 60)

        result = runner.invoke(app, ['logs', 'clean', '--days', '30', '--dry-run'])

        assert result.exit_code == 0
        assert str(old_log) in result.stdout
        assert old_log.exists()


def test_latest_for_a_name_no_run_has_is_an_error():
    result = runner.invoke(app, ['logs', 'latest', 'nonexistent-command-xyz'])

    assert result.exit_code == 1
    assert result.stdout == ''


def test_analyzed_latest_finds_by_name_an_analysis_of_a_file_outside_the_cache(tmp_path):
    """`logsift analyze scratch/deploy.log`, then `logsift json latest deploy`, as analyze's help suggests."""
    log_file = tmp_path / 'deploy.log'
    log_file.write_text('ERROR: boom\n')
    runner.invoke(app, ['analyze', str(log_file)])

    result = runner.invoke(app, ['json', 'latest', 'deploy'])

    assert result.exit_code == 0


class TestMonitorStreamFlags:
    """Test the monitor command --stream and --update-interval flags."""

    def test_monitor_with_stream_flag(self):
        """Test monitor with --stream flag for real-time output."""
        result = runner.invoke(app, ['monitor', '--stream', '--format=json', '--', 'echo', 'stream test'])

        assert result.exit_code == 0
        # Should have captured output and analysis
        data = json.loads(result.stdout)
        assert 'summary' in data

    def test_monitor_with_update_interval(self):
        """Test monitor with custom --update-interval."""
        result = runner.invoke(app, ['monitor', '--update-interval', '5', '--format=json', '--', 'echo', 'interval test'])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert 'summary' in data

    def test_monitor_default_periodic_updates(self):
        """Test monitor default behavior (periodic updates, not streaming)."""
        # Without --stream, should still work (periodic mode)
        result = runner.invoke(app, ['monitor', '--format=json', '--', 'echo', 'periodic test'])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert 'summary' in data

    def test_monitor_stream_with_interval(self):
        """Test monitor with both --stream and --update-interval."""
        result = runner.invoke(app, ['monitor', '--stream', '--update-interval', '10', '--format=json', '--', 'echo', 'both flags test'])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert 'summary' in data
