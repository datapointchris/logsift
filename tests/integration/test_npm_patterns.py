"""An npm failure reads as an error, whether npm 6 printed it as `npm ERR!` or npm 7 on as `npm error`."""

import pytest

from logsift.core.analyzer import Analyzer

# Each failure as npm printed it, and the pattern that names it.
NPM_FAILURES = {
    'npm 11 missing script': (
        'npm error Missing script: "nope"\nnpm error\nnpm error To see a list of scripts, run:\nnpm error   npm run\n',
        'npm_missing_script',
    ),
    'npm 6 missing script': ('npm ERR! missing script: build\n', 'npm_missing_script'),
    'npm 11 install offline': (
        'npm error code ENOTCACHED\n'
        "npm error request to https://registry.npmjs.org/no-such-package failed: cache mode is 'only-if-cached'\n",
        'npm_error_code',
    ),
    'npm 6 failed script': (
        'npm ERR! code ELIFECYCLE\nnpm ERR! errno 2\nnpm ERR! app@1.0.0 build: `webpack`\nnpm ERR! Exit status 2\n',
        'npm_error_code',
    ),
}


@pytest.mark.parametrize(('log', 'pattern_name'), NPM_FAILURES.values(), ids=NPM_FAILURES)
def test_an_npm_failure_reads_as_an_error(log, pattern_name):
    errors = Analyzer().analyze(log)['errors']

    assert pattern_name in [error.get('pattern_name') for error in errors]
