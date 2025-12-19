"""Tests for expanded pattern library.

These tests verify that additional patterns for shellcheck, ruff, and
other common pre-commit hooks correctly match real output.
"""

import re
import tomllib
from pathlib import Path


class TestSpecificShellcheckPatterns:
    """Test specific shellcheck patterns with actionable suggestions."""

    def test_sc2086_quoting_pattern(self):
        """Test SC2086 quoting pattern matches real output."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'shellcheck_sc2086_quoting'),
            None,
        )
        assert pattern is not None

        test_line = '    ^---^ SC2086 (info): Double quote to prevent globbing and word splitting.'
        match = re.search(pattern['regex'], test_line)
        assert match is not None

    def test_sc2155_declare_assign_pattern(self):
        """Test SC2155 declare/assign pattern."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'shellcheck_sc2155_declare_assign'),
            None,
        )
        assert pattern is not None

        test_line = 'SC2155 (warning): Declare and assign separately to avoid masking return values.'
        match = re.search(pattern['regex'], test_line)
        assert match is not None

    def test_sc2034_unused_var_pattern(self):
        """Test SC2034 unused variable pattern."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'shellcheck_sc2034_unused_var'),
            None,
        )
        assert pattern is not None

        test_line = 'SC2034 (warning): UNUSED_VAR appears unused. Verify use (or export if used externally).'
        match = re.search(pattern['regex'], test_line)
        assert match is not None


class TestSpecificRuffPatterns:
    """Test specific ruff patterns with actionable suggestions."""

    def test_f401_unused_import_pattern(self):
        """Test F401 unused import pattern."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'ruff_f401_unused_import'),
            None,
        )
        assert pattern is not None

        test_line = "src/main.py:10:1: F401 'sys' imported but unused"
        match = re.search(pattern['regex'], test_line)
        assert match is not None

    def test_e501_line_too_long_pattern(self):
        """Test E501 line too long pattern."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'ruff_e501_line_too_long'),
            None,
        )
        assert pattern is not None

        test_line = 'src/main.py:15:5: E501 line too long (120 > 88 characters)'
        match = re.search(pattern['regex'], test_line)
        assert match is not None

    def test_f841_unused_variable_pattern(self):
        """Test F841 unused variable pattern."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'ruff_f841_unused_variable'),
            None,
        )
        assert pattern is not None

        test_line = "src/utils.py:5:1: F841 local variable 'x' is assigned to but never used"
        match = re.search(pattern['regex'], test_line)
        assert match is not None


class TestPythonErrorPatterns:
    """Test Python error patterns."""

    def test_module_not_found_pattern(self):
        """Test ModuleNotFoundError pattern."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'module_not_found'),
            None,
        )
        assert pattern is not None

        test_line = "ModuleNotFoundError: No module named 'requests'"
        match = re.search(pattern['regex'], test_line)
        assert match is not None
        assert match.group(1) == 'requests'

    def test_syntax_error_pattern(self):
        """Test SyntaxError pattern."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'syntax_error_python'),
            None,
        )
        assert pattern is not None

        test_line = 'SyntaxError: invalid syntax'
        match = re.search(pattern['regex'], test_line)
        assert match is not None


class TestIntegrationWithAnalyzer:
    """Test that expanded patterns work with the analyzer."""

    def test_analyzer_detects_specific_shellcheck_issues(self):
        """Test analyzer detects specific shellcheck issues."""
        from logsift.core.analyzer import Analyzer

        log_content = """\
shellcheck...............................................................Failed
In script.sh line 5:
    ^---^ SC2086 (info): Double quote to prevent globbing and word splitting.
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        # Should detect the SC2086 warning
        sc_warning = next(
            (w for w in result['warnings'] if 'SC2086' in w.get('message', '')),
            None,
        )
        assert sc_warning is not None
        assert sc_warning.get('code') == 'SC2086'

    def test_analyzer_detects_specific_ruff_issues(self):
        """Test analyzer detects specific ruff issues."""
        from logsift.core.analyzer import Analyzer

        log_content = """\
ruff.....................................................................Failed
src/main.py:10:1: F401 'sys' imported but unused
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        # Should detect the F401 error
        f401_error = next(
            (e for e in result['errors'] if 'F401' in e.get('message', '')),
            None,
        )
        assert f401_error is not None
        assert f401_error.get('code') == 'F401'
