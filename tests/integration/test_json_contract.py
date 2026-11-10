"""analyze and monitor --format json, validated against schemas/analysis.schema.json."""

import json
from pathlib import Path

from jsonschema import Draft7Validator
from typer.testing import CliRunner

from logsift.cli import app

SCHEMA = json.loads((Path(__file__).resolve().parents[2] / 'schemas' / 'analysis.schema.json').read_text())

# One line of each format the parser reads, plus a file reference, a tool code, pre-commit hook lines,
# a pattern with a suggestion and one that widens its context, so every optional field the schema names appears.
MIXED_LOG = """\
2025-11-27T14:30:22Z starting build
{"level": "error", "message": "db down", "file": "api.py", "file_line": 12, "timestamp": "2025-11-27T14:30:23Z"}
bash: frobnicate: command not found
time=2025-11-27T14:30:24Z level=warning msg="slow query"
<13>Nov 27 14:30:25 host app: something happened
src/main.py:42:5: F401 'os' imported but unused
ruff.....................................................................Failed
check yaml...............................................................Passed
An unexpected error has occurred: CalledProcessError: boom
WARNING -  Doc file 'x.md' contains a link
"""


def test_analyze_and_monitor_json_match_the_published_schema(tmp_path):
    log = tmp_path / 'mixed.log'
    log.write_text(MIXED_LOG)
    runner = CliRunner()

    analyzed = runner.invoke(app, ['analyze', '--format', 'json', str(log)])
    monitored = runner.invoke(app, ['monitor', '--minimal', '--format', 'json', '--', 'cat', str(log)])

    validator = Draft7Validator(SCHEMA)
    for result in (analyzed, monitored):
        assert result.exit_code == 0, result.output
        document = json.loads(result.stdout)
        assert list(validator.iter_errors(document)) == []
    saved = Path(json.loads(monitored.stdout)['summary']['log_file'].replace('/raw/', '/json/')).with_suffix('.json')
    assert list(validator.iter_errors(json.loads(saved.read_text()))) == []
    assert 'summary' not in json.loads(analyzed.stdout)
