"""Tests for error code and file reference extraction.

These tests verify that logsift extracts error codes (F401, E501, SC2086)
and file references from linter output into the error metadata.
"""

from logsift.core.analyzer import Analyzer


class TestErrorCodeExtraction:
    """Test error code extraction from linter output."""

    def test_extracts_ruff_error_code(self):
        """Test that ruff error codes are extracted."""
        log_content = """\
ruff.....................................................................Failed
src/main.py:10:1: F401 'sys' imported but unused
src/main.py:15:5: E501 line too long (120 > 88 characters)
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        assert len(result['errors']) >= 2

        # Find the F401 error
        f401_error = next(
            (e for e in result['errors'] if 'F401' in e.get('message', '')),
            None,
        )
        assert f401_error is not None
        assert f401_error.get('code') == 'F401'

    def test_extracts_shellcheck_error_code(self):
        """Test that shellcheck SC codes are extracted."""
        log_content = """\
shellcheck...............................................................Failed
In script.sh line 5:
    ^---^ SC2086 (info): Double quote to prevent globbing and word splitting.
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        # Find the SC2086 warning
        sc_warning = next(
            (w for w in result['warnings'] if 'SC2086' in w.get('message', '')),
            None,
        )
        assert sc_warning is not None
        assert sc_warning.get('code') == 'SC2086'

    def test_extracts_mypy_error_code(self):
        """Test that mypy error codes are extracted."""
        log_content = """\
mypy.....................................................................Failed
src/main.py:10: error: Argument 1 to "foo" has incompatible type  [arg-type]
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        # Find the mypy error
        mypy_error = next(
            (e for e in result['errors'] if 'incompatible type' in e.get('message', '')),
            None,
        )
        assert mypy_error is not None
        assert mypy_error.get('code') == 'arg-type'

    def test_extracts_refurb_error_code(self):
        """Test that refurb FURB codes are extracted."""
        log_content = """\
refurb...................................................................Failed
tests/main.py:6:1 [FURB101]: Replace `with open(x) as f: y = f.read()` with `y = Path(x).read_text()`
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        # Find the FURB101 warning
        furb_warning = next(
            (w for w in result['warnings'] if 'FURB101' in w.get('message', '')),
            None,
        )
        assert furb_warning is not None
        assert furb_warning.get('code') == 'FURB101'


class TestFileLineColExtraction:
    """Test file, line, and column extraction from linter output."""

    def test_extracts_file_line_col_from_ruff(self):
        """Test that file:line:col is extracted from ruff errors."""
        log_content = """\
ruff.....................................................................Failed
src/main.py:10:1: F401 'sys' imported but unused
"""

        analyzer = Analyzer()
        result = analyzer.analyze(log_content)

        # Find the F401 error
        f401_error = next(
            (e for e in result['errors'] if 'F401' in e.get('message', '')),
            None,
        )
        assert f401_error is not None

        # Check file references are extracted
        file_refs = f401_error.get('file_references', [])
        assert len(file_refs) >= 1
        assert file_refs[0][0] == 'src/main.py'
        assert file_refs[0][1] == 10


class TestToonFormatterErrorCodes:
    """Test TOON formatter includes error codes."""

    def test_toon_includes_error_code(self):
        """Test that TOON output includes error codes when present."""
        from logsift.output.toon_formatter import format_toon

        analysis_result = {
            'summary': {'status': 'failed', 'exit_code': 1},
            'stats': {'total_errors': 1, 'total_warnings': 0},
            'errors': [
                {
                    'id': 1,
                    'severity': 'error',
                    'line_in_log': 2,
                    'message': "src/main.py:10:1: F401 'sys' imported but unused",
                    'code': 'F401',
                    'suggestion': 'Remove unused import',
                }
            ],
            'warnings': [],
            'hooks': {'failed': ['ruff'], 'passed': []},
        }

        result = format_toon(analysis_result)

        # Error code should be in output
        assert 'F401' in result
