# Installation Guide

Complete installation instructions for logsift.

## Requirements

- **Python 3.13+** - logsift uses modern Python features
- **uv** - the installer, which records the package index a release came from
- **Git** - only for a development install, which clones the repository

## Local Development Installation

Install logsift as a global tool for local testing and development:

```bash
# Clone the repository
git clone https://github.com/datapointchris/logsift.git
cd logsift

# Install as editable global tool
uv tool install --editable .
```

### Benefits of Editable Install

- Changes to source code are immediately reflected
- No need to reinstall after modifications
- `logsift` command available system-wide
- Perfect for development and testing

### Verify Installation

```bash
# Check installation location: inside the directory `uv tool dir --bin` prints
which logsift

# Check version
logsift --version
# Prints the installed version

# Test basic functionality
logsift --help
logsift monitor --format=json -- echo "Hello from logsift"
```

## Installing a Release

Every release is published to a package index of its own:

```bash
uv tool install --index https://pypi.ichrisbirch.com/simple/ logsift
```

Name the index on the install. Without it uv asks PyPI, where `logsift` is a different project.
uv records the index beside the tool, which is where `logsift update` reads it back.

## Uninstallation

Remove logsift completely:

```bash
# Uninstall the tool
uv tool uninstall logsift

# Name the cache and config directories, to delete them by hand if you want them gone
logsift config
```

## Troubleshooting

### Command Not Found

uv puts `logsift` in its tool bin directory. If your shell cannot find it, that directory is not
on `PATH`:

```bash
uv tool dir --bin       # the directory uv installed logsift into
uv tool update-shell    # add it to your shell's PATH, then open a new shell
```

### Permission Errors

logsift writes every run under its cache directory, which `logsift config` names on its `cache`
row. Make sure you own that directory and can write to it.

### Python Version Issues

Check Python version:

```bash
python --version  # Should be 3.13+

# If using multiple Python versions
python3.13 --version
```

Install Python 3.13 if needed:

```bash
# macOS with Homebrew
brew install python@3.13

# Ubuntu/Debian
sudo apt update
sudo apt install python3.13

# Or use pyenv
pyenv install 3.13
pyenv global 3.13
```

### UV Not Installed

Install UV if not present:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with pip
pip install uv

# Or with Homebrew (macOS)
brew install uv
```

## Development Setup

To contribute, clone the repository and run `task setup`, which installs the dev and test groups
and the git hooks. [Development Setup](development/setup.md) has the rest.

## Configuration

logsift runs on its defaults, so a config file is optional. To keep raw logs for 30 days instead
of 90:

```bash
mkdir -p "${XDG_CONFIG_HOME:-$HOME/.config}/logsift"
cat > "${XDG_CONFIG_HOME:-$HOME/.config}/logsift/config.toml" << 'EOF'
[logs.clean]
delete_older_than_days = 30
EOF
logsift config   # logs clean --days now reads 30, from config.toml
```

See [Config Format](api/config-format.md) for every key.

## Upgrading

### From Source (Editable Install)

```bash
cd /path/to/logsift
git pull origin main
# No reinstall needed - changes are live due to editable install
```

### A Release

```bash
logsift update
```

It installs the newest release from the index over the running one.

## System Requirements

### Minimum

- **OS**: macOS, Linux, Windows WSL
- **Python**: 3.13+
- **RAM**: 512 MB
- **Disk**: 50 MB for installation, variable for cache

### Recommended

- **OS**: macOS or Linux
- **Python**: 3.13
- **RAM**: 1 GB
- **Disk**: 1 GB for cache (90-day retention)

## Dependencies

Core dependencies are installed automatically. `[project] dependencies` in `pyproject.toml` is the
list, and `uv tree --no-dev --depth 1` prints what an install resolves it to.

Development dependencies (optional):

- See `pyproject.toml` `[dependency-groups]` for complete list

## Platform-Specific Notes

### macOS

No special requirements. Homebrew installation of Python 3.13 recommended.

### Linux

Ensure Python 3.13 is available. Some distributions may require:

```bash
# Ubuntu/Debian - install build dependencies
sudo apt install python3.13-dev python3.13-venv

# Fedora/RHEL
sudo dnf install python3.13-devel
```

### Windows WSL

Recommended approach. Install WSL2 with Ubuntu, then follow Linux instructions.

### Native Windows

Not supported. Use WSL2.

## Verification Checklist

After installation, verify everything works:

- [ ] `logsift --version` prints a version rather than `unknown`
- [ ] `logsift --help` displays help message
- [ ] `logsift monitor -- echo test` executes successfully
- [ ] `logsift logs list` shows the log that run saved under `~/.cache/logsift/raw/`
- [ ] JSON output works: `logsift monitor --format=json -- echo test`
- [ ] Markdown output works: `logsift monitor --format=markdown -- echo test`

## Next Steps

After successful installation:

1. **[5-Minute Quickstart](quickstart.md)** - Get started immediately
2. **[CLI Reference](cli-reference.md)** - Where each command's help lives, and the exit codes
3. **[Agentic Integration](concepts/agentic-integration.md)** - Use with Claude Code

## Getting Help

Installation issues? Check:

1. This troubleshooting section
2. [GitHub Issues](https://github.com/datapointchris/logsift/issues)
3. [Development Setup](development/setup.md) for detailed dev environment guide

Report installation bugs on [GitHub](https://github.com/datapointchris/logsift/issues) with:

- Operating system and version
- Python version (`python --version`)
- UV version (`uv --version`)
- Complete error message
- Steps to reproduce
