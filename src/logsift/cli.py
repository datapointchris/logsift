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
    ctx: typer.Context,
    command: Annotated[list[str] | None, typer.Argument(help='Command to monitor')] = None,
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
    stream: Annotated[
        bool,
        typer.Option(
            '--stream',
            help='Stream all output to terminal in real-time (default: show periodic updates)',
        ),
    ] = False,
    update_interval: Annotated[
        int,
        typer.Option(
            '--update-interval',
            help='Seconds between progress updates when not streaming (default: 60)',
            envvar='LOGSIFT_UPDATE_INTERVAL',
        ),
    ] = 60,
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
    """Monitor a command and analyze its output for errors

    Runs a command while capturing both stdout and stderr, then analyzes the
    output using pattern matching to identify errors, warnings, and actionable
    items. Results are cached and can be re-analyzed later.

    By default, shows periodic progress updates every 60 seconds. Use --stream
    to see all output in real-time.

    Common Options:
        -n, --name          Name for this monitoring session
        --format            Output format: auto, json, markdown, plain
        --stream            Stream all output in real-time
        --update-interval   Seconds between updates (default: 60)
        --notify            Send desktop notification on completion
        --external-log      Tail external log file while monitoring
        --append            Append to existing log

    Examples:
        logsift monitor -- make build
        logsift monitor --stream -- npm install
        logsift monitor --update-interval 10 -- pytest tests/
        logsift monitor --format json -- docker build -t myapp .
    """
    from logsift.cli_formatter import format_help_with_colors

    # Show help if no command provided
    if command is None or len(command) == 0:
        help_text = format_help_with_colors(ctx)
        click.echo(help_text, color=True)
        raise typer.Exit()

    from logsift.commands.monitor import monitor_command

    monitor_command(
        command,
        name=name,
        output_format=format,
        stream=stream,
        update_interval=update_interval,
        notify=notify,
        external_log=external_log,
        append=append,
    )


@app.command()
def analyze(
    ctx: typer.Context,
    log_file: Annotated[
        str | None,
        typer.Argument(help='Path to log file to analyze, or "latest" for most recent log (optional if using --interactive)'),
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
    """Analyze an existing log file for errors and patterns

    Analyzes a log file (from disk or cache) and extracts errors, warnings,
    and actionable items using pattern matching. Works with any log format
    (JSON, structured, plain text).

    Common Options:
        --format            Output format: auto, json, markdown, plain
        -i, --interactive   Use fzf to select log file

    Examples:
        logsift analyze /var/log/app.log
        logsift analyze --format json build.log
        logsift analyze latest
        logsift analyze --interactive
        logsift analyze  # Interactive if fzf is available
    """
    from logsift.cli_formatter import format_help_with_colors

    # Show help if no arguments provided
    if not log_file and not interactive:
        help_text = format_help_with_colors(ctx)
        click.echo(help_text, color=True)
        raise typer.Exit()

    from logsift.commands.analyze import analyze_log

    # Handle "latest" shortcut
    if log_file == 'latest':
        from logsift.cache.manager import CacheManager

        cache = CacheManager()
        latest_log = cache.get_absolute_latest_log()

        if not latest_log:
            console.print('[red]Error: No cached logs found[/red]')
            raise typer.Exit(1)

        log_file = str(latest_log)
        console.print(f'[cyan]Analyzing latest log: {log_file}[/cyan]\n')

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
    ctx: typer.Context,
    log_file: Annotated[str | None, typer.Argument(help='Path to log file to watch')] = None,
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
    """Watch and analyze a log file in real-time as it grows

    Continuously monitors a log file for new lines and analyzes them as they
    appear. Useful for monitoring long-running services or applications.
    Press Ctrl+C to stop watching.

    Common Options:
        -i, --interval      Update interval in seconds (default: 1)

    Examples:
        logsift watch /var/log/app.log
        logsift watch --interval 5 /var/log/nginx/error.log
        logsift watch ./logs/development.log
    """
    from logsift.cli_formatter import format_help_with_colors

    # Show help if no log file provided
    if not log_file:
        help_text = format_help_with_colors(ctx)
        click.echo(help_text, color=True)
        raise typer.Exit()

    from logsift.commands.watch import watch_log

    watch_log(log_file, interval=interval)


# Create logs command group
logs_app = typer.Typer(
    help='Manage cached log files',
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
    cls=ColoredTyperGroup,  # Use our custom colored formatter
    invoke_without_command=True,
)
app.add_typer(logs_app, name='logs')


@logs_app.callback()
def logs_callback(ctx: typer.Context) -> None:
    """Manage cached log files."""
    # Show help if no subcommand provided
    if ctx.invoked_subcommand is None:
        from logsift.cli_formatter import format_help_with_colors

        help_text = format_help_with_colors(ctx)
        click.echo(help_text, color=True)
        raise typer.Exit()


@logs_app.command('list')
def logs_list(
    format: Annotated[
        str,
        typer.Option(
            '--format',
            help='Output format: table (default), json (for scripts), plain (simple list)',
        ),
    ] = 'table',
) -> None:
    """List all cached log files with metadata.

    Shows all logs stored in the cache directory with their size and modification
    time. Useful for finding previously monitored sessions.

    Examples:
        # List all cached logs
        logsift logs list

        # Get JSON output for scripting
        logsift logs list --format json

        # Simple list of paths
        logsift logs list --format plain
    """
    from logsift.commands.logs import list_logs

    list_logs(output_format=format)


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

        # Browse raw file content (no analysis)
        logsift logs browse --view
    """
    from logsift.commands.logs import browse_logs

    action = 'view' if view else 'select'
    browse_logs(action=action)


@logs_app.command('latest')
def logs_latest(
    name: Annotated[
        str | None,
        typer.Argument(help='Name of log to find (e.g., "echo", "pytest"). If omitted, shows absolute latest log'),
    ] = None,
    tail: Annotated[
        bool,
        typer.Option(
            '--tail',
            help='Tail the log file in real-time instead of displaying it',
        ),
    ] = False,
    interval: Annotated[
        int,
        typer.Option(
            '-i',
            '--interval',
            help='Update interval in seconds when tailing (default: 1)',
        ),
    ] = 1,
) -> None:
    """Show the most recent log file, optionally tailing it in real-time.

    Finds the latest log file by name and displays its raw contents. Use --tail
    to watch it in real-time. If no name is provided, uses the absolute latest
    log across all cached logs.

    Examples:
        # Show the latest pytest log
        logsift logs latest pytest

        # Tail the latest build log in real-time
        logsift logs latest make --tail

        # Show the absolute latest log (any name)
        logsift logs latest

        # Tail with custom update interval
        logsift logs latest pytest --tail --interval 5
    """
    from logsift.cache.manager import CacheManager
    from logsift.commands.watch import tail_log

    cache = CacheManager()

    # Get the latest log
    if name:
        log_path = cache.get_latest_log(name)
        if not log_path:
            console.print(f'[red]Error: No logs found for name "{name}"[/red]')
            raise typer.Exit(1)
    else:
        log_path = cache.get_absolute_latest_log()
        if not log_path:
            console.print('[red]Error: No cached logs found[/red]')
            raise typer.Exit(1)

    console.print(f'[cyan]Latest log: {log_path}[/cyan]\n')

    # Either tail or show the raw log
    if tail:
        tail_log(str(log_path), interval=interval)
    else:
        # Show raw log contents
        with open(log_path) as f:
            print(f.read(), end='')


@app.command()
def help(
    ctx: typer.Context,
    command: Annotated[str | None, typer.Argument(help='Command to get help for')] = None,
) -> None:
    """Display help information for logsift commands.

    Examples:
        logsift help
        logsift help monitor
        logsift help analyze
    """
    from logsift.cli_formatter import format_help_with_colors

    # Get the Click context for the main app
    click_ctx = ctx.parent or ctx

    if command is None:
        # Show main help using custom formatter
        help_text = format_help_with_colors(click_ctx)
        click.echo(help_text, color=True)
    else:
        # Try to get the command from the group
        if hasattr(click_ctx.command, 'get_command'):
            cmd = click_ctx.command.get_command(click_ctx, command)
            if cmd:
                # Create context for the command and show its help with custom formatter
                with click.Context(cmd, info_name=command, parent=click_ctx) as cmd_ctx:
                    help_text = format_help_with_colors(cmd_ctx)
                    click.echo(help_text, color=True)
            else:
                console.print(f'[red]Error: Unknown command "{command}"[/red]')
                console.print('[dim]Run "logsift help" to see available commands[/dim]')
                raise typer.Exit(1)
        else:
            console.print(f'[red]Error: Unknown command "{command}"[/red]')
            console.print('[dim]Run "logsift help" to see available commands[/dim]')
            raise typer.Exit(1)


if __name__ == '__main__':
    app()
