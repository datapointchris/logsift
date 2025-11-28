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

    # Issue header
    severity = '🔴 ERROR' if is_error else '🟡 WARNING'
    issue_id = issue.get('id', '?')
    line_number = issue.get('line_in_log', '?')

    lines.append(f'### {severity} #{issue_id} (Line {line_number})\n')

    # Message
    message = issue.get('message', 'No message')
    lines.append(f'**Message:** {message}\n')

    # Pattern match info
    pattern_name = issue.get('pattern_name')
    if pattern_name:
        lines.append(f'**Pattern:** `{pattern_name}`')

    description = issue.get('description')
    if description:
        lines.append(f'**Description:** {description}')

    # Tags
    tags = issue.get('tags', [])
    if tags:
        tag_str = ', '.join(f'`{tag}`' for tag in tags)
        lines.append(f'**Tags:** {tag_str}')

    # File references
    file_refs = issue.get('file_references', [])
    if file_refs:
        refs_str = ', '.join(f'`{file}:{line}`' for file, line in file_refs)
        lines.append(f'**Files:** {refs_str}')

    # Suggestion
    suggestion = issue.get('suggestion')
    if suggestion:
        lines.append(f'\n**💡 Suggestion:** {suggestion}')

    # Context
    context_before = issue.get('context_before', [])
    context_after = issue.get('context_after', [])

    if context_before or context_after:
        lines.extend(('\n**Context:**', '```'))

        for ctx in context_before:
            ctx_line = ctx.get('line_number', '?')
            ctx_msg = ctx.get('message', '')
            lines.append(f'{ctx_line:>5} | {ctx_msg}')

        # The error/warning line itself
        lines.append(f'{line_number:>5} | ▶ {message}')

        for ctx in context_after:
            ctx_line = ctx.get('line_number', '?')
            ctx_msg = ctx.get('message', '')
            lines.append(f'{ctx_line:>5} | {ctx_msg}')

        lines.append('```')

    lines.append('')  # Blank line between issues

    return '\n'.join(lines)
