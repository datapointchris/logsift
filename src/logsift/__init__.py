"""logsift - Intelligent log analysis for agentic workflows.

logsift is an LLM-optimized log analysis and command monitoring tool designed
specifically for Claude Code and other AI agents to efficiently diagnose, fix,
and retry failed operations with minimal context overhead.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version

# The installed distribution's version, which the release tag sets through uv-dynamic-versioning.
try:
    __version__ = version('logsift')
except PackageNotFoundError:
    __version__ = 'unknown'
__author__ = 'Chris Birch'
__email__ = 'datapointchris@gmail.com'

__all__ = ['__version__', '__author__', '__email__']
