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
        # Main help - show commands
        commands = []
        for name in ctx.command.list_commands(ctx):
            cmd = ctx.command.get_command(ctx, name)
            if cmd and not cmd.hidden:
                help_text = cmd.get_short_help_str(limit=100)
                commands.append((name, help_text))

        if commands:
            formatter.write_paragraph()
            formatter.write_heading('Commands')
            formatter.current_section = 'Commands'
            formatter.write_dl(commands)

    # Write options grouped by category
    option_groups: dict[str, list[tuple[str, str]]] = {}
    for param in ctx.command.get_params(ctx):
        if isinstance(param, click.Option):
            # Group options
            group = getattr(param, 'group', 'Options')
            if group not in option_groups:
                option_groups[group] = []

            opts = param.get_help_record(ctx)
            if opts:
                option_groups[group].append(opts)

    # Write each option group
    for group_name in ('Output options', 'Cache options', 'Global options', 'Options'):
        if group_name in option_groups:
            formatter.write_paragraph()
            formatter.write_heading(group_name)
            formatter.current_section = group_name
            formatter.write_dl(option_groups[group_name])

    # Write epilog
    if ctx.command.epilog:
        formatter.write_paragraph()
        formatter.write_text(ctx.command.epilog)

    return formatter.getvalue()
