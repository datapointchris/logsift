"""Tests for the bat display helpers' plain fallback."""

import subprocess
from io import StringIO

from logsift.utils.display import display_file_with_bat
from logsift.utils.display import display_with_bat


def _bat_missing(*args, **kwargs):
    raise FileNotFoundError('bat')


def test_fallback_writes_to_injected_stream_when_bat_is_missing(monkeypatch, tmp_path):
    """Without bat, content and file text go to the stream the caller passes."""
    monkeypatch.setattr(subprocess, 'run', _bat_missing)
    log_file = tmp_path / 'app.log'
    log_file.write_text('from file')

    stream = StringIO()
    display_with_bat('from content', stream=stream)
    display_file_with_bat(log_file, stream=stream)

    assert stream.getvalue().splitlines() == ['from content', 'from file']
