"""Accès à la machine par psutil ([SYSTEME-A-LA-FRONTIERE]) : process et mémoire."""

import os
import sys
import time
from datetime import UTC, datetime

import psutil

from sweep.linux_proc import NO_DETAILS, read_proc_details
from sweep.memory_status import MemoryStatus
from sweep.process_info import ProcessInfo

DEFAULT_SAMPLE_SECONDS = 1.0
GONE = (psutil.NoSuchProcess, psutil.ZombieProcess)
HAS_PROC = sys.platform.startswith("linux")


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
    owner = _owner_key(psutil.Process())
    snapshots = (_snapshot(handle, owner) for handle in handles)
    return [snapshot for snapshot in snapshots if snapshot is not None]


def _snapshot(handle: psutil.Process, owner: object) -> ProcessInfo | None:
    try:
        with handle.oneshot():
            details = read_proc_details(handle.pid) if HAS_PROC else NO_DETAILS
            return ProcessInfo(
                pid=handle.pid,
                ppid=handle.ppid(),
                name=handle.name(),
                cmdline=_clean_cmdline(handle.cmdline()),
                rss_bytes=handle.memory_info().rss,
                started_at=datetime.fromtimestamp(handle.create_time(), UTC),
                cpu_percent=handle.cpu_percent(None),
                cwd=_cwd(handle),
                is_own=_owner_key(handle) == owner,
                terminal=_terminal(handle),
                is_stopped=handle.status() == psutil.STATUS_STOPPED,
                stdin_target=details.stdin_target,
                open_pipes=details.open_pipes,
                mount_namespace=details.mount_namespace,
            )
    except (*GONE, psutil.AccessDenied):
        return None


def _owner_key(handle: psutil.Process) -> object:
    """L'uid réel sous Unix, le nom d'utilisateur sous Windows ; None si illisible."""
    try:
        return handle.uids().real if hasattr(os, "getuid") else handle.username()
    except (*GONE, psutil.AccessDenied):
        return None


def _terminal(handle: psutil.Process) -> str | None:
    """Le terminal, s'il existe encore (Windows n'en a pas la notion : None)."""
    try:
        terminal = handle.terminal() if hasattr(handle, "terminal") else None
    except (*GONE, psutil.AccessDenied):
        return None
    return terminal if terminal is not None and os.path.exists(terminal) else None


def _cwd(handle: psutil.Process) -> str | None:
    """Dossier courant ; None si illisible."""
    try:
        return handle.cwd()
    except (*GONE, psutil.AccessDenied, FileNotFoundError):
        return None


def _clean_cmdline(arguments: list[str]) -> tuple[str, ...]:
    """Sans les arguments vides de fin, que laisse un process qui réécrit son titre (npm)."""
    while arguments and not arguments[-1]:
        arguments = arguments[:-1]
    return tuple(arguments)
