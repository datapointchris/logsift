"""Tests for multi-line error context extraction.

These tests verify that patterns with context_lines_after correctly
extract extended context for multi-line errors like CalledProcessError.
"""

import re
import tomllib
from pathlib import Path

from logsift.core.analyzer import Analyzer


class TestMultiLinePatterns:
    """Test patterns that require extended context."""

    def test_called_process_error_pattern_matches(self):
        """Test that CalledProcessError pattern exists and matches."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'pre_commit_called_process_error'),
            None,
        )
        assert pattern is not None, 'pre_commit_called_process_error pattern not found'

        test_line = 'An unexpected error has occurred: CalledProcessError'
        match = re.search(pattern['regex'], test_line)
        assert match is not None, f"Pattern didn't match: {test_line}"
        assert pattern.get('context_lines_after', 0) >= 5

    def test_stderr_section_pattern_matches(self):
        """Test that stderr section marker pattern exists and matches."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'stderr_section_error'),
            None,
        )
        assert pattern is not None, 'stderr_section_error pattern not found'

        test_line = 'stderr:'
        match = re.search(pattern['regex'], test_line)
        assert match is not None, f"Pattern didn't match: {test_line}"


class TestAnalyzerExtendedContext:
    """Test analyzer behavior with extended context patterns."""

    def test_analyzer_extracts_extended_context(self):
        """Test that analyzer extracts extended context for CalledProcessError."""
        log_content = """\
Starting pre-commit hook...
An unexpected error has occurred: CalledProcessError
command: ('/usr/local/bin/docker', 'system', 'info')
return code: 1
stdout:
    {"ID":""}
stderr:
    failed to connect to the docker API at unix:///socket.sock
Aborting hook execution"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        assert len(result['errors']) >= 1

        # Find the CalledProcessError
        cpe_error = next(
            (e for e in result['errors'] if 'CalledProcessError' in e.get('message', '')),
            None,
        )
        assert cpe_error is not None, 'CalledProcessError not detected'

        # Should have extended context
        context_after = cpe_error.get('context_after', [])
        assert len(context_after) > 0, 'No context_after extracted'

        # Context should include the stderr info
        context_messages = [c.get('message', '') for c in context_after]
        context_text = ' '.join(context_messages)
        assert 'stderr' in context_text or 'docker' in context_text.lower(), f'Expected stderr/docker info in context, got: {context_text}'

    def test_analyzer_preserves_context_lines_after_in_issue(self):
        """Test that analyzer stores context_lines_after from pattern in issue."""
        log_content = """\
An unexpected error has occurred: CalledProcessError
command: ('/usr/local/bin/docker', 'system', 'info')
return code: 1
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        assert len(result['errors']) >= 1

        cpe_error = next(
            (e for e in result['errors'] if 'CalledProcessError' in e.get('message', '')),
            None,
        )
        assert cpe_error is not None

        # Pattern should specify extended context
        pattern_context = cpe_error.get('pattern_context_lines_after')
        assert pattern_context is not None and pattern_context >= 5, f'Expected pattern_context_lines_after >= 5, got: {pattern_context}'


class TestToonFormatterContext:
    """Test TOON formatter includes extended context when needed."""

    def test_toon_includes_context_for_multiline_errors(self):
        """Test that TOON output includes context_after for errors that need it."""
        from logsift.output.toon_formatter import format_toon

        analysis_result = {
            'summary': {'status': 'failed', 'exit_code': 1},
            'stats': {'total_errors': 1, 'total_warnings': 0},
            'errors': [
                {
                    'id': 1,
                    'severity': 'error',
                    'line_in_log': 2,
                    'message': 'An unexpected error has occurred: CalledProcessError',
                    'context_after': [
                        {'line_number': 3, 'message': "command: ('/usr/local/bin/docker',)"},
                        {'line_number': 4, 'message': 'return code: 1'},
                        {'line_number': 5, 'message': 'stderr:'},
                        {'line_number': 6, 'message': '    failed to connect to docker API'},
                    ],
                    'pattern_context_lines_after': 6,
                    'suggestion': 'Check stderr for root cause',
                }
            ],
            'warnings': [],
        }

        result = format_toon(analysis_result)

        # Context should be included because pattern_context_lines_after is set
        # Check that we can see some of the context info
        assert 'CalledProcessError' in result
        # Either context_after is included, or the message is extended
        assert 'docker' in result.lower() or 'context_after' in result


class TestDockerConnectionPattern:
    """Test docker connection failure pattern."""

    def test_docker_socket_pattern_matches(self):
        """Test that docker socket connection pattern matches."""
        pattern_file = Path('src/logsift/patterns/defaults/pre-commit.toml')
        with pattern_file.open('rb') as f:
            data = tomllib.load(f)

        pattern = next(
            (p for p in data['patterns'] if p['name'] == 'docker_socket_connection_failure'),
            None,
        )
        assert pattern is not None, 'docker_socket_connection_failure pattern not found'

        test_line = 'failed to connect to the docker API at unix:///Users/chris/.config/colima/max/docker.sock'
        match = re.search(pattern['regex'], test_line)
        assert match is not None, f"Pattern didn't match: {test_line}"
        assert pattern['severity'] == 'error'
        assert 'suggestion' in pattern
