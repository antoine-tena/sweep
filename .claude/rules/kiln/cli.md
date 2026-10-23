---
paths:
  - "backend/**"
---
<!-- Written by kiln and kept current by `kiln update`: do not edit, it would be overwritten. -->
# Backend: Python command-line tool

`backend/sweep/`: commands (`cli.py`, entry point `__main__.py`) and business logic.
Run: `cd backend && uv run sweep --help`; install on the machine: `uv tool install --editable
backend` (from the root); check: `kiln check`.

## Architecture

- **[THIN-CLI]** `sweep/cli.py` is the only door: it reads the arguments, calls the core
  and writes the result. No computation, no business decision: beyond dispatching on the
  sub-command, the code goes to a module of the core.
- **[PURE-CORE]** The core (`sweep/<domain>.py`) receives values and returns values, often
  `dataclass(frozen=True)`: no `argparse`, no writing to the terminal, no `sys.exit`. It is
  tested without a terminal.
- **[SYSTEM-AT-THE-EDGE]** What touches the machine (processes, files, network, external
  commands) lives in dedicated access modules, called by `cli.py` or injected into the core
  (parameter or `Protocol`) so that tests replace them. An external command runs through
  `subprocess.run([...], check=..., timeout=...)`, as a list of arguments, never `shell=True`.
- **[MULTI-PLATFORM]** What depends on the system (Linux, macOS, Windows, WSL) goes through one
  detection function and one module per platform; never scattered `if sys.platform` in the core.

## Interface

- **[OUTPUT-STREAM]** The result is written to the stream received as a parameter (`out: TextIO`,
  `sys.stdout` by default), errors to `sys.stderr`. `print()` is banned ([LOGGING]).
- **[EXIT-CODES]** `main()` returns a named exit code (`EXIT_OK`, `EXIT_FAILURE`…): 0 for a
  success, non-zero for a failure. An expected error gives a one-line message, in the project's
  language, with no Python traceback; an unexpected one keeps its traceback.
- **[MACHINE-OUTPUT]** Every command that returns data offers `--json`: a stable, documented
  output, with no decoration, for a script or an agent to read.
- **[DESTRUCTIVE-ACTIONS]** An irreversible action (delete, kill, overwrite) shows what it is
  about to do and asks for confirmation; `--yes` skips it, `--dry-run` simulates without touching
  anything. Never a destructive action by default.

## Code and tests

- **[LOGGING]** No `print()` outside the output stream of `cli.py`; a log goes through
  `structlog` (checked).
- **[MINIMAL-DEPENDENCIES]** The standard library first (`argparse`, `pathlib`, `subprocess`); a
  dependency is added when it avoids fragile code (process reading, complex formats), justified in
  its commit ([NEW-DEPENDENCY]).
- **[TESTS]** Every function of the core has its tests; `main()` is tested by passing it its
  arguments and an `io.StringIO`, never by running a subprocess.
- **[NO-NETWORK]** No test sends a network request nor touches the machine's real processes:
  system access is simulated.
- **[REGRESSION-TEST]** Every bug fix comes with the test that would have caught it.
