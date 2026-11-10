"""logsift - Intelligent log analysis for agentic workflows.

logsift is an LLM-optimized log analysis and command monitoring tool designed
specifically for Claude Code and other AI agents to efficiently diagnose, fix,
and retry failed operations with minimal context overhead.
"""

import json
from importlib.metadata import PackageNotFoundError
from importlib.metadata import distribution


def tool_version() -> str:
    """This build's version, then ` @ <sha8>` when it was installed from a git ref, or 'unknown' from a source checkout.

    The version is the installed distribution's, which the release tag sets through
    uv-dynamic-versioning. The commit is the one uv records in direct_url.json for a git install,
    which names the build when a branch install reports one version for many commits.
    """
    try:
        dist = distribution('logsift')
    except PackageNotFoundError:
        return 'unknown'
    commit = json.loads(dist.read_text('direct_url.json') or '{}').get('vcs_info', {}).get('commit_id')
    return f'{dist.version} @ {commit[:8]}' if commit else dist.version


__version__ = tool_version()
__author__ = 'Chris Birch'
__email__ = 'datapointchris@gmail.com'

__all__ = ['__version__', '__author__', '__email__']
