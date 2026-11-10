"""Help in uv's style: colored, sectioned, with no boxes.

Typer from 0.27 runs its own copy of Click as `typer._click`, a private module. A group, an
argument and an option are told apart by `typer.core`'s classes, which are the ones Typer builds.
A context and a help formatter have no public name but `typer.Context`, which subclasses the copy's
context and is never what Typer passes in. So both are typed `Any`, and the formatter is made by the
context's own `formatter_class`.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

import typer
from typer.core import TyperArgument
from typer.core import TyperGroup
from typer.core import TyperOption


class ColoredTyperGroup(TyperGroup):
    """A Typer group whose help is `format_help_with_colors`."""

    def format_help(self, ctx: Any, formatter: Any) -> None:
        typer.echo(format_help_with_colors(ctx), color=True)


def heading_line(heading: str) -> str:
    """A section heading in bright green."""
    return f'{typer.style(f"{heading}:", fg="bright_green", bold=True)}\n'


def definition_list(rows: Sequence[tuple[str, str]], *, colored: bool, col_max: int = 30, col_spacing: int = 2) -> str:
    """Rows of a term and its description, the descriptions aligned, the terms bright blue where colored."""
    max_width = min(max((len(first) for first, _ in rows), default=0), col_max)
    lines = []
    for first, second in rows:
        term = typer.style(first, fg='bright_blue') if colored else first
        # Padded by the term's own length, which the color codes do not count toward.
        padding = ' ' * (max_width - len(first) + col_spacing)
        lines.append(f'  {term}{padding}{second}\n' if second else f'  {term}\n')
    return ''.join(lines)


def commands_by_section(ctx: Any, group: TyperGroup) -> list[tuple[str, str]]:
    """Pair each subcommand name with the help section it is listed under.

    Commands sharing a `rich_help_panel` are listed together, sections in the order their first
    command appears. Commands with no panel come last, under "Additional commands", as cobra
    lists its ungrouped children. A group whose commands name no panel keeps one "Commands" section.
    """
    sections: dict[str, list[str]] = {}
    ungrouped: list[str] = []
    for name in group.list_commands(ctx):
        # Typer leaves a falsy placeholder object, not None, on a command given no panel
        panel = getattr(group.get_command(ctx, name), 'rich_help_panel', None)
        if isinstance(panel, str) and panel:
            sections.setdefault(panel, []).append(name)
        else:
            ungrouped.append(name)

    ungrouped_heading = 'Additional commands' if sections else 'Commands'
    pairs = [(panel, name) for panel, names in sections.items() for name in names]
    pairs += [(ungrouped_heading, name) for name in ungrouped]
    return pairs


def format_help_with_colors(ctx: Any) -> str:
    """Format help text with uv-style colors and structure."""
    formatter = ctx.formatter_class(width=ctx.terminal_width, max_width=120)

    # Write description (clean up by removing Common Options and Examples sections)
    if ctx.command.help:
        formatter.write_paragraph()
        # For individual commands, only show the main description, not Common Options or Examples
        help_text = ctx.command.help
        if not isinstance(ctx.command, TyperGroup):
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
    usage_text = ctx.command.get_usage(ctx).replace('Usage: ', '')
    # Color the usage text blue and put it on same line as heading
    usage_heading = typer.style('Usage:', fg='bright_green', bold=True)
    usage_colored = typer.style(usage_text, fg='bright_blue')
    formatter.write(f'{usage_heading} {usage_colored}\n')

    # Write Arguments section for individual commands
    if not isinstance(ctx.command, TyperGroup):
        arguments = []
        for param in ctx.command.get_params(ctx):
            if isinstance(param, TyperArgument):
                opts = param.get_help_record(ctx)
                if opts:
                    arguments.append(opts)

        if arguments:
            formatter.write_paragraph()
            formatter.write(heading_line('Arguments'))
            formatter.write(definition_list(arguments, colored=False))

    # Get command object
    if isinstance(ctx.command, TyperGroup) and ctx.command.list_commands(ctx):
        # Main help - show commands under their sections with expanded descriptions, flags, and examples
        formatter.write_paragraph()
        current_heading = None

        for heading, name in commands_by_section(ctx, ctx.command):
            cmd = ctx.command.get_command(ctx, name)
            if cmd and not cmd.hidden:
                if heading != current_heading:
                    formatter.write(heading_line(heading))
                    current_heading = heading

                # Get full help text
                full_help = cmd.help or ''
                help_lines = full_help.split('\n\n')  # Split by paragraphs

                # Take first paragraph as summary
                summary = help_lines[0].replace('\n', ' ').strip() if help_lines else ''

                # Write command name in blue
                colored_name = typer.style(name, fg='bright_blue')
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
                            colored_flag = typer.style(flag, fg='cyan')
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
                                    formatter.write(f'      {typer.style("# Basic usage", dim=True)}\n')
                                elif example_count == 1:
                                    formatter.write(f'      {typer.style("# With options", dim=True)}\n')

                                # Write example in yellow
                                formatter.write(f'      {typer.style(line, fg="yellow")}\n')
                                example_count += 1
                                if example_count >= 2:
                                    break

                formatter.write('\n')

    # Write options grouped by category
    output_options: list[tuple[str, str]] = []
    global_options: list[tuple[str, str]] = []

    for param in ctx.command.get_params(ctx):
        if isinstance(param, TyperOption):
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
            if '--format' in opt_name or '--notify' in opt_name:
                output_options.append((opt_name, help_text))
            else:
                global_options.append((opt_name, help_text))

    # Write option groups in order
    if output_options:
        formatter.write_paragraph()
        formatter.write(heading_line('Output options'))
        formatter.write(definition_list(output_options, colored=True))

    if global_options:
        formatter.write_paragraph()
        formatter.write(heading_line('Global options'))
        formatter.write(definition_list(global_options, colored=True))

    # Write Examples section for individual commands
    if not isinstance(ctx.command, TyperGroup) and ctx.command.help:
        # Extract examples from the original help text
        help_paragraphs = ctx.command.help.split('\n\n')
        for para in help_paragraphs:
            if para.strip().startswith('Examples:'):
                formatter.write_paragraph()
                formatter.write(heading_line('Examples'))

                # Get example lines
                examples_text = para.replace('Examples:', '').strip()
                example_lines = examples_text.split('\n')

                for line in example_lines:
                    line = line.strip()
                    if line:
                        # Skip comment lines, but show them as dimmed
                        if line.startswith('#'):
                            formatter.write(f'  {typer.style(line, dim=True)}\n')
                        else:
                            # Show example in yellow
                            formatter.write(f'  {typer.style(line, fg="yellow")}\n')
                break

    # Write epilog
    if ctx.command.epilog:
        formatter.write_paragraph()
        formatter.write_text(ctx.command.epilog)

    return formatter.getvalue()
