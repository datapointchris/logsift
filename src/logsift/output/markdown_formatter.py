"""Markdown formatter for human-readable output.

Generates beautiful colored markdown output for terminal display.
"""

from typing import Any


def format_markdown(analysis_result: dict[str, Any]) -> str:
    """Format analysis results as markdown for human reading.

    Args:
        analysis_result: Analysis results dictionary

    Returns:
        Markdown string with colors and formatting
    """
    lines = []

    # Get stats
    stats = analysis_result.get('stats', {})
    total_errors = stats.get('total_errors', 0)
    total_warnings = stats.get('total_warnings', 0)

    # Header with summary
    lines.append('# Log Analysis Results\n')

    if total_errors == total_warnings == 0:
        lines.append('**Status:** ✓ Clean - No errors or warnings found\n')
        return '\n'.join(lines)

    lines.append(f'**Errors:** {total_errors} | **Warnings:** {total_warnings}\n')

    # Format errors
    errors = analysis_result.get('errors', [])
    if errors:
        lines.append('## Errors\n')
        for error in errors:
            lines.append(_format_issue(error, is_error=True))

    # Format warnings
    warnings = analysis_result.get('warnings', [])
    if warnings:
        lines.append('## Warnings\n')
        for warning in warnings:
            lines.append(_format_issue(warning, is_error=False))

    return '\n'.join(lines)


def _format_issue(issue: dict[str, Any], is_error: bool) -> str:
    """Format a single error or warning.

    Args:
        issue: Issue dictionary
        is_error: True for errors, False for warnings

    Returns:
        Formatted markdown string
    """
    lines = []

    # Issue header (simplified - no emojis)
    severity = 'Error' if is_error else 'Warning'
    issue_id = issue.get('id', '?')
    line_number = issue.get('line_in_log', '?')

    lines.append(f'### {severity} #{issue_id} (Line {line_number})\n')

    # Message (no "Message:" label, just the message)
    message = issue.get('message', 'No message')
    lines.append(f'{message}\n')

    # File references (kept - actionable)
    file_refs = issue.get('file_references', [])
    if file_refs:
        refs_str = ', '.join(f'`{file}:{line}`' for file, line in file_refs)
        lines.append(f'**Files:** {refs_str}\n')

    # Suggestion (kept - actionable, no emoji)
    suggestion = issue.get('suggestion')
    if suggestion:
        lines.append(f'**Suggestion:** {suggestion}\n')

    # Context (simplified to line range)
    context_before = issue.get('context_before', [])
    context_after = issue.get('context_after', [])

    if context_before or context_after:
        # Calculate line range
        start_line = line_number
        end_line = line_number

        if context_before:
            start_line = min(ctx.get('line_number', line_number) for ctx in context_before)
        if context_after:
            end_line = max(ctx.get('line_number', line_number) for ctx in context_after)

        lines.append(f'**Context:** Lines {start_line}-{end_line}')

    lines.append('')  # Blank line between issues

    return '\n'.join(lines)
