# CLI Reference

Every command's flags, defaults and examples are in its own help, which the code generates, so
this page does not repeat them:

```bash
logsift --help            # the commands, grouped by what they are for
logsift monitor --help    # one command's arguments, options and examples
logsift help monitor      # the same screen
logsift config            # every setting's value, and the flag, variable or file that set it
```

## What Each Stream Carries

- **stdout** holds the answer: the analysis from `monitor` and `analyze`, a listing, or a saved
  file. `--format json` and the piped default, toon, put nothing else there, so a program can
  parse stdout whole.
- **stderr** holds everything about the run: `monitor`'s banner and progress, which file a
  `latest` picked, warnings, and errors. `monitor -q` keeps only the warnings and errors there.

## Exit Codes

- **0**: the command did what it was asked. `analyze` exits 0 whatever it found in the log.
- **1**: logsift could not do it: a log file that does not exist, a `latest` with nothing saved,
  a file `clean` could not delete, a `config.toml` that fails to parse, or fzf missing.
- **2**: the command line was wrong: an unknown command or flag, a value outside a flag's set,
  `analyze` given more or fewer than one of a path, `--latest` and `--choose`, or a `choose` run
  without a terminal.
- **Anything else**: `monitor` exits with the monitored command's own code, so a caller branches
  on the command's result as if it had run the command itself.

```bash
if logsift monitor -q --format json -- make test > analysis.json; then
    echo "Tests passed"
else
    jq '.errors[0]' analysis.json
fi
```

## See Also

- [Configuration](api/config-format.md) - The `config.toml` keys and the variables beside them
- [JSON Schema](api/json-schema.md) - The shape `--format json` prints
- [Pattern Format](api/pattern-format.md) - Writing custom patterns
