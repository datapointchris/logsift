"""Every external process logsift starts: fzf, bat, notify-send, osascript and the monitored command.

`run()` takes a program to completion. `stream()` starts the command `logsift monitor` watches and
hands back its merged output a line at a time. A program that is not installed raises
FileNotFoundError from either, which each caller turns into its own fallback.
"""

import dataclasses as dc
import os
import shlex
import subprocess  # nosec B404
from collections.abc import Iterator
from collections.abc import Sequence

# Printed by the fallback shell after its start-up files run, so their output can be dropped.
SHELL_PREAMBLE_END = '___LOGSIFT_COMMAND_START___'


def run(argv: Sequence[str], *, input_text: str | None = None, capture: bool = False) -> subprocess.CompletedProcess[str]:
    """Run argv to completion and return its result, whatever its exit code.

    Args:
        argv: The program and its arguments, never passed through a shell
        input_text: Text written to the program's stdin, or None to leave stdin inherited
        capture: Capture stdout and stderr instead of letting them reach the terminal
    """
    return subprocess.run(list(argv), input=input_text, capture_output=capture, text=True, check=False)  # nosec B603


@dc.dataclass
class StreamedProcess:
    """A started command whose stdout and stderr arrive merged, one line at a time."""

    process: subprocess.Popen[str]
    # Set when the command runs through an interactive shell, whose start-up output precedes it.
    preamble_end: str | None

    @property
    def pid(self) -> int:
        return self.process.pid

    def lines(self) -> Iterator[str]:
        """Yield each line the command prints, with its newline, after any shell start-up output."""
        output = iter(self.process.stdout or ())
        if self.preamble_end is not None:
            for line in output:
                if self.preamble_end in line:
                    break
        yield from output

    def wait(self) -> int:
        return self.process.wait()

    def terminate(self) -> None:
        self.process.terminate()
        self.process.wait()


def stream(argv: Sequence[str]) -> StreamedProcess:
    """Start argv with its output merged into one line-buffered pipe.

    A program not on PATH may be a shell function or alias, so it is run again through
    `$SHELL -i -c`, which reads the user's start-up files. Whatever those print comes before
    SHELL_PREAMBLE_END and never reaches `lines()`.
    """
    try:
        return StreamedProcess(start_merged(list(argv)), preamble_end=None)
    except FileNotFoundError:
        shell = os.environ.get('SHELL', '/bin/bash')
        wrapped = f'printf "\\n{SHELL_PREAMBLE_END}\\n" >&2; {shlex.join(argv)}'
        return StreamedProcess(start_merged([shell, '-i', '-c', wrapped]), preamble_end=SHELL_PREAMBLE_END)


def start_merged(argv: list[str]) -> subprocess.Popen[str]:
    """Start argv with stderr folded into a line-buffered text stdout."""
    return subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)  # nosec B603
