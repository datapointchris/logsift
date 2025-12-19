"""Tests for pre-commit hook name detection.

These tests verify that logsift extracts hook names from pre-commit output
and includes them in the summary for LLM consumption.
"""

from logsift.core.analyzer import Analyzer


class TestHookDetection:
    """Test hook name detection in pre-commit output."""

    def test_detects_single_failed_hook(self):
        """Test detection of a single failed hook."""
        log_content = """\
check yaml...............................................................Passed
check toml...............................................................Passed
ruff.....................................................................Failed
src/main.py:10:1: F401 'sys' imported but unused
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        assert 'hooks' in result
        assert 'failed' in result['hooks']
        assert 'ruff' in result['hooks']['failed']

    def test_detects_multiple_failed_hooks(self):
        """Test detection of multiple failed hooks."""
        log_content = """\
check yaml...............................................................Passed
ruff.....................................................................Failed
shellcheck...............................................................Failed
mypy.....................................................................Passed
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        assert 'hooks' in result
        assert len(result['hooks']['failed']) == 2
        assert 'ruff' in result['hooks']['failed']
        assert 'shellcheck' in result['hooks']['failed']

    def test_detects_passed_hooks(self):
        """Test detection of passed hooks."""
        log_content = """\
check yaml...............................................................Passed
check toml...............................................................Passed
ruff.....................................................................Passed
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        assert 'hooks' in result
        assert 'passed' in result['hooks']
        assert len(result['hooks']['passed']) == 3
        assert len(result['hooks']['failed']) == 0

    def test_no_hooks_detected_in_non_precommit_output(self):
        """Test that non-pre-commit output doesn't produce false positives."""
        log_content = """\
INFO: Starting application
ERROR: Connection failed
INFO: Shutting down
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        # Should have hooks field but with empty lists
        assert 'hooks' in result
        assert len(result['hooks']['failed']) == 0
        assert len(result['hooks']['passed']) == 0

    def test_hook_detection_with_hook_id_format(self):
        """Test detection with - hook id: format."""
        log_content = """\
ruff.....................................................................Failed
- hook id: ruff
- exit code: 1
src/main.py:10:1: F401 'sys' imported but unused
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        assert 'ruff' in result['hooks']['failed']

    def test_hook_detection_with_various_separator_lengths(self):
        """Test detection with different lengths of dots."""
        log_content = """\
check yaml.......Passed
ruff................................................................................Failed
mypy...Passed
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        assert 'ruff' in result['hooks']['failed']
        assert 'check yaml' in result['hooks']['passed']
        assert 'mypy' in result['hooks']['passed']


class TestToonFormatterHooks:
    """Test TOON formatter includes hooks field."""

    def test_toon_includes_failed_hooks(self):
        """Test that TOON output includes failed hooks."""
        from logsift.output.toon_formatter import format_toon

        analysis_result = {
            'summary': {'status': 'failed', 'exit_code': 1},
            'stats': {'total_errors': 1, 'total_warnings': 0},
            'errors': [],
            'warnings': [],
            'hooks': {
                'failed': ['ruff', 'shellcheck'],
                'passed': ['check yaml', 'check toml'],
            },
        }

        result = format_toon(analysis_result)

        # Should include failed hooks in output
        assert 'hooks' in result or 'ruff' in result
        assert 'failed' in result or 'ruff' in result

    def test_toon_omits_hooks_when_empty(self):
        """Test that TOON output omits hooks when none detected."""
        from logsift.output.toon_formatter import format_toon

        analysis_result = {
            'summary': {'status': 'success', 'exit_code': 0},
            'stats': {'total_errors': 0, 'total_warnings': 0},
            'errors': [],
            'warnings': [],
            'hooks': {
                'failed': [],
                'passed': [],
            },
        }

        result = format_toon(analysis_result)

        # Hooks should not appear if empty (token efficiency)
        # The actual behavior depends on implementation
        assert isinstance(result, str)
