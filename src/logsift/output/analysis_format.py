"""The formats monitor and analyze print an analysis in, and what `auto` picks."""

import enum
import sys
from collections.abc import Callable
from typing import Any
from typing import NamedTuple
from typing import TextIO

from logsift.cache.manager import SavedKind
from logsift.output.json_formatter import format_json
from logsift.output.markdown_formatter import format_markdown
from logsift.output.toon_formatter import format_toon


class AnalysisFormat(enum.StrEnum):
    AUTO = 'auto'
    JSON = 'json'
    TOON = 'toon'
    MARKDOWN = 'markdown'


class Rendering(NamedTuple):
    render: Callable[[dict[str, Any]], str]
    saved_as: SavedKind


# Every format an analysis prints in, and the cache directory each run saves it under.
RENDERINGS = {
    AnalysisFormat.JSON: Rendering(format_json, SavedKind.JSON),
    AnalysisFormat.TOON: Rendering(format_toon, SavedKind.TOON),
    AnalysisFormat.MARKDOWN: Rendering(format_markdown, SavedKind.MD),
}
ANALYSIS_KINDS = tuple(rendering.saved_as for rendering in RENDERINGS.values())


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
    return RENDERINGS[resolve_format(requested, stream)].render(analysis)


def renderings_to_save(analysis: dict[str, Any]) -> dict[SavedKind, str]:
    """The analysis rendered in every format, keyed by the cache directory each is saved under."""
    return {rendering.saved_as: rendering.render(analysis) for rendering in RENDERINGS.values()}
