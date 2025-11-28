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
    format: Annotated[str, typer.Option('--format', help='Output format: auto, json, markdown, plain')] = 'auto',
    notify: Annotated[bool, typer.Option('--notify', help='Send desktop notification on completion')] = False,
    external_log: Annotated[str | None, typer.Option('--external-log', help='Tail external log file while monitoring')] = None,
    append: Annotated[bool, typer.Option('--append', help='Append to existing log instead of creating new')] = False,
) -> None:
    """Monitor a command and analyze its output.

    Example:
        logsift monitor -- make build
        logsift monitor -n install -- task install
        logsift monitor --external-log /var/log/app.log -- npm start
        logsift monitor -n build --append -- make
    """
    from logsift.commands.monitor import monitor_command

    monitor_command(
        command,
        name=name,
        output_format=format,
        notify=notify,
        external_log=external_log,
        append=append,
    )


@app.command()
def analyze(
    log_file: Annotated[str | None, typer.Argument(help='Path to log file to analyze (optional with fzf)')] = None,
    format: Annotated[str, typer.Option('--format', help='Output format: auto, json, markdown, plain')] = 'auto',
    interactive: Annotated[bool, typer.Option('-i', '--interactive', help='Use fzf to select log file')] = False,
) -> None:
    """Analyze an existing log file.

    If no log file is provided and fzf is installed, an interactive selector will appear.

    Example:
        logsift analyze /var/log/app.log
        logsift analyze --format=json build.log
        logsift analyze --interactive
        logsift analyze  # Interactive if fzf is available
    """
    from logsift.commands.analyze import analyze_log

    # If no log file provided, try interactive mode
    if not log_file:
        from logsift.cache.manager import CacheManager
        from logsift.utils.fzf import is_fzf_available
        from logsift.utils.fzf import select_log_file

        if not is_fzf_available() and not interactive:
            console.print('[red]Error: No log file specified and fzf is not available[/red]')
            console.print('[dim]Provide a log file path or install fzf for interactive mode[/dim]')
            raise typer.Exit(1)

        # Use fzf to select a log file
        cache = CacheManager()
        logs = cache.list_all_logs()

        if not logs:
            console.print('[yellow]No cached logs found[/yellow]')
            raise typer.Exit(1)

        selected = select_log_file(logs, 'Select log file to analyze')

        if not selected:
            console.print('[dim]No file selected[/dim]')
            raise typer.Exit(0)

        log_file = selected
        console.print(f'[cyan]Analyzing: {log_file}[/cyan]\n')

    analyze_log(log_file, output_format=format)


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
    from logsift.commands.watch import watch_log

    watch_log(log_file, interval=interval)


# Create logs command group
logs_app = typer.Typer(help='Manage cached log files')
app.add_typer(logs_app, name='logs')


@logs_app.command('list')
def logs_list(
    context: Annotated[str | None, typer.Option('-c', '--context', help='Filter by context')] = None,
    format: Annotated[str, typer.Option('--format', help='Output format: table, json, plain')] = 'table',
) -> None:
    """List cached log files.

    Example:
        logsift logs list
        logsift logs list --context monitor
        logsift logs list --format json
    """
    from logsift.commands.logs import list_logs

    list_logs(context=context, output_format=format)


@logs_app.command('clean')
def logs_clean(
    days: Annotated[int, typer.Option('-d', '--days', help='Delete logs older than N days')] = 90,
    dry_run: Annotated[bool, typer.Option('--dry-run', help='Show what would be deleted')] = False,
) -> None:
    """Clean old log files from cache.

    Example:
        logsift logs clean --dry-run
        logsift logs clean --days 30
        logsift logs clean --days 7
    """
    from logsift.commands.logs import clean_logs

    clean_logs(days=days, dry_run=dry_run)


@logs_app.command('browse')
def logs_browse(
    context: Annotated[str | None, typer.Option('-c', '--context', help='Filter by context')] = None,
    view: Annotated[bool, typer.Option('--view', help='Browse file content (default: analyze)')] = False,
) -> None:
    """Browse cached log files interactively with fzf.

    Requires fzf to be installed.

    Example:
        logsift logs browse
        logsift logs browse --context monitor
        logsift logs browse --view
    """
    from logsift.commands.logs import browse_logs

    action = 'view' if view else 'select'
    browse_logs(context=context, action=action)


if __name__ == '__main__':
    app()
