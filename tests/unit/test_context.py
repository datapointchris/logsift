"""How many lines `analyze` keeps around an issue: two each side, or what its pattern asks for after it."""

from logsift.core.analyzer import Analyzer


def messages(entries):
    return [entry['message'] for entry in entries]


def test_an_issue_carries_two_lines_each_side():
    [error] = Analyzer().analyze('one\ntwo\nERROR: boom\nfour\nfive\nsix\n')['errors']

    assert (messages(error['context_before']), messages(error['context_after'])) == (['one', 'two'], ['four', 'five'])


def test_a_pattern_asking_for_more_lines_after_gets_them():
    """bandit prints its Severity, CWE, More Info and Location lines under the issue's header."""
    log = 'zero\n>> Issue: [B307:blacklist] Use of eval.\n   Severity: Medium\n   CWE: x\n   More Info: y\n   Location: a.py:1\nseven\n'

    [warning] = Analyzer().analyze(log)['warnings']

    assert messages(warning['context_after']) == ['Severity: Medium', 'CWE: x', 'More Info: y', 'Location: a.py:1']
