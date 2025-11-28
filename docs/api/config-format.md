# Configuration File Format

TOML specification for logsift configuration.

## File Location

Create config file at:

```
~/.config/logsift/config.toml
```

## Full Example

```toml
[cache]
directory = "~/.cache/logsift"
retention_days = 90

[analysis]
context_lines = 2
max_errors = 100

[output]
default_format = "auto"  # auto, json, markdown

[patterns]
custom_dir = "~/.config/logsift/patterns"
```

## [cache]

Cache directory settings:

```toml
[cache]
directory = "~/.cache/logsift"  # Cache directory path
retention_days = 90              # Days to keep logs
```

**Fields:**

- `directory` (string) - Path to cache directory
  - Default: `~/.cache/logsift`
  - Tilde expansion supported
  - Created automatically if missing

- `retention_days` (integer) - Log retention period
  - Default: `90`
  - Logs older than this are deleted by cleanup
  - Set to `0` for infinite retention

## [analysis]

Analysis behavior settings:

```toml
[analysis]
context_lines = 2      # Lines of context around errors
max_errors = 100       # Maximum errors to extract
```

**Fields:**

- `context_lines` (integer) - Context lines around errors
  - Default: `2`
  - Extracts N lines before and after each error
  - Range: 0-10

- `max_errors` (integer) - Maximum errors to extract
  - Default: `100`
  - Prevents unbounded memory usage
  - First N errors are extracted

## [output]

Output format settings:

```toml
[output]
default_format = "auto"  # auto, json, markdown
```

**Fields:**

- `default_format` (string) - Default output format
  - Default: `"auto"`
  - Valid values: `"auto"`, `"json"`, `"markdown"`
  - Can be overridden with `--format` flag

## [patterns]

Pattern loading settings:

```toml
[patterns]
custom_dir = "~/.config/logsift/patterns"
```

**Fields:**

- `custom_dir` (string) - Custom patterns directory
  - Default: `~/.config/logsift/patterns`
  - Tilde expansion supported
  - All `*.toml` files loaded automatically

## Minimal Configuration

Default values are sensible. Minimal config:

```toml
# Empty config file uses all defaults
```

Or override only what you need:

```toml
[cache]
retention_days = 30  # Keep logs for 30 days instead of 90
```

## Environment Variables (Future)

Phase 3 will add environment variable support:

```bash
export LOGSIFT_CONFIG=/custom/path/config.toml
export LOGSIFT_CACHE_DIR=/custom/cache
export LOGSIFT_NO_COLOR=1
```

## Validation

Configuration is validated on load. Invalid config causes startup failure.

Checks:

- [ ] Valid TOML syntax
- [ ] All sections optional
- [ ] Field types correct
- [ ] Paths exist (created if missing)
- [ ] Valid enum values

## See Also

- [Installation](../installation.md) - Setup and config
- [CLI Reference](../cli-reference.md) - Override config with flags
