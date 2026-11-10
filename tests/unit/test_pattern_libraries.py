"""Tests for the shipped pattern libraries outside pre-commit.toml."""

import re


def test_bash_command_not_found_pattern(builtin_pattern):
    pattern = builtin_pattern('bash_command_not_found')

    assert re.search(pattern['regex'], 'bash: unzip: command not found')
