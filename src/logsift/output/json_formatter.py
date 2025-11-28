"""JSON formatter for LLM-optimized output.

Generates structured JSON output designed for Claude Code and other AI agents.
"""

from typing import Any


def format_json(analysis_result: dict[str, Any]) -> str:
    """Format analysis results as JSON for LLM consumption.

    Args:
        analysis_result: Analysis results dictionary

    Returns:
        JSON string formatted for LLM agents
    """
    raise NotImplementedError('JSON formatter not yet implemented')
