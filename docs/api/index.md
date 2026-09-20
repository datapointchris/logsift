# API Reference

Format specifications for the files logsift reads and the output it writes. Reach for these when
writing a consumer against logsift's output, or when hand-editing one of its TOML files.

## Documentation

- [JSON Schema](json-schema.md) — Every field logsift emits, with types and nullability, plus the stability promise and Python and jq parsing examples
- [Pattern Format](pattern-format.md) — Keys a `[[patterns]]` entry takes, the rules each key enforces, match priority, and worked capture-group regexes
- [Config Format](config-format.md) — Keys under `[cache]`, `[analysis]`, `[output]` and `[patterns]`, with defaults and the config file's location
