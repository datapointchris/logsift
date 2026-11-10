"""The formats monitor and analyze print an analysis in, and what `auto` picks."""

import enum
import sys
from collections.abc import Callable
from typing import Any
from typing import TextIO

from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown
from logsift.output.toon_formatter import format_toon


class AnalysisFormat(enum.StrEnum):
    AUTO = 'auto'
    JSON = 'json'
    TOON = 'toon'
    MARKDOWN = 'markdown'


RENDERERS: dict[AnalysisFormat, Callable[[dict[str, Any]], str]] = {
    AnalysisFormat.JSON: format_json,
    AnalysisFormat.TOON: format_toon,
    AnalysisFormat.MARKDOWN: format_markdown,
}


def resolve_format(requested: str, stream: TextIO | None = None) -> AnalysisFormat:
    """Return the format to print in: auto is markdown on a terminal, and toon for an agent reading a pipe.

    Args:
        requested: An AnalysisFormat value
        stream: Where the analysis is printed; sys.stdout at call time when omitted
    """
    chosen = AnalysisFormat(requested)
    if chosen is not AnalysisFormat.AUTO:
        return chosen
    out = stream if stream is not None else sys.stdout
    return AnalysisFormat.MARKDOWN if out.isatty() else AnalysisFormat.TOON


def render_analysis(analysis: dict[str, Any], requested: str, stream: TextIO | None = None) -> str:
    """The analysis as text in the requested format, auto resolved against stream."""
    return RENDERERS[resolve_format(requested, stream)](analysis)
