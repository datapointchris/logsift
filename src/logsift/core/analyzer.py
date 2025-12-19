"""Main analysis orchestrator.

Coordinates the analysis pipeline: parsing, pattern matching, and context extraction.
"""

import re
from contextlib import suppress
from typing import Any

from logsift.core.detectors import FileReferenceDetector
from logsift.core.detectors import IssueDetector
from logsift.core.parser import LogParser
from logsift.patterns.loader import PatternLoader


class Analyzer:
    """Main analysis orchestrator that coordinates the log analysis pipeline."""

    def __init__(self, context_lines: int = 2) -> None:
        """Initialize the analyzer.

        Args:
            context_lines: Number of lines to extract before/after errors (default: 2)
        """
        # Initialize all components
        self.parser = LogParser()
        self.pattern_loader = PatternLoader()
        self.issue_detector = IssueDetector()
        self.file_reference_detector = FileReferenceDetector()
        self.context_lines = context_lines

        # Load built-in patterns
        self.patterns = self.pattern_loader.load_builtin_patterns()

    def analyze(self, log_content: str) -> dict[str, Any]:
        """Analyze log content and return structured results.

        Args:
            log_content: Raw log content to analyze

        Returns:
            Dictionary containing analysis results with errors, warnings, and actionable items
        """
        # Parse log content
        log_entries = self.parser.parse(log_content)

        # Detect errors and warnings using TOML patterns (single pass)
        errors, warnings = self.issue_detector.detect_issues(log_entries, self.patterns)

        # Enhance errors with file references and context
        enhanced_errors = self._enhance_issues(errors, log_entries)

        # Enhance warnings with file references and context
        enhanced_warnings = self._enhance_issues(warnings, log_entries)

        # Detect pre-commit hooks from log entries
        hooks = self._detect_hooks(log_entries)

        # Build statistics
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
            # Extract file references from the message
            message = issue.get('message', '')
            file_refs = self.file_reference_detector.detect_references(message)
            if file_refs:
                issue['file_references'] = file_refs

            # Extract context around this issue
            line_number = issue.get('line_in_log')
            if line_number is not None:
                # Find index in log_entries
                for idx, entry in enumerate(log_entries):
                    if entry.get('line_number') == line_number:
                        with suppress(IndexError, ValueError):
                            # Use pattern's context_lines_after if specified
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
        # Validate error_index
        if error_index < 0 or error_index >= len(log_entries):
            raise IndexError(f'Error index {error_index} out of bounds for log entries of length {len(log_entries)}')

        # Calculate start and end indices for context
        start_index = max(0, error_index - self.context_lines)

        # Use pattern's context_lines_after if specified, otherwise use default
        effective_context_after = context_lines_after if context_lines_after is not None else self.context_lines
        end_index = min(len(log_entries), error_index + effective_context_after + 1)

        # Extract context before and after the error
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
