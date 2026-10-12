"""Un passage complet : photo de la machine, règles, conseils."""

from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

from sweep.advice import build_advice
from sweep.machine import Machine
from sweep.rules import ScanContext, find_candidates
from sweep.rules.patterns import IDLE_AGENT_AGE
from sweep.rules.tree import ProcessTree
from sweep.scan_result import ScanResult

HEAVIEST_COUNT = 8


def scan(
    machine: Machine,
    now: datetime,
    own_pid: int,
    path_exists: Callable[[str], bool] = lambda path: Path(path).exists(),
    idle_agent_age: timedelta = IDLE_AGENT_AGE,
) -> ScanResult:
    processes = machine.read_processes()
    tree = ProcessTree(processes)
    protected = frozenset({own_pid, *(ancestor.pid for ancestor in tree.ancestors(own_pid))})
    context = ScanContext(tree, now, protected, path_exists, idle_agent_age)
    memory, platform, host = machine.read_memory(), machine.platform(), machine.read_host()
    heaviest = sorted(processes, key=lambda process: process.rss_bytes, reverse=True)
    return ScanResult(
        platform=platform,
        memory=memory,
        host=host,
        candidates=tuple(find_candidates(context)),
        heaviest=tuple(heaviest[:HEAVIEST_COUNT]),
        advice=tuple(build_advice(memory, platform, host)),
        processes_by_pid=dict(tree.by_pid),
    )
