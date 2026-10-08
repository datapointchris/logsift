"""Unit tests for utility functions."""

import datetime as dt

from logsift.utils.timestamps import format_duration
from logsift.utils.timestamps import parse_timestamp


def test_parse_timestamp_iso_format():
    """Test parsing ISO format timestamps."""
    parsed = parse_timestamp('2025-11-27T14:30:22Z')
    assert parsed is not None
    assert isinstance(parsed, dt.datetime)


def test_parse_timestamp_invalid():
    """Test parsing invalid timestamp returns None."""
    parsed = parse_timestamp('not a timestamp')
    assert parsed is None


def test_format_duration_seconds():
    """Test formatting duration in seconds."""
    assert format_duration(45) == '45s'


def test_format_duration_minutes():
    """Test formatting duration in minutes."""
    assert format_duration(222) == '3m 42s'


def test_format_duration_hours():
    """Test formatting duration in hours."""
    assert format_duration(7320) == '2h 2m'
