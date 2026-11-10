# Development Setup

Complete guide for contributing to logsift.

## Requirements

- Python 3.13+
- uv (package installer)
- [Task](https://taskfile.dev) (runs the commands in `Taskfile.yml`)
- Git

## Initial Setup

```bash
git clone https://github.com/datapointchris/logsift.git
cd logsift

# Install the dev and test groups, and the commit and commit-msg hooks
task setup

# Install as an editable tool, so `logsift` runs your checkout
uv tool install --editable .
```

`task --list` names every command. `logsift --version` and `task test` confirm the install.

## Development Workflow

1. Name a branch for the work it holds, with no type prefix: `git switch -c hook-status-in-toon`.
2. Edit code in `src/logsift/`, with its tests in `tests/unit/` or `tests/integration/`.
3. `task format` applies ruff's formatting and autofixes. `task lint` runs ruff, mypy, bandit and
   deptry without writing, as CI does. `task test` runs the suite.
4. Commit with a [Conventional Commits](https://www.conventionalcommits.org/) message, such as
   `feat: read a pattern's code group` or `fix: keep the level prefix in the message`.
5. Push the branch and open a pull request on GitHub.

The commit runs every hook `.pre-commit-config.yaml` declares, among them ruff, mypy, codespell,
markdownlint and shellcheck, and the commit-msg hook checks the message. So nothing needs running
by hand before a commit. `uv run pre-commit run <hook-id> --files <path>` reruns one hook on one
file while fixing what it found.

## Project Structure

```text
logsift/
├── src/logsift/
│   ├── cli.py                # Typer entry: parses the command line and calls a command
│   ├── commands/             # One module per command, orchestrating the rest
│   ├── core/                 # Parsing, issue detection, file references, analysis
│   ├── patterns/             # Pattern loading and validation, and the built-in TOML files
│   ├── output/               # toon, JSON and Markdown formatters
│   ├── monitor/              # Following a file as it grows
│   ├── config/               # config.toml loading and each option's resolved value
│   ├── cache/                # The cache directory's one door, CacheManager
│   ├── utils/                # bat, fzf, notifications and timestamps
│   ├── process_runner.py     # Where every external process starts
│   └── xdg_dirs.py           # The config and cache directories
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py           # Shared fixtures
├── schemas/                  # The JSON schema --format json prints to
├── docs/
├── pyproject.toml
└── Taskfile.yml
```

## Running Tests

`task test` passes anything after `--` to pytest:

```bash
task test                                                       # all tests
task test -- tests/unit/test_parser.py -v                       # one file
task test -- tests/unit/test_parser.py::test_parser_initialization -v  # one test
task test:coverage                                              # with a coverage report
```

## Testing Philosophy

1. **Test behavior, not implementation**
2. **Integration tests as important as unit tests**
3. **Use real log samples**

## Documentation

```bash
uv run mkdocs serve   # serve docs locally
uv run mkdocs build   # build the static site
```

## Troubleshooting

### A Hook Fails the Commit

The commit did not happen. Read what each hook printed, fix the cause, stage again and commit again.
`task format` fixes what ruff can fix itself.

### Tests Fail

```bash
task test -- -vv                                      # verbose output
task test -- -s                                       # show print output
task test -- tests/unit/test_file.py::test_name -vv   # one failing test
```

### Type Errors

```bash
task typecheck
```

## See Also

- [Testing Guide](testing.md) - Testing best practices
- [Code Patterns](patterns.md) - Code standards
