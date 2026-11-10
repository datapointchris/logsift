"""JSON formatter for LLM-optimized output.

Generates the document schemas/analysis.schema.json describes, for Claude Code and other AI agents.
"""

import json
from typing import Any

SCHEMA_VERSION = 1


def format_json(analysis_result: dict[str, Any]) -> str:
    """Format analysis results as the JSON document schemas/analysis.schema.json describes.

    Args:
        analysis_result: Analysis results dictionary

    Returns:
        JSON string formatted for LLM agents
    """
    output = {'schema_version': SCHEMA_VERSION} | prepare_for_json(analysis_result)

    return json.dumps(output, indent=2, ensure_ascii=False)


def prepare_for_json(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare data for JSON serialization by converting tuples to lists.

    Args:
        data: Analysis result data

    Returns:
        Data with tuples converted to lists
    """
    result = {}

    for key, value in data.items():
        if isinstance(value, list):
            result[key] = [convert_item(item) for item in value]
        else:
            result[key] = value

    return result


def convert_item(item: Any) -> Any:
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
                converted[key] = [list(ref) if isinstance(ref, tuple) else ref for ref in value]
            elif isinstance(value, dict | list):
                converted[key] = convert_item(value)
            else:
                converted[key] = value
        return converted
    if isinstance(item, list):
        return [convert_item(x) for x in item]
    return item
