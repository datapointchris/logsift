"""Custom CLI help formatter matching uv's style.

Provides colored, well-structured help output without boxes or excessive formatting.
"""

from __future__ import annotations

import click
from click import Context


class UVStyleHelpFormatter(click.HelpFormatter):
    """Help formatter that matches uv's clean, colored style."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_section = None

    def write_heading(self, heading: str) -> None:
        """Write a section heading in bright green."""
        if heading:
            # Use click.style with color=True to force ANSI codes
            styled = click.style(f'{heading}:', fg='bright_green', bold=True)
            # Get the ANSI-encoded string
            self.write(f'{styled}\n')

    def write_dl(
        self,
        rows: list[tuple[str, str]],
        col_max: int = 30,
        col_spacing: int = 2,
    ) -> None:
        """Write a definition list with proper alignment and colors."""
        # Calculate max width for first column
        widths = [len(row[0]) for row in rows]
        max_width = min(max(widths) if widths else 0, col_max)

        for first, second in rows:
            # Color command names blue in Commands section
            if self.current_section == 'Commands':
                # Use click.style and get actual length for padding
                colored_first = click.style(first, fg='bright_blue')
                first_len = len(first)  # Length without ANSI codes
                # Write with proper indentation
                self.write(f'  {colored_first}')
            else:
                first_len = len(first)
                self.write(f'  {first}')

            if second:
                # Add spacing and description
                padding = ' ' * (max_width - first_len + col_spacing)
                self.write(f'{padding}{second}')
            self.write('\n')


def format_help_with_colors(ctx: Context) -> str:
    """Format help text with uv-style colors and structure."""
    formatter = UVStyleHelpFormatter(width=ctx.terminal_width, max_width=120)

    # Write description
    if ctx.command.help:
        formatter.write_paragraph()
        formatter.write_text(ctx.command.help)

    # Write usage
    formatter.write_paragraph()
    formatter.write_heading('Usage')
    formatter.current_section = 'Usage'
    usage_text = ctx.command.get_usage(ctx).replace('Usage: ', '')
    formatter.write(f'  {usage_text}\n')

    # Get command object
    if isinstance(ctx.command, click.Group):
        # Main help - show commands with expanded descriptions
        commands = []
        for name in ctx.command.list_commands(ctx):
            cmd = ctx.command.get_command(ctx, name)
            if cmd and not cmd.hidden:
                # Get full help text and extract first paragraph + common options if present
                full_help = cmd.help or ''
                help_lines = full_help.split('\n\n')  # Split by paragraphs

                # Take first paragraph as summary
                summary = help_lines[0].replace('\n', ' ').strip() if help_lines else ''

                commands.append((name, summary))

        if commands:
            formatter.write_paragraph()
            formatter.write_heading('Commands')
            formatter.current_section = 'Commands'
            formatter.write_dl(commands)

    # Write options grouped by category
    cache_options: list[tuple[str, str]] = []
    output_options: list[tuple[str, str]] = []
    global_options: list[tuple[str, str]] = []

    for param in ctx.command.get_params(ctx):
        if isinstance(param, click.Option):
            opts = param.get_help_record(ctx)
            if not opts:
                continue

            opt_name, help_text = opts

            # Environment variables are already shown by Typer as [env var: X]
            # We don't need to add them again - Typer handles this automatically

            # Group options by name patterns
            if '--cache' in opt_name or '--no-cache' in opt_name:
                cache_options.append((opt_name, help_text))
            elif '--format' in opt_name or '--notify' in opt_name:
                output_options.append((opt_name, help_text))
            elif '--config' in opt_name or '--verbose' in opt_name or '--quiet' in opt_name:
                global_options.append((opt_name, help_text))
            else:
                global_options.append((opt_name, help_text))

    # Write option groups in order
    if cache_options:
        formatter.write_paragraph()
        formatter.write_heading('Cache options')
        formatter.current_section = 'Cache options'
        formatter.write_dl(cache_options)

    if output_options:
        formatter.write_paragraph()
        formatter.write_heading('Output options')
        formatter.current_section = 'Output options'
        formatter.write_dl(output_options)

    if global_options:
        formatter.write_paragraph()
        formatter.write_heading('Global options')
        formatter.current_section = 'Global options'
        formatter.write_dl(global_options)

    # Write epilog
    if ctx.command.epilog:
        formatter.write_paragraph()
        formatter.write_text(ctx.command.epilog)

    return formatter.getvalue()
