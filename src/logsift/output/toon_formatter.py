"""TOON formatter for LLM-optimized compact output.

Generates TOON (Token-Oriented Object Notation) output designed for Claude Code
and other AI agents. Achieves 30-60% token reduction vs JSON while maintaining
accuracy.
"""

from typing import Any

from toon_format import encode


def format_toon(analysis_result: dict[str, Any]) -> str:
    """Format analysis results as TOON for LLM consumption.

    Strips non-actionable metadata (pattern_matched, description, tags) and
    null fields to create compact output optimized for LLM agents.

    Args:
        analysis_result: Analysis results dictionary

    Returns:
        TOON string formatted for LLM agents
    """
    # Strip non-actionable fields before encoding
    compact_data = _prepare_for_toon(analysis_result)

    # Encode to TOON format
    return encode(compact_data)


def _prepare_for_toon(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare data for TOON encoding by stripping non-actionable fields.

    Removes:
    - Pattern metadata (pattern_matched, description, tags)
    - Null/None fields
    - Verbose context arrays (simplified to essential info)

    Args:
        data: Analysis result data

    Returns:
        Compact data ready for TOON encoding
    """
    result: dict[str, Any] = {}

    # Copy summary, stripping nulls
    if 'summary' in data:
        result['summary'] = _strip_nulls(data['summary'])

    # Copy stats
    if 'stats' in data:
        result['stats'] = data['stats']

    # Process errors - strip metadata and nulls
    if 'errors' in data:
        result['errors'] = [_compact_error(error) for error in data['errors']]

    # Process warnings - strip metadata and nulls
    if 'warnings' in data:
        result['warnings'] = [_compact_error(warning) for warning in data['warnings']]

    return result


def _compact_error(error: dict[str, Any]) -> dict[str, Any]:
    """Strip non-actionable fields from an error/warning.

    Keeps only: id, severity, line_in_log, message, file, file_line, suggestion
    Removes: pattern_matched, description, tags, context_before

    For multi-line errors (pattern_context_lines_after is set), context_after
    is preserved as a simple list of message strings for LLM consumption.

    Args:
        error: Error/warning dictionary

    Returns:
        Compact error dictionary
    """
    # Define fields to keep (actionable data only)
    keep_fields = {
        'id',
        'severity',
        'line_in_log',
        'message',
        'file',
        'file_line',
        'suggestion',
    }

    # Filter to keep only actionable fields, then strip nulls
    compact = {k: v for k, v in error.items() if k in keep_fields}

    # For multi-line errors, include context_after as simple list of messages
    if error.get('pattern_context_lines_after') and error.get('context_after'):
        context_messages = [entry.get('message', '') for entry in error['context_after'] if isinstance(entry, dict)]
        if context_messages:
            compact['context_after'] = context_messages

    return _strip_nulls(compact)


def _strip_nulls(data: dict[str, Any]) -> dict[str, Any]:
    """Remove None/null values from a dictionary.

    Args:
        data: Dictionary to process

    Returns:
        Dictionary with null values removed
    """
    return {k: v for k, v in data.items() if v is not None}
