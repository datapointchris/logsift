"""Tests for the bat display helpers' plain fallback."""

from io import StringIO

from logsift import process_runner
from logsift.utils.display import display_file_with_bat
from logsift.utils.display import display_with_bat


def bat_missing(*args, **kwargs):
    raise FileNotFoundError('bat')


def test_fallback_writes_to_injected_stream_when_bat_is_missing(monkeypatch, tmp_path):
    """Without bat, content and file text go to the stream the caller passes."""
    monkeypatch.setattr(process_runner, 'run', bat_missing)
    log_file = tmp_path / 'app.log'
    log_file.write_text('from file')

    stream = StringIO()
    display_with_bat('from content', stream=stream)
    display_file_with_bat(log_file, stream=stream)

    assert stream.getvalue().splitlines() == ['from content', 'from file']
