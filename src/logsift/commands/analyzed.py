"""What only the `analyzed` group does: show a saved analysis rendered as Markdown, and clean."""

import json
from pathlib import Path

import typer
from rich.console import Console

from logsift.cache.manager import SavedKind
from logsift.commands.clean import clean_saved_files
from logsift.commands.find_saved_file import choose_file
from logsift.commands.find_saved_file import latest_file
from logsift.output.analysis_format import ANALYSIS_KINDS
from logsift.output.markdown_formatter import format_markdown
from logsift.utils.display import display_with_bat

stderr_console = Console(stderr=True)


def show_analysis(json_path: Path) -> None:
    """Page a saved analysis rendered as Markdown."""
    try:
        analysis = json.loads(json_path.read_text())
    except (json.JSONDecodeError, OSError) as fault:
        stderr_console.print(f'[red]Error reading analysis: {fault}[/red]')
        raise typer.Exit(1) from None
    display_with_bat(format_markdown(analysis), language='markdown', filename=json_path.name)


def choose_analysis() -> None:
    """Pick a saved analysis with fzf and page it as Markdown."""
    chosen = choose_file(SavedKind.JSON, 'Choose an analysis to read', '`logsift analyzed latest <name>`')
    stderr_console.print(f'[cyan]Analysis: {chosen}[/cyan]\n')
    show_analysis(chosen)


def show_latest_analyzed(name: str | None) -> None:
    """Page the most recently written analysis, or the most recent whose run name contains name, as Markdown."""
    path = latest_file(SavedKind.JSON, name)
    stderr_console.print(f'[cyan]Latest analysis: {path}[/cyan]\n')
    show_analysis(path)


def clean_analyzed(days: int, dry_run: bool) -> None:
    """Delete the saved analyses older than days, in every format, or with dry_run name each one instead."""
    clean_saved_files(ANALYSIS_KINDS, days, dry_run, 'analysis file')
