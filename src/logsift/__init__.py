"""logsift - Intelligent log analysis for agentic workflows.

logsift is an LLM-optimized log analysis and command monitoring tool designed
specifically for Claude Code and other AI agents to efficiently diagnose, fix,
and retry failed operations with minimal context overhead.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as installed_version


def tool_version() -> str:
    """This build's version, or 'unknown' from a source checkout.

    Read from the installed distribution, whose version the release tag sets
    through uv-dynamic-versioning. A constant here would be bumped by nothing.

    A checkout that was never installed has no metadata and says so rather than
    inventing a number.
    """
    try:
        return installed_version('logsift')
    except PackageNotFoundError:
        return 'unknown'


__version__ = tool_version()
__author__ = 'Chris Birch'
__email__ = 'datapointchris@gmail.com'

__all__ = ['__version__', '__author__', '__email__']
