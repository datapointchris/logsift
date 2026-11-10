"""Main analysis orchestrator.

Coordinates the analysis pipeline: parsing, pattern matching, and context extraction.
"""

import re
from contextlib import suppress
from typing import Any

from logsift import xdg_dirs
from logsift.core.detectors import IssueDetector
from logsift.core.file_references import FileReferenceDetector
from logsift.core.parser import LogParser
from logsift.patterns.loader import PatternLoader


class Analyzer:
    """Main analysis orchestrator that coordinates the log analysis pipeline."""

    def __init__(self, context_lines: int = 2) -> None:
        """Initialize the analyzer.

        Args:
            context_lines: Number of lines to extract before/after errors (default: 2)
        """
        self.parser = LogParser()
        self.pattern_loader = PatternLoader()
        self.issue_detector = IssueDetector()
        self.file_reference_detector = FileReferenceDetector()
        self.context_lines = context_lines

        builtin = self.pattern_loader.load_builtin_patterns()
        custom = self.pattern_loader.load_custom_patterns(xdg_dirs.custom_patterns_dir())
        # Custom first, so a user's pattern wins; the prefix keeps a custom docker.toml from replacing the built-in one.
        self.patterns = {f'custom/{category}': patterns for category, patterns in custom.items()} | builtin

    def analyze(self, log_content: str) -> dict[str, Any]:
        """Analyze log content and return structured results.

        Args:
            log_content: Raw log content to analyze

        Returns:
            Dictionary of errors, warnings, hooks and stats, the body of schemas/analysis.schema.json
        """
        log_entries = self.parser.parse(log_content)

        errors, warnings = self.issue_detector.detect_issues(log_entries, self.patterns)

        enhanced_errors = self._enhance_issues(errors, log_entries)

        enhanced_warnings = self._enhance_issues(warnings, log_entries)

        hooks = self._detect_hooks(log_entries)

        stats = {
            'total_errors': len(errors),
            'total_warnings': len(warnings),
        }

        return {
            'errors': enhanced_errors,
            'warnings': enhanced_warnings,
            'hooks': hooks,
            'stats': stats,
        }

    def _enhance_issues(self, issues: list[dict[str, Any]], log_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Enhance issues with file references and context.

        Pattern matching already happened during detection, so we only add:
        - File references (file:line patterns in the message)
        - Context lines (surrounding log entries)

        Args:
            issues: List of error or warning dictionaries
            log_entries: All parsed log entries

        Returns:
            Enhanced issues with additional metadata
        """
        enhanced = []

        for issue in issues:
            message = issue.get('message', '')
            file_refs = self.file_reference_detector.detect_references(message)
            if file_refs:
                issue['file_references'] = file_refs

            line_number = issue.get('line_in_log')
            if line_number is not None:
                for idx, entry in enumerate(log_entries):
                    if entry.get('line_number') == line_number:
                        with suppress(IndexError, ValueError):
                            pattern_context_after = issue.get('pattern_context_lines_after')
                            context = self._extract_context(log_entries, idx, context_lines_after=pattern_context_after)
                            issue['context_before'] = context['context_before']
                            issue['context_after'] = context['context_after']
                        break

            enhanced.append(issue)

        return enhanced

    def _extract_context(
        self,
        log_entries: list[dict[str, Any]],
        error_index: int,
        context_lines_after: int | None = None,
    ) -> dict[str, Any]:
        """Extract context lines around an error entry.

        Args:
            log_entries: List of all log entries
            error_index: Index of the error in log_entries
            context_lines_after: Override for lines after (from pattern's context_lines_after)

        Returns:
            Dictionary with before and after context

        Raises:
            IndexError: If error_index is out of bounds
        """
        if error_index < 0 or error_index >= len(log_entries):
            raise IndexError(f'Error index {error_index} out of bounds for log entries of length {len(log_entries)}')

        start_index = max(0, error_index - self.context_lines)

        effective_context_after = context_lines_after if context_lines_after is not None else self.context_lines
        end_index = min(len(log_entries), error_index + effective_context_after + 1)

        context_before = log_entries[start_index:error_index]
        context_after = log_entries[error_index + 1 : end_index]

        return {
            'context_before': context_before,
            'context_after': context_after,
        }

    def _detect_hooks(self, log_entries: list[dict[str, Any]]) -> dict[str, list[str]]:
        """Detect pre-commit hook names from log entries.

        Looks for patterns like:
        - "hookname...Passed" or "hookname...Failed"
        - "- hook id: hookname"

        Args:
            log_entries: Parsed log entries

        Returns:
            Dictionary with 'passed' and 'failed' lists of hook names
        """
        passed: list[str] = []
        failed: list[str] = []

        # Pattern to match: hookname followed by dots and Passed/Failed
        # Examples: "ruff.....................................................................Failed"
        #           "check yaml...............................................................Passed"
        hook_status_pattern = re.compile(r'^(.+?)\.{3,}(Passed|Failed)\s*$')

        for entry in log_entries:
            message = entry.get('message', '')
            match = hook_status_pattern.match(message)
            if match:
                hook_name = match.group(1).strip()
                status = match.group(2)
                if status == 'Passed' and hook_name not in passed:
                    passed.append(hook_name)
                elif status == 'Failed' and hook_name not in failed:
                    failed.append(hook_name)

        return {
            'passed': passed,
            'failed': failed,
        }
