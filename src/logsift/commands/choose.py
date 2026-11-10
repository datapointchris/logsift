"""The gate every `choose` passes before it opens fzf."""

import sys

import typer
from rich.console import Console

from logsift.utils.fzf import is_fzf_available

stderr_console = Console(stderr=True)


def require_picker(instead: str) -> None:
    """Exit unless a person at a terminal can pick, naming the command that needs no picker.

    A picker waiting on a closed stdin would hang its caller, so without a terminal this exits 2
    at once. Without fzf it exits 1 and says to install it.

    Args:
        instead: The command that names the file outright, such as "`logsift logs latest <name>`"
    """
    if not sys.stdin.isatty():
        stderr_console.print(f'[red]Error: choose needs a terminal to pick on. Without one, run {instead}[/red]')
        raise typer.Exit(2)
    if not is_fzf_available():
        stderr_console.print('[red]Error: choose needs fzf, which is not on PATH[/red]')
        stderr_console.print(f'Install fzf (https://github.com/junegunn/fzf#installation), or run {instead}')
        raise typer.Exit(1)
