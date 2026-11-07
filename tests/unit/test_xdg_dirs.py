"""Tests for XDG base directory resolution."""

from pathlib import Path

import pytest

from logsift import xdg_dirs


def test_dirs_follow_the_xdg_variables(monkeypatch, tmp_path):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'config'))
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))

    assert xdg_dirs.config_dir() == tmp_path / 'config' / 'logsift'
    assert xdg_dirs.cache_dir() == tmp_path / 'cache' / 'logsift'


@pytest.mark.parametrize('value', ['', 'relative/path'])
def test_dirs_fall_back_to_home_when_the_variable_is_unusable(monkeypatch, value):
    monkeypatch.setenv('XDG_CONFIG_HOME', value)
    monkeypatch.setenv('XDG_CACHE_HOME', value)

    assert xdg_dirs.config_dir() == Path.home() / '.config' / 'logsift'
    assert xdg_dirs.cache_dir() == Path.home() / '.cache' / 'logsift'
