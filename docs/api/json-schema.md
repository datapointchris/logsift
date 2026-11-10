# JSON Output Schema

[`schemas/analysis.schema.json`](https://github.com/datapointchris/logsift/blob/main/schemas/analysis.schema.json)
is the contract for `--format json`. It is a draft-07 JSON Schema with `$id`
`urn:logsift:analysis:v1`, and each field's meaning is its `description` there. Read the fields
from the file rather than from an example, because an example goes stale and the file is what a
test validates every real run against.

## Three places print it

- `logsift analyze --format json <log>` prints the analysis of a log file. It has no `summary`,
  because nothing ran.
- `logsift monitor --format json -- <command>` adds `summary`: the status, exit code, duration and
  command of the run, and the path of the raw log it saved.
- Each saved analysis under `$XDG_CACHE_HOME/logsift/json/` holds the same document.

## Versioning

Every document carries `schema_version`, which is `1`. A change that renames or removes a field, or
changes what a field means, raises it along with the `$id`. Adding an optional field raises neither.
Check `schema_version` before trusting any other field.

## Reading it

- **An optional field is absent, never null.** `pattern_name`, `description`, `tags` and
  `suggestion` appear only when a TOML pattern matched the line. A JSON or key=value line flagged by
  its own `level` field carries none of them.
- **`suggestion` is a string**: the matching pattern's fix hint.
- **`file_references` lists `[path, line]` pairs** found in the message, such as
  `["src/main.py", 42]`.
- **`context_before` and `context_after` hold parsed lines**, each an object with `line_number`,
  `level`, `format` and `message`, rather than bare strings.
- **`hooks.failed` names each pre-commit hook** the log showed failing.

## Validating output against it

```bash
logsift analyze --format json app.log > analysis.json
uvx check-jsonschema --schemafile schemas/analysis.schema.json analysis.json
```

## Parsing examples

### Python

```python
import json
import subprocess

run = subprocess.run(['logsift', 'monitor', '--quiet', '--format', 'json', '--', 'make', 'build'], capture_output=True, text=True)
data = json.loads(run.stdout)

if data['summary']['status'] == 'failed':
    for error in data['errors']:
        print(f'Error: {error["message"]}')
        for path, line in error.get('file_references', []):
            print(f'  at {path}:{line}')
```

### jq

```bash
# Every error message
logsift analyze --format json app.log | jq -r '.errors[].message'

# Every file:line reference
logsift analyze --format json app.log | jq -r '.errors[].file_references[]? | "\(.[0]):\(.[1])"'

# Errors that carry a fix hint
logsift analyze --format json app.log | jq '[.errors[] | select(.suggestion)]'
```

## See Also

- [Output Modes](../concepts/output-modes.md) - JSON, toon and Markdown
- [Agentic Integration](../concepts/agentic-integration.md) - Using JSON with AI
