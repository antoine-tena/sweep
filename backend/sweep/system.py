"""Accès à la machine par psutil ([SYSTEME-A-LA-FRONTIERE]) : process et mémoire."""

import time
from datetime import UTC, datetime

import psutil

from sweep.memory_status import MemoryStatus
from sweep.process_info import ProcessInfo

DEFAULT_SAMPLE_SECONDS = 1.0
GONE = (psutil.NoSuchProcess, psutil.ZombieProcess)


def read_memory() -> MemoryStatus:
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return MemoryStatus(
        total_bytes=ram.total,
        available_bytes=ram.available,
        swap_total_bytes=swap.total,
        swap_used_bytes=swap.used,
    )


def read_processes(sample_seconds: float = DEFAULT_SAMPLE_SECONDS) -> list[ProcessInfo]:
    """Tous les process lisibles ; le CPU est mesuré sur `sample_seconds`."""
    handles = list(psutil.process_iter())
    for handle in handles:
        try:
            handle.cpu_percent(None)
        except (*GONE, psutil.AccessDenied):
            continue
    time.sleep(sample_seconds)
    snapshots = (_snapshot(handle) for handle in handles)
    return [snapshot for snapshot in snapshots if snapshot is not None]


def _snapshot(handle: psutil.Process) -> ProcessInfo | None:
    try:
        with handle.oneshot():
            return ProcessInfo(
                pid=handle.pid,
                ppid=handle.ppid(),
                name=handle.name(),
                cmdline=_clean_cmdline(handle.cmdline()),
                rss_bytes=handle.memory_info().rss,
                started_at=datetime.fromtimestamp(handle.create_time(), UTC),
                cpu_percent=handle.cpu_percent(None),
                cwd=_cwd(handle),
            )
    except (*GONE, psutil.AccessDenied):
        return None


def _cwd(handle: psutil.Process) -> str | None:
    """Dossier courant, suffixé ` (deleted)` par Linux quand il a disparu ; None si illisible."""
    try:
        return handle.cwd()
    except (*GONE, psutil.AccessDenied, FileNotFoundError):
        return None


def _clean_cmdline(arguments: list[str]) -> tuple[str, ...]:
    """Sans les arguments vides de fin, que laisse un process qui réécrit son titre (npm)."""
    while arguments and not arguments[-1]:
        arguments = arguments[:-1]
    return tuple(arguments)
