"""Fabriques de process et de machines simulés : aucun test ne touche aux vrais process."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sweep.host_status import HostStatus
from sweep.memory_status import MemoryStatus
from sweep.platforms import Platform
from sweep.process_info import ProcessInfo
from sweep.rules import ScanContext
from sweep.rules.tree import ProcessTree

NOW = datetime(2026, 10, 13, 12, 0, tzinfo=UTC)
MIB = 1024**2
GIB = 1024**3
INIT_PID = 1


def make_process(
    pid: int,
    command: str,
    *,
    ppid: int = INIT_PID,
    rss_mib: int = 100,
    age: timedelta = timedelta(minutes=5),
    cpu_percent: float = 0.0,
    cwd: str | None = "/home/user",
    name: str | None = None,
) -> ProcessInfo:
    arguments = tuple(command.split())
    return ProcessInfo(
        pid=pid,
        ppid=ppid,
        name=name if name is not None else arguments[0].rsplit("/", 1)[-1],
        cmdline=arguments,
        rss_bytes=rss_mib * MIB,
        started_at=NOW - age,
        cpu_percent=cpu_percent,
        cwd=cwd,
    )


def make_context(
    processes: list[ProcessInfo],
    *,
    protected_pids: frozenset[int] = frozenset(),
    missing_paths: frozenset[str] = frozenset(),
) -> ScanContext:
    return ScanContext(
        tree=ProcessTree(processes),
        now=NOW,
        protected_pids=protected_pids,
        path_exists=lambda path: path not in missing_paths,
    )


def make_memory(*, swap_used_gib: int = 0, available_gib: int = 6) -> MemoryStatus:
    return MemoryStatus(
        total_bytes=10 * GIB,
        available_bytes=available_gib * GIB,
        swap_total_bytes=3 * GIB,
        swap_used_bytes=swap_used_gib * GIB,
    )


@dataclass
class FakeMachine:
    processes: list[ProcessInfo]
    memory: MemoryStatus = field(default_factory=make_memory)
    host: HostStatus | None = None
    machine_platform: Platform = Platform.LINUX
    terminated: list[int] = field(default_factory=list)

    def platform(self) -> Platform:
        return self.machine_platform

    def read_processes(self) -> list[ProcessInfo]:
        return self.processes

    def read_memory(self) -> MemoryStatus:
        return self.memory

    def read_host(self) -> HostStatus | None:
        return self.host

    def terminate(self, targets: Sequence[ProcessInfo]) -> list[int]:
        self.terminated += [target.pid for target in targets]
        return []
