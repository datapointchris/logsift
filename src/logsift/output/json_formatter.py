"""JSON formatter for LLM-optimized output.

Generates structured JSON output designed for Claude Code and other AI agents.
"""

import json
from typing import Any


def format_json(analysis_result: dict[str, Any]) -> str:
    """Format analysis results as JSON for LLM consumption.

    Args:
        analysis_result: Analysis results dictionary

    Returns:
        JSON string formatted for LLM agents
    """
    # Convert file_references tuples to lists for JSON serialization
    output = _prepare_for_json(analysis_result)

    # Pretty-print with 2-space indentation for readability
    return json.dumps(output, indent=2, ensure_ascii=False)


def _prepare_for_json(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare data for JSON serialization by converting tuples to lists.

    Args:
        data: Analysis result data

    Returns:
        Data with tuples converted to lists
    """
    # Deep copy to avoid modifying original
    result = {}

    for key, value in data.items():
        if isinstance(value, list):
            result[key] = [_convert_item(item) for item in value]
        else:
            result[key] = value

    return result


def _convert_item(item: Any) -> Any:
    """Convert an item for JSON serialization.

    Args:
        item: Item to convert

    Returns:
        Converted item
    """
    if isinstance(item, dict):
        converted = {}
        for key, value in item.items():
            if key == 'file_references' and isinstance(value, list):
                # Convert list of tuples to list of lists
                converted[key] = [list(ref) if isinstance(ref, tuple) else ref for ref in value]
            elif isinstance(value, dict | list):
                converted[key] = _convert_item(value)
            else:
                converted[key] = value
        return converted
    if isinstance(item, list):
        return [_convert_item(x) for x in item]
    return item
