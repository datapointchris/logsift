"""Main CLI application using Typer.

This module defines the primary logsift command-line interface with subcommands for monitoring, analyzing, and managing logs.
"""

from typing import Annotated

import typer
from rich.console import Console

from logsift import __version__

app = typer.Typer(
    name='logsift',
    help='Intelligent log analysis for agentic workflows',
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        console.print(f'logsift version {__version__}')
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        '--version',
        '-v',
        callback=version_callback,
        is_eager=True,
        help='Show version and exit',
    ),
) -> None:
    """logsift - Intelligent log analysis for agentic workflows.

    An LLM-optimized log analysis and command monitoring tool designed for
    Claude Code and other AI agents.
    """
    pass


@app.command()
def monitor(
    command: Annotated[list[str], typer.Argument(help='Command to monitor')],
    name: Annotated[str | None, typer.Option('-n', '--name', help='Name for this monitoring session')] = None,
    interval: Annotated[int, typer.Option('-i', '--interval', help='Progress check interval in seconds')] = 60,
    format: Annotated[str, typer.Option('--format', help='Output format: auto, json, markdown, plain')] = 'auto',
) -> None:
    """Monitor a command and analyze its output.

    Example:
        logsift monitor -- make build
        logsift monitor -n install -i 30 -- task install
    """
    console.print('[yellow]Monitor command not yet implemented[/yellow]')
    console.print(f'Command: {" ".join(command)}')
    console.print(f'Name: {name}')
    console.print(f'Interval: {interval}s')
    console.print(f'Format: {format}')


@app.command()
def analyze(
    log_file: Annotated[str, typer.Argument(help='Path to log file to analyze')],
    format: Annotated[str, typer.Option('--format', help='Output format: auto, json, markdown, plain')] = 'auto',
) -> None:
    """Analyze an existing log file.

    Example:
        logsift analyze /var/log/app.log
        logsift analyze --format=json build.log
    """
    console.print('[yellow]Analyze command not yet implemented[/yellow]')
    console.print(f'Log file: {log_file}')
    console.print(f'Format: {format}')


@app.command()
def watch(
    log_file: Annotated[str, typer.Argument(help='Path to log file to watch')],
    interval: Annotated[int, typer.Option('-i', '--interval', help='Update interval in seconds')] = 1,
) -> None:
    """Watch and analyze a log file in real-time.

    Example:
        logsift watch /var/log/app.log
        logsift watch -i 2 /var/log/app.log
    """
    console.print('[yellow]Watch command not yet implemented[/yellow]')
    console.print(f'Log file: {log_file}')
    console.print(f'Interval: {interval}s')


if __name__ == '__main__':
    app()
