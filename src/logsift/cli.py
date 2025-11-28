"""Main CLI application using Typer.

This module defines the primary logsift command-line interface with subcommands for monitoring, analyzing, and managing logs.
"""

from typing import Annotated

import click
import typer
from rich.console import Console
from typer.core import TyperGroup

from logsift import __version__
from logsift.cli_formatter import format_help_with_colors


class ColoredTyperGroup(TyperGroup):
    """Custom TyperGroup that uses our uv-style colored formatter."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        """Override help formatting to use our custom colored formatter."""
        help_text = format_help_with_colors(ctx)
        # Use click.echo to properly handle ANSI color codes
        click.echo(help_text, color=True)


app = typer.Typer(
    name='logsift',
    help='LLM-optimized log analysis for automated error diagnosis.',
    add_completion=False,
    rich_markup_mode=None,  # Disable Rich markup
    pretty_exceptions_enable=False,  # Disable Rich exceptions
    epilog='Use `logsift help <command>` for more details on a specific command.',
    cls=ColoredTyperGroup,  # Use our custom colored formatter
)
console = Console()


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        console.print(f'logsift version {__version__}')
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        None,
        '--version',
        '-V',
        callback=version_callback,
        is_eager=True,
        help='Display the logsift version',
    ),
    verbose: bool = typer.Option(
        False,
        '--verbose',
        '-v',
        help='Use verbose output',
        envvar='LOGSIFT_VERBOSE',
    ),
    quiet: bool = typer.Option(
        False,
        '--quiet',
        '-q',
        help='Use quiet output (errors only)',
        envvar='LOGSIFT_QUIET',
    ),
    cache_dir: str | None = typer.Option(
        None,
        '--cache-dir',
        help='Path to the cache directory',
        envvar='LOGSIFT_CACHE_DIR',
    ),
    no_cache: bool = typer.Option(
        False,
        '--no-cache',
        help='Avoid reading from or writing to the cache',
        envvar='LOGSIFT_NO_CACHE',
    ),
    config_file: str | None = typer.Option(
        None,
        '--config-file',
        help='Path to a logsift.toml configuration file',
        envvar='LOGSIFT_CONFIG_FILE',
    ),
    no_config: bool = typer.Option(
        False,
        '--no-config',
        help='Avoid loading configuration files',
        envvar='LOGSIFT_NO_CONFIG',
    ),
) -> None:
    """logsift - Intelligent log analysis for agentic workflows.

    An LLM-optimized log analysis and command monitoring tool designed for
    Claude Code and other AI agents. Extracts actionable insights from verbose
    logs and provides structured output optimized for LLMs.
    """
    # Store options in context for subcommands to use
    ctx.obj = {
        'verbose': verbose,
        'quiet': quiet,
        'cache_dir': cache_dir,
        'no_cache': no_cache,
        'config_file': config_file,
        'no_config': no_config,
    }

    # If no subcommand is provided, show help (like uv does)
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


@app.command()
def monitor(
    command: Annotated[list[str], typer.Argument(help='Command to monitor')],
    name: Annotated[
        str | None,
        typer.Option(
            '-n',
            '--name',
            help='Name for this monitoring session (default: auto-generated timestamp)',
            envvar='LOGSIFT_SESSION_NAME',
        ),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            '--format',
            help='Output format: auto (detects TTY), json (for LLMs), markdown (for humans), plain (no colors)',
            envvar='LOGSIFT_OUTPUT_FORMAT',
        ),
    ] = 'auto',
    notify: Annotated[
        bool,
        typer.Option(
            '--notify',
            help='Send desktop notification on completion (requires notify-send or osascript)',
        ),
    ] = False,
    external_log: Annotated[
        str | None,
        typer.Option(
            '--external-log',
            help='Tail external log file while monitoring (merges command output with external logs)',
        ),
    ] = None,
    append: Annotated[
        bool,
        typer.Option(
            '--append',
            help='Append to existing log instead of creating new (useful for iterative debugging)',
        ),
    ] = False,
) -> None:
    """Monitor a command and analyze its output for errors.

    Runs a command while capturing both stdout and stderr, then analyzes the
    output using pattern matching to identify errors, warnings, and actionable
    items. Results are cached and can be re-analyzed later.

    Examples:
        # Monitor a build command
        logsift monitor -- make build

        # Monitor with custom session name
        logsift monitor -n install-deps -- npm install

        # Get JSON output for Claude Code
        logsift monitor --format json -- pytest tests/

        # Monitor with external log file
        logsift monitor --external-log /var/log/app.log -- npm start

        # Append to existing session (useful for retry workflows)
        logsift monitor -n build --append -- make

        # Get notification when long-running command completes
        logsift monitor --notify -- docker build -t myapp .
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
    log_file: Annotated[
        str | None,
        typer.Argument(help='Path to log file to analyze (optional if using --interactive or fzf)'),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            '--format',
            help='Output format: auto (detects TTY), json (for LLMs), markdown (for humans), plain (no colors)',
            envvar='LOGSIFT_OUTPUT_FORMAT',
        ),
    ] = 'auto',
    interactive: Annotated[
        bool,
        typer.Option(
            '-i',
            '--interactive',
            help='Use fzf to interactively select from cached logs',
        ),
    ] = False,
) -> None:
    """Analyze an existing log file for errors and patterns.

    Analyzes a log file (from disk or cache) and extracts errors, warnings,
    and actionable items using pattern matching. Works with any log format
    (JSON, structured, plain text).

    If no log file is provided and fzf is installed, shows an interactive
    selector for cached logs.

    Examples:
        # Analyze a specific log file
        logsift analyze /var/log/app.log

        # Analyze with JSON output for LLM consumption
        logsift analyze --format json build.log

        # Interactive mode (select from cached logs)
        logsift analyze --interactive
        logsift analyze  # Same as above if fzf is available

        # Analyze previously monitored command output
        logsift analyze ~/.cache/logsift/monitor/build-20241128_120000_000000.log
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
    interval: Annotated[
        int,
        typer.Option(
            '-i',
            '--interval',
            help='Update interval in seconds (how often to check for new lines)',
            envvar='LOGSIFT_WATCH_INTERVAL',
        ),
    ] = 1,
) -> None:
    """Watch and analyze a log file in real-time as it grows.

    Continuously monitors a log file for new lines and analyzes them as they
    appear. Useful for monitoring long-running services or applications.
    Press Ctrl+C to stop watching.

    Examples:
        # Watch application log with 1-second updates
        logsift watch /var/log/app.log

        # Watch with custom interval (less CPU usage)
        logsift watch --interval 5 /var/log/nginx/error.log

        # Watch local development server
        logsift watch ./logs/development.log
    """
    from logsift.commands.watch import watch_log

    watch_log(log_file, interval=interval)


# Create logs command group
logs_app = typer.Typer(
    help='Manage cached log files',
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    cls=ColoredTyperGroup,  # Use our custom colored formatter
)
app.add_typer(logs_app, name='logs')


@logs_app.command('list')
def logs_list(
    context: Annotated[
        str | None,
        typer.Option(
            '-c',
            '--context',
            help='Filter by context (monitor, analyze, watch)',
        ),
    ] = None,
    format: Annotated[
        str,
        typer.Option(
            '--format',
            help='Output format: table (default), json (for scripts), plain (simple list)',
        ),
    ] = 'table',
) -> None:
    """List all cached log files with metadata.

    Shows all logs stored in the cache directory with their size, modification
    time, and context. Useful for finding previously monitored sessions.

    Examples:
        # List all cached logs
        logsift logs list

        # List only monitor logs
        logsift logs list --context monitor

        # Get JSON output for scripting
        logsift logs list --format json

        # Simple list of paths
        logsift logs list --format plain
    """
    from logsift.commands.logs import list_logs

    list_logs(context=context, output_format=format)


@logs_app.command('clean')
def logs_clean(
    days: Annotated[
        int,
        typer.Option(
            '-d',
            '--days',
            help='Delete logs older than N days (default: 90)',
            envvar='LOGSIFT_RETENTION_DAYS',
        ),
    ] = 90,
    dry_run: Annotated[
        bool,
        typer.Option(
            '--dry-run',
            help='Show what would be deleted without actually deleting',
        ),
    ] = False,
) -> None:
    """Clean old log files from cache to free up disk space.

    Deletes cached logs older than the specified number of days. Use --dry-run
    to preview what would be deleted before actually removing files.

    Examples:
        # Preview what would be deleted (safe)
        logsift logs clean --dry-run

        # Delete logs older than 30 days
        logsift logs clean --days 30

        # Aggressive cleanup (only keep last week)
        logsift logs clean --days 7

        # Use default retention (90 days)
        logsift logs clean
    """
    from logsift.commands.logs import clean_logs

    clean_logs(days=days, dry_run=dry_run)


@logs_app.command('browse')
def logs_browse(
    context: Annotated[
        str | None,
        typer.Option(
            '-c',
            '--context',
            help='Filter by context (monitor, analyze, watch)',
        ),
    ] = None,
    view: Annotated[
        bool,
        typer.Option(
            '--view',
            help='Browse raw file content instead of analyzing (useful for inspection)',
        ),
    ] = False,
) -> None:
    """Browse and search cached log files interactively using fzf.

    Opens an interactive fuzzy-finder interface to search and select from
    cached logs. By default, analyzes the selected file. Use --view to browse
    raw content instead.

    Requires fzf to be installed (install with: brew install fzf).

    Examples:
        # Browse and analyze a cached log
        logsift logs browse

        # Browse only monitor logs
        logsift logs browse --context monitor

        # Browse raw file content (no analysis)
        logsift logs browse --view

        # Search through monitor logs interactively
        logsift logs browse -c monitor
    """
    from logsift.commands.logs import browse_logs

    action = 'view' if view else 'select'
    browse_logs(context=context, action=action)


if __name__ == '__main__':
    app()
