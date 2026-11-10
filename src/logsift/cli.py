"""Main CLI application using Typer.

This module defines the primary logsift command-line interface with subcommands for monitoring, analyzing, and managing logs.
"""

from typing import Annotated
from typing import cast

import typer
from pyselfupdate import Config
from pyselfupdate import notify
from pyselfupdate.typercmd import add_update_command
from rich.console import Console

from logsift import __version__
from logsift import xdg_dirs
from logsift.cache.manager import SavedKind
from logsift.commands.analyze import analyze_log
from logsift.commands.analyze import log_file_for
from logsift.commands.analyze import stream_analyze_log
from logsift.commands.analyzed import choose_analysis
from logsift.commands.analyzed import clean_analyzed
from logsift.commands.analyzed import show_latest_analyzed
from logsift.commands.config import show_config
from logsift.commands.format_commands import create_format_commands
from logsift.commands.listing import LimitOption
from logsift.commands.listing import ListFormat
from logsift.commands.listing import ListFormatOption
from logsift.commands.listing import print_listing
from logsift.commands.logs import choose_log
from logsift.commands.logs import clean_logs
from logsift.commands.logs import show_latest_log
from logsift.commands.monitor import monitor_command
from logsift.config.loader import ConfigError
from logsift.config.loader import default_map
from logsift.config.loader import load_user_config
from logsift.output.analysis_format import AnalysisFormat

app = typer.Typer(
    name='logsift',
    help=(
        'LLM-optimized log analysis for automated error diagnosis.\n\n'
        'Start with `logsift monitor -- <command>`. It runs the command, saves its output '
        'and prints the errors it found. Reach for `logsift analyze` only when the log '
        'already exists: a file another tool wrote, or `--latest` to re-run the patterns '
        'over the last capture.\n\n'
        '`logs` holds what a run printed, and `analyzed` holds what logsift found in it, '
        'rendered as Markdown. Open `logs` to read the raw output, and `analyzed` to reread the '
        'errors without running the command again. `raw`, `json`, `toon` and `md` each show one '
        'kind of saved file exactly as it is stored: the raw log, or the analysis as '
        '`--format json`, `toon` or `markdown` printed it.'
    ),
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    epilog=(
        '\b\n'
        'Examples:\n'
        '  # Run a build, then print the errors it hit\n'
        '  logsift monitor -- make build\n'
        '  # Print only the analysis, as JSON\n'
        '  logsift monitor --minimal --format json -- pytest tests/\n'
        '  # Re-run the patterns over the last capture\n'
        '  logsift analyze --latest\n'
        '  # Reread the newest analysis of a run named build\n'
        '  logsift analyzed latest build\n\n'
        '`logsift <command> --help` describes one command.'
    ),
)
console = Console()

# Shared by the `update` command and the daily check in the callback below, so
# the notice cannot name a release the update command would not install.
UPDATE_CONFIG = Config(tool='logsift', owner='datapointchris')
add_update_command(app, UPDATE_CONFIG)

# Help sections, named for what their commands are for. Typer lists a command with no panel,
# such as `help` and `update`, first, under "Commands".
ANALYZE_PANEL = 'Analyze'
BROWSE_PANEL = 'Browse saved runs'


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        console.print(f'logsift {__version__}')
        raise typer.Exit()


@app.callback()
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
) -> None:
    """Load config.toml for every command, and queue the daily update notice."""
    # Never raises and never prints an error; the notice is deferred to exit so
    # it lands after the command's own output. `logsift update` is the only
    # place an update failure is reported, and is skipped here because it is
    # about to do the thing the notice would suggest.
    if ctx.invoked_subcommand != 'update':
        notify(UPDATE_CONFIG)

    # Click builds the subcommand's context after this callback, so it inherits this default_map.
    try:
        ctx.default_map = default_map(load_user_config(xdg_dirs.config_file()))
    except ConfigError as fault:
        typer.echo(f'Error: {fault}', err=True)
        raise typer.Exit(1) from None


@app.command(rich_help_panel=ANALYZE_PANEL, no_args_is_help=True)
def monitor(
    ctx: typer.Context,
    command: Annotated[list[str] | None, typer.Argument(help='Command to monitor')] = None,
    name: Annotated[
        str | None,
        typer.Option(
            '-n',
            '--name',
            help='Name for this run, used in its saved file names. Taken from the command when omitted',
            envvar='LOGSIFT_SESSION_NAME',
        ),
    ] = None,
    format: Annotated[
        AnalysisFormat,
        typer.Option(
            '--format',
            help='How to print the analysis. auto is markdown on a terminal and toon when piped',
            envvar='LOGSIFT_OUTPUT_FORMAT',
        ),
    ] = AnalysisFormat.AUTO,
    stream: Annotated[
        bool,
        typer.Option(
            '--stream',
            help='Print every line of output as it arrives, instead of a progress report every --update-interval',
        ),
    ] = False,
    update_interval: Annotated[
        int,
        typer.Option(
            '--update-interval',
            help='Seconds between progress updates when not streaming',
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
    append: Annotated[
        bool,
        typer.Option(
            '--append',
            help='Append to existing log instead of creating new (useful for iterative debugging)',
        ),
    ] = False,
    minimal: Annotated[
        bool,
        typer.Option(
            '--minimal',
            help='Suppress all progress output, only show final analysis result (ideal for LLM workflows)',
        ),
    ] = False,
) -> None:
    """Monitor a command and analyze its output for errors

    Runs a command while capturing both stdout and stderr, then analyzes the
    output using pattern matching to identify errors and warnings. Results are
    cached and can be re-analyzed later.

    By default, shows periodic progress updates every 60 seconds. Use --stream
    to see all output in real-time.

    \b
    Examples:
        logsift monitor -- make build
        logsift monitor --stream -- npm install
        logsift monitor --minimal -- pre-commit run --files file.py
        logsift monitor --format json -- docker build -t myapp .
    """
    monitor_command(
        command or [],
        name=name,
        output_format=format,
        stream=stream,
        update_interval=update_interval,
        minimal=minimal,
        notify=notify,
        append=append,
    )


@app.command(rich_help_panel=ANALYZE_PANEL, no_args_is_help=True)
def analyze(
    ctx: typer.Context,
    log_file: Annotated[str | None, typer.Argument(help='The log file to analyze')] = None,
    latest: Annotated[bool, typer.Option('--latest', help='Analyze the newest log monitor captured')] = False,
    choose: Annotated[bool, typer.Option('--choose', help='Pick a log monitor captured with fzf. Needs a terminal')] = False,
    format: Annotated[
        AnalysisFormat,
        typer.Option(
            '--format',
            help='How to print the analysis. auto is markdown on a terminal and toon when piped',
            envvar='LOGSIFT_OUTPUT_FORMAT',
        ),
    ] = AnalysisFormat.AUTO,
    stream: Annotated[
        bool,
        typer.Option(
            '--stream',
            help='Stream analyze: analyze entire file, then continue as it grows',
        ),
    ] = False,
    interval: Annotated[
        int,
        typer.Option(
            '-i',
            '--interval',
            help='Update interval in seconds when streaming',
        ),
    ] = 1,
    no_save: Annotated[
        bool,
        typer.Option(
            '--no-save',
            help='Do not save analysis results to cache (useful for testing)',
        ),
    ] = False,
) -> None:
    """Analyze an existing log file for errors and patterns

    Analyzes a log file (from disk or cache) and extracts errors and warnings,
    with a fix hint where a pattern has one. Works with any log format
    (JSON, structured, plain text).

    By default, analysis results are saved in all formats (JSON, TOON, Markdown).
    Use --no-save to skip saving (useful when testing pattern changes).

    \b
    Examples:
        logsift analyze /var/log/app.log
        logsift analyze --format json build.log
        logsift analyze --latest
        logsift analyze --latest --no-save
        logsift analyze --latest --stream
        logsift analyze --choose
    """
    log_file = log_file_for(log_file, latest, choose, stream)
    if stream:
        stream_analyze_log(log_file, interval=interval)
    else:
        analyze_log(log_file, output_format=format, save=not no_save)


# Create logs command group
logs_app = typer.Typer(
    help='Manage cached log files',
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
app.add_typer(logs_app, name='logs', rich_help_panel=BROWSE_PANEL)


# Create analyzed command group
analyzed_app = typer.Typer(
    help='Manage saved analysis results',
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
app.add_typer(analyzed_app, name='analyzed', rich_help_panel=BROWSE_PANEL)


@logs_app.command('list')
def logs_list(format: ListFormatOption = ListFormat.TABLE, limit: LimitOption = None) -> None:
    """List the cached raw logs, newest first, with their size and modification time.

    \b
    Examples:
        # The ten newest logs
        logsift logs list -n 10

        # Every log, as JSON for a script
        logsift logs list --format json

        # One tab-separated path, size and time per log
        logsift logs list --format plain
    """
    print_listing(SavedKind.RAW, format, limit, 'Cached Log Files', 'No cached logs found')


@logs_app.command('clean')
def logs_clean(
    days: Annotated[
        int,
        typer.Option(
            '-d',
            '--days',
            help='Delete logs older than N days',
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

    \b
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
    clean_logs(days=days, dry_run=dry_run)


@logs_app.command('choose')
def logs_choose(
    view: Annotated[bool, typer.Option('--view', help="Search the chosen log's lines in fzf instead of analyzing it")] = False,
    tail: Annotated[bool, typer.Option('--tail', help='Tail the chosen log in real-time instead of analyzing it')] = False,
    interval: Annotated[int, typer.Option('-i', '--interval', help='Update interval in seconds when tailing')] = 1,
) -> None:
    """Pick a cached log with fzf, then analyze it, search it or tail it.

    Needs a terminal and fzf. Without a terminal it exits 2 and names the
    command that takes the log by name instead.

    \b
    Examples:
        # Pick a log and analyze it
        logsift logs choose

        # Pick a log and search its lines
        logsift logs choose --view

        # Pick a log and tail it
        logsift logs choose --tail
    """
    if tail:
        action = 'tail'
    elif view:
        action = 'view'
    else:
        action = 'select'

    choose_log(action=action, interval=interval)


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
            help='Update interval in seconds when tailing',
        ),
    ] = 1,
) -> None:
    """Show the most recent log file, optionally tailing it in real-time.

    Finds the latest log file by name and displays its raw contents. Use --tail
    to watch it in real-time. If no name is provided, uses the absolute latest
    log across all cached logs.

    \b
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
    show_latest_log(name, tail, interval)


@analyzed_app.command('list')
def analyzed_list(format: ListFormatOption = ListFormat.TABLE, limit: LimitOption = None) -> None:
    """List the saved analyses by their JSON file, newest first, with their size and modification time.

    \b
    Examples:
        logsift analyzed list
        logsift analyzed list -n 5 --format json
    """
    print_listing(SavedKind.JSON, format, limit, 'Saved Analysis Results', 'No saved analyses found')


@analyzed_app.command('choose')
def analyzed_choose() -> None:
    """Pick a saved analysis with fzf and page it as Markdown.

    Needs a terminal and fzf. Without a terminal it exits 2 and names the
    command that takes the analysis by name instead.

    \b
    Examples:
        logsift analyzed choose
    """
    choose_analysis()


@analyzed_app.command('latest')
def analyzed_latest(
    name: Annotated[
        str | None,
        typer.Argument(help='Name to filter by (substring match). If omitted, shows absolute latest'),
    ] = None,
) -> None:
    """Show the most recent saved analysis.

    Displays the latest saved analysis result, optionally filtered by name.

    \b
    Examples:
        # Show absolute latest analysis
        logsift analyzed latest

        # Show latest analysis matching "build"
        logsift analyzed latest build
    """
    show_latest_analyzed(name)


@analyzed_app.command('clean')
def analyzed_clean(
    days: Annotated[
        int,
        typer.Option(
            '-d',
            '--days',
            help='Delete analyses older than this many days',
        ),
    ] = 30,
    dry_run: Annotated[
        bool,
        typer.Option(
            '--dry-run',
            help='Show what would be deleted without actually deleting',
        ),
    ] = False,
) -> None:
    """Clean old saved analyses from cache.

    Removes the json, toon and md analyses older than the specified number of days.
    Raw logs are left for 'logsift logs clean'.
    Use --dry-run to preview what would be deleted.

    \b
    Examples:
        # Clean analyses older than 30 days
        logsift analyzed clean

        # Clean analyses older than 7 days
        logsift analyzed clean --days 7

        # Preview what would be deleted
        logsift analyzed clean --dry-run
    """
    clean_analyzed(days=days, dry_run=dry_run)


for kind in SavedKind:
    app.add_typer(create_format_commands(kind), name=kind, rich_help_panel=BROWSE_PANEL)


@app.command('config')
def config(ctx: typer.Context) -> None:
    """Print each setting's resolved value and the layer that set it.

    A value comes from its flag, then its environment variable, then
    config.toml in $XDG_CONFIG_HOME/logsift, then logsift's default. FROM
    names the layer that answered, and FILE KEY the config.toml key that
    would set it. A config.toml that fails to parse, or names a key logsift
    does not read, stops every command and names the problem.

    \b
    Examples:
        logsift config
        LOGSIFT_OUTPUT_FORMAT=json logsift config
    """
    show_config(ctx)


@app.command()
def help(
    ctx: typer.Context,
    command: Annotated[str | None, typer.Argument(help='Command to get help for')] = None,
) -> None:
    """Display help information for logsift commands.

    \b
    Examples:
        logsift help
        logsift help monitor
        logsift help analyze
    """
    root_ctx = ctx.parent or ctx
    if command is None:
        typer.echo(root_ctx.get_help())
        return

    # Typer builds the root of an app with subcommands as a TyperGroup.
    group = cast(typer.core.TyperGroup, root_ctx.command)
    cmd = group.get_command(root_ctx, command)
    if cmd is None:
        # A usage error exits 2, so a caller can tell a mistyped name from a command that ran and failed.
        known = ', '.join(group.list_commands(root_ctx))
        typer.echo(f'Error: Unknown command "{command}". The commands are: {known}', err=True)
        raise typer.Exit(2)
    # The command's own context class, which is the one Typer would build for it.
    with cmd.context_class(cmd, info_name=command, parent=root_ctx) as cmd_ctx:
        typer.echo(cmd_ctx.get_help())


if __name__ == '__main__':
    app()
