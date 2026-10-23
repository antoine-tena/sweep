"""Arrêt des process : SIGTERM, puis SIGKILL pour ceux qui l'ignorent ([DESTRUCTIVE-ACTIONS])."""

from collections.abc import Sequence
from datetime import UTC, datetime

import psutil

from sweep.process_info import ProcessInfo

GRACE_SECONDS = 3.0
# create_time est arrondi par le système : une photo et une relecture peuvent différer un peu.
START_TOLERANCE_SECONDS = 1.0


def terminate_processes(targets: Sequence[ProcessInfo]) -> list[int]:
    handles = [handle for target in targets if (handle := _same_process(target)) is not None]
    for handle in handles:
        _send(handle, is_forced=False)
    _, alive = psutil.wait_procs(handles, timeout=GRACE_SECONDS)
    for handle in alive:
        _send(handle, is_forced=True)
    _, survivors = psutil.wait_procs(alive, timeout=GRACE_SECONDS)
    return [handle.pid for handle in survivors]


def _same_process(target: ProcessInfo) -> psutil.Process | None:
    """Le process vivant, s'il est bien celui de la photo (un pid peut avoir été réattribué)."""
    try:
        handle = psutil.Process(target.pid)
        started_at = datetime.fromtimestamp(handle.create_time(), UTC)
    except psutil.NoSuchProcess, psutil.AccessDenied:
        return None
    drift = abs((started_at - target.started_at).total_seconds())
    return handle if drift <= START_TOLERANCE_SECONDS else None


def _send(handle: psutil.Process, *, is_forced: bool) -> None:
    try:
        if is_forced:
            handle.kill()
        else:
            handle.terminate()
            # Un process suspendu ne reçoit SIGTERM qu'une fois relancé.
            handle.resume()
    except psutil.NoSuchProcess, psutil.AccessDenied:
        return
