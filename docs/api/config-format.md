# Configuration File Format

logsift reads one optional TOML file, `$XDG_CONFIG_HOME/logsift/config.toml`, else
`~/.config/logsift/config.toml`. Without it, logsift runs on its defaults.

## Every key, set to logsift's default

This file sets each key to the value logsift uses when the key is absent. Copy only the keys you
mean to change.

```toml
# How monitor and analyze print the analysis: auto, json, toon or markdown.
# auto prints Markdown on a terminal and toon when piped.
print_analysis_as = "auto"

[monitor]
# Seconds between monitor's progress reports. --stream and --quiet print none.
report_progress_every_seconds = 60

[logs.clean]
# `logsift logs clean` deletes raw logs older than this many days.
delete_older_than_days = 90

[analyzed.clean]
# `logsift analyzed clean` deletes saved analyses older than this many days.
delete_older_than_days = 30
```

## A flag beats its variable, which beats the file

Each value comes from the first of these that sets it:

1. Its flag, such as `--format json`.
2. Its environment variable, such as `LOGSIFT_OUTPUT_FORMAT=json`.
3. Its key in `config.toml`.
4. logsift's default.

| Key | Flag | Variable |
| --- | --- | --- |
| `print_analysis_as` | `monitor --format`, `analyze --format` | `LOGSIFT_OUTPUT_FORMAT` |
| `monitor.report_progress_every_seconds` | `monitor --update-interval` | `LOGSIFT_UPDATE_INTERVAL` |
| `logs.clean.delete_older_than_days` | `logs clean --days` | `LOGSIFT_RETENTION_DAYS` |
| `analyzed.clean.delete_older_than_days` | `analyzed clean --days` | none |

`monitor --name` and `LOGSIFT_SESSION_NAME` have no key. A name in the file would give every run
the same name.

## `logsift config` prints what resolved

`logsift config` prints each value logsift will use and the layer that set it. FROM names the
variable, `config.toml` or `default`. FILE KEY names the key that would set it.

```text
LOCATION         PATH                                          FROM
config file      /home/me/.config/logsift/config.toml          default
custom patterns  /home/me/.config/logsift/patterns             default
cache            /home/me/.cache/logsift                       default

OPTION                     VALUE                    FROM                      FILE KEY
monitor --format           json                     config.toml               print_analysis_as
monitor --update-interval  5                        $LOGSIFT_UPDATE_INTERVAL  monitor.report_progress_every_seconds
monitor --name             named after the command  default                   -
analyze --format           json                     config.toml               print_analysis_as
logs clean --days          90                       default                   logs.clean.delete_older_than_days
analyzed clean --days      30                       default                   analyzed.clean.delete_older_than_days
```

The config file's path says `(absent)` when there is no file.

## A file logsift cannot honor stops every command

logsift reads `config.toml` once, before any command runs. These stop the command with exit code 1:

- A file that fails to parse. The error names the file and the parser's message.
- A key logsift does not read, such as one left under an old name. The error names it and every key
  logsift reads.
- A value of the wrong TOML type, such as `report_progress_every_seconds = "60"`. The error names
  the key.

None of them falls back to the defaults.

## No key moves a directory

The XDG variables move logsift's directories, and `logsift config` prints each with the layer that
set it:

- Custom patterns: `$XDG_CONFIG_HOME/logsift/patterns/`, else `~/.config/logsift/patterns/`.
- Captured logs and saved analyses: `$XDG_CACHE_HOME/logsift/`, else `~/.cache/logsift/`.

## See Also

- [CLI Reference](../cli-reference.md) - Every flag and variable
- [Custom Patterns](../guides/custom-patterns.md) - Pattern files under the patterns directory
