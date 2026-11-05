# Instructions for coding agents in logsift

`CLAUDE.md` at the repository root is the one copy of this repo's guidance for coding agents.
Read it before changing anything. It holds the design principles, the rule that pattern matching
lives only in the TOML pattern files, the JSON output contract, and the developer commands.

The facts it points at are read from their source rather than copied here:

- `pyproject.toml` holds the dependencies, the tool settings and the coverage floor
  (`fail_under`).
- `.pre-commit-config.yaml` holds the checks every commit runs.
- `Taskfile.yml` holds the developer commands, and `task --list` names them.
