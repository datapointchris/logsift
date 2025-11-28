"""Dual-stream manager for simultaneous JSON and Markdown output.

Manages writing to multiple output streams simultaneously.
"""

import sys
from pathlib import Path
from typing import Any
from typing import TextIO

from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown


class StreamManager:
    """Manage dual output streams for JSON and Markdown."""

    def __init__(self) -> None:
        """Initialize the stream manager."""
        pass

    def write_dual(
        self,
        analysis_result: dict[str, Any],
        json_path: str | None = None,
        markdown_path: str | None = None,
    ) -> None:
        """Write analysis results to multiple streams.

        Args:
            analysis_result: Analysis results dictionary
            json_path: Optional path to write JSON output
            markdown_path: Optional path to write markdown output
        """
        write_dual_output(
            analysis_result=analysis_result,
            json_path=Path(json_path) if json_path else None,
            markdown_path=Path(markdown_path) if markdown_path else None,
        )


def write_dual_output(
    analysis_result: dict[str, Any],
    json_path: Path | None = None,
    markdown_path: Path | None = None,
    json_stream: TextIO | None = None,
    markdown_stream: TextIO | None = None,
) -> None:
    """Write analysis results to multiple output destinations.

    Args:
        analysis_result: Analysis results dictionary
        json_path: Optional path to write JSON output (file)
        markdown_path: Optional path to write Markdown output (file)
        json_stream: Optional stream to write JSON output (e.g., sys.stdout)
        markdown_stream: Optional stream to write Markdown output (e.g., sys.stdout)

    Example:
        # Write JSON to file, Markdown to stdout
        write_dual_output(result, json_path=Path('output.json'), markdown_stream=sys.stdout)

        # Write both to stdout (with separator)
        write_dual_output(result, json_stream=sys.stdout, markdown_stream=sys.stdout)
    """
    # Format the outputs
    json_output = format_json(analysis_result)
    markdown_output = format_markdown(analysis_result)

    # Write JSON output
    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json_output, encoding='utf-8')

    if json_stream:
        json_stream.write(json_output)
        json_stream.write('\n')
        json_stream.flush()

    # Write Markdown output
    if markdown_path:
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(markdown_output, encoding='utf-8')

    if markdown_stream:
        markdown_stream.write(markdown_output)
        markdown_stream.write('\n')
        markdown_stream.flush()


def write_stream_mode(
    analysis_result: dict[str, Any],
    json_cache_path: Path,
) -> None:
    """Write in stream mode: JSON to file, Markdown to stdout.

    This is the recommended mode for monitoring commands where humans
    want to see progress (Markdown) while LLMs can read the structured
    data later (JSON file).

    Args:
        analysis_result: Analysis results dictionary
        json_cache_path: Path to write JSON output for later retrieval
    """
    write_dual_output(
        analysis_result=analysis_result,
        json_path=json_cache_path,
        markdown_stream=sys.stdout,
    )


def write_both_to_stdout(analysis_result: dict[str, Any]) -> None:
    """Write both JSON and Markdown to stdout with separator.

    Used for debugging or when explicitly requested with --both flag.

    Args:
        analysis_result: Analysis results dictionary
    """
    # Write JSON first
    print('=== JSON OUTPUT ===')
    print(format_json(analysis_result))
    print()

    # Then Markdown
    print('=== MARKDOWN OUTPUT ===')
    print(format_markdown(analysis_result))
