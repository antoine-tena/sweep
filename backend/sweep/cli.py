"""sweep : trouve ce qui encombre la RAM et le swap, et propose quoi tuer.

Sans option, sweep ne fait que montrer. `--kill` demande confirmation avant d'arrêter quoi que
ce soit ([DESTRUCTIF]).
"""

import argparse
import os
import sys
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from importlib.metadata import version
from typing import TextIO

from sweep.local_machine import LocalMachine
from sweep.machine import Machine
from sweep.report import render_json, render_text
from sweep.rules.patterns import IDLE_AGENT_AGE
from sweep.scan import scan
from sweep.scan_result import ScanResult
from sweep.sizes import format_size

PROGRAM = "sweep"
EXIT_OK = 0
EXIT_FAILURE = 1
YES_ANSWERS = frozenset({"o", "oui", "y", "yes"})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=PROGRAM, description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {version(PROGRAM)}")
    parser.add_argument("--kill", action="store_true", help="arrêter les candidats trouvés")
    parser.add_argument("--yes", action="store_true", help="avec --kill : sans confirmation")
    parser.add_argument("--dry-run", action="store_true", help="avec --kill : simuler seulement")
    parser.add_argument("--json", action="store_true", help="rapport en JSON, sans rien tuer")
    parser.add_argument(
        "--idle-hours",
        type=_positive_hours,
        default=IDLE_AGENT_AGE / timedelta(hours=1),
        help="âge à partir duquel un agent sans activité est candidat (défaut : %(default)g)",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    out: TextIO = sys.stdout,
    machine: Machine | None = None,
    ask: Callable[[str], str] = input,
    clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> int:
    args = build_parser().parse_args(argv)
    machine = machine or LocalMachine()
    idle_age = timedelta(hours=args.idle_hours)
    result = scan(machine, clock(), os.getpid(), idle_agent_age=idle_age)
    if args.json:
        out.write(render_json(result))
        return EXIT_OK
    out.write(render_text(result))
    if not args.kill or not result.candidates:
        return EXIT_OK
    if args.dry_run:
        out.write("\nSimulation : rien n'a été arrêté.\n")
        return EXIT_OK
    if not args.yes and ask("\nTout arrêter ? [o/N] ").strip().lower() not in YES_ANSWERS:
        out.write("Rien n'a été arrêté.\n")
        return EXIT_OK
    return _kill(machine, result, out)


def _kill(machine: Machine, result: ScanResult, out: TextIO) -> int:
    survivors = machine.terminate(result.targets())
    if survivors:
        out.write(f"Encore vivants (droits insuffisants ?) : {', '.join(map(str, survivors))}\n")
        return EXIT_FAILURE
    out.write(f"Arrêtés : environ {format_size(result.reclaimable_bytes)} libérés.\n")
    return EXIT_OK


def _positive_hours(raw_hours: str) -> float:
    """Validée à la frontière ([VALIDATION-AUX-FRONTIERES]) : un nombre d'heures positif."""
    try:
        hours = float(raw_hours)
    except ValueError:
        raise argparse.ArgumentTypeError(f"nombre d'heures attendu : {raw_hours!r}") from None
    if hours <= 0:
        raise argparse.ArgumentTypeError("le nombre d'heures doit être positif")
    return hours
