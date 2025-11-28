"""Color output helpers for terminal display.

Provides utilities for colored output using rich.
"""

from rich.console import Console

console = Console()


def print_error(message: str) -> None:
    """Print an error message in red.

    Args:
        message: Error message to print
    """
    console.print(f'[red]❌ {message}[/red]')


def print_warning(message: str) -> None:
    """Print a warning message in yellow.

    Args:
        message: Warning message to print
    """
    console.print(f'[yellow]⚠️  {message}[/yellow]')


def print_success(message: str) -> None:
    """Print a success message in green.

    Args:
        message: Success message to print
    """
    console.print(f'[green]✅ {message}[/green]')


def print_info(message: str) -> None:
    """Print an info message in blue.

    Args:
        message: Info message to print
    """
    console.print(f'[blue]ℹ️  {message}[/blue]')
