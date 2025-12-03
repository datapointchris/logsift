"""Main analysis orchestrator.

Coordinates the analysis pipeline: parsing, pattern matching, and context extraction.
"""

from contextlib import suppress
from typing import Any

from logsift.core.context import ContextExtractor
from logsift.core.extractors import FileReferenceExtractor
from logsift.core.extractors import IssueExtractor
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
        self.issue_extractor = IssueExtractor()
        self.file_reference_extractor = FileReferenceExtractor()
        self.context_extractor = ContextExtractor(context_lines=context_lines)

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

        # Extract errors and warnings using ALL TOML patterns
        errors, warnings = self.issue_extractor.extract_issues(log_entries, self.patterns)

        # Enhance errors with file references and context
        # (pattern matching already happened during extraction)
        enhanced_errors = self._enhance_issues(errors, log_entries)

        # Enhance warnings with file references and context
        enhanced_warnings = self._enhance_issues(warnings, log_entries)

        # Build statistics
        stats = {
            'total_errors': len(errors),
            'total_warnings': len(warnings),
        }

        return {
            'errors': enhanced_errors,
            'warnings': enhanced_warnings,
            'stats': stats,
        }

    def _enhance_issues(self, issues: list[dict[str, Any]], log_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Enhance issues with file references and context.

        Pattern matching already happened during extraction, so we only add:
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
            file_refs = self.file_reference_extractor.extract_references(message)
            if file_refs:
                issue['file_references'] = file_refs

            # Extract context around this issue
            # Find the issue in log_entries by line number
            line_number = issue.get('line_in_log')
            if line_number is not None:
                # Find index in log_entries
                for idx, entry in enumerate(log_entries):
                    if entry.get('line_number') == line_number:
                        with suppress(IndexError, ValueError):
                            context = self.context_extractor.extract_context(log_entries, idx)
                            issue['context_before'] = context['context_before']
                            issue['context_after'] = context['context_after']
                        break

            enhanced.append(issue)

        return enhanced
