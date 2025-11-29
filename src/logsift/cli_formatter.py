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
            # Color command names and option flags blue
            if self.current_section in ('Commands', 'Cache options', 'Output options', 'Global options'):
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

    # Write description (clean up by removing Common Options and Examples sections)
    if ctx.command.help:
        formatter.write_paragraph()
        # For individual commands, only show the main description, not Common Options or Examples
        help_text = ctx.command.help
        if not isinstance(ctx.command, click.Group):
            # Split by double newlines and only take paragraphs before "Common Options:" or "Examples:"
            paragraphs = help_text.split('\n\n')
            clean_paragraphs = []
            for para in paragraphs:
                if para.strip().startswith('Common Options:') or para.strip().startswith('Examples:'):
                    break
                clean_paragraphs.append(para)
            help_text = '\n\n'.join(clean_paragraphs)
        formatter.write_text(help_text)

    # Write usage on same line with blue color
    formatter.write_paragraph()
    formatter.current_section = 'Usage'
    usage_text = ctx.command.get_usage(ctx).replace('Usage: ', '')
    # Color the usage text blue and put it on same line as heading
    usage_heading = click.style('Usage:', fg='bright_green', bold=True)
    usage_colored = click.style(usage_text, fg='bright_blue')
    formatter.write(f'{usage_heading} {usage_colored}\n')

    # Write Arguments section for individual commands
    if not isinstance(ctx.command, click.Group):
        arguments = []
        for param in ctx.command.get_params(ctx):
            if isinstance(param, click.Argument):
                opts = param.get_help_record(ctx)
                if opts:
                    arguments.append(opts)

        if arguments:
            formatter.write_paragraph()
            formatter.write_heading('Arguments')
            formatter.current_section = 'Arguments'
            formatter.write_dl(arguments)

    # Get command object
    if isinstance(ctx.command, click.Group) and ctx.command.list_commands(ctx):
        # Main help - show commands with expanded descriptions, flags, and examples
        formatter.write_paragraph()
        formatter.write_heading('Commands')
        formatter.current_section = 'Commands'

        for name in ctx.command.list_commands(ctx):
            cmd = ctx.command.get_command(ctx, name)
            if cmd and not cmd.hidden:
                # Get full help text
                full_help = cmd.help or ''
                help_lines = full_help.split('\n\n')  # Split by paragraphs

                # Take first paragraph as summary
                summary = help_lines[0].replace('\n', ' ').strip() if help_lines else ''

                # Write command name in blue
                colored_name = click.style(name, fg='bright_blue')
                formatter.write(f'  {colored_name}\n')

                # Write summary
                if summary:
                    formatter.write(f'    {summary}\n')

                # Extract and write Common Options (flags) if present
                for _, paragraph in enumerate(help_lines):
                    if paragraph.strip().startswith('Common Options:'):
                        # Write the options header
                        formatter.write('\n')
                        # Parse options and align them
                        options_text = paragraph.replace('Common Options:', '').strip()
                        options = []
                        for line in options_text.split('\n'):
                            line = line.strip()
                            if line:
                                # Split flag from description using multiple spaces as separator
                                # Format is: "-n, --name          Description" or "--format        Description"
                                # Find where multiple spaces (2+) start - that's the description
                                import re

                                match = re.match(r'^(\S+(?:\s+\S+)?)\s{2,}(.+)$', line)
                                if match:
                                    flag = match.group(1)
                                    desc = match.group(2)
                                    options.append((flag, desc))
                                else:
                                    # Fallback for lines without description
                                    parts = line.split(None, 1)
                                    if len(parts) == 2:
                                        options.append((parts[0], parts[1]))
                                    elif len(parts) == 1:
                                        options.append((parts[0], ''))

                        # Find max width for alignment
                        max_width = max((len(opt[0]) for opt in options), default=0)

                        # Write aligned options
                        for flag, desc in options:
                            colored_flag = click.style(flag, fg='cyan')
                            padding = ' ' * (max_width - len(flag) + 2)
                            formatter.write(f'      {colored_flag}{padding}{desc}\n')

                # Extract and write Examples if present
                for _, paragraph in enumerate(help_lines):
                    if paragraph.strip().startswith('Examples:'):
                        formatter.write('\n')
                        # Get example lines
                        examples = paragraph.replace('Examples:', '').strip().split('\n')
                        # Show first 2 examples with different invocation styles
                        example_count = 0
                        for line in examples:
                            line = line.strip()
                            if line and not line.startswith('#') and example_count < 2:
                                # Add descriptive comment based on example content
                                if example_count == 0:
                                    formatter.write(f'      {click.style("# Basic usage", dim=True)}\n')
                                elif example_count == 1:
                                    formatter.write(f'      {click.style("# With options", dim=True)}\n')

                                # Write example in yellow
                                formatter.write(f'      {click.style(line, fg="yellow")}\n')
                                example_count += 1
                                if example_count >= 2:
                                    break

                formatter.write('\n')

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

            # Skip --help flag (we have 'logsift help' command instead)
            if '--help' in opt_name:
                continue

            # Environment variables are already shown by Typer as [env var: X]
            # We don't need to add them again - Typer handles this automatically

            # Group options by name patterns
            if '--cache' in opt_name or '--no-cache' in opt_name:
                cache_options.append((opt_name, help_text))
            elif '--format' in opt_name or '--notify' in opt_name:
                output_options.append((opt_name, help_text))
            elif '--config' in opt_name or '--no-config' in opt_name:
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

    # Write Examples section for individual commands
    if not isinstance(ctx.command, click.Group) and ctx.command.help:
        # Extract examples from the original help text
        help_paragraphs = ctx.command.help.split('\n\n')
        for para in help_paragraphs:
            if para.strip().startswith('Examples:'):
                formatter.write_paragraph()
                formatter.write_heading('Examples')
                formatter.current_section = 'Examples'

                # Get example lines
                examples_text = para.replace('Examples:', '').strip()
                example_lines = examples_text.split('\n')

                for line in example_lines:
                    line = line.strip()
                    if line:
                        # Skip comment lines, but show them as dimmed
                        if line.startswith('#'):
                            formatter.write(f'  {click.style(line, dim=True)}\n')
                        else:
                            # Show example in yellow
                            formatter.write(f'  {click.style(line, fg="yellow")}\n')
                break

    # Write epilog
    if ctx.command.epilog:
        formatter.write_paragraph()
        formatter.write_text(ctx.command.epilog)

    return formatter.getvalue()
