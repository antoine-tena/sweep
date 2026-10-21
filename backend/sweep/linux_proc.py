"""Ce que psutil ne donne pas, lu dans /proc (Linux et WSL) : entrée standard, canaux, montage."""

import os
from dataclasses import dataclass
from pathlib import Path

from sweep.process_info import PIPE_PREFIX

PROC = Path("/proc")


@dataclass(frozen=True)
class ProcDetails:
    stdin_target: str | None
    open_pipes: frozenset[str]
    mount_namespace: str | None


NO_DETAILS = ProcDetails(stdin_target=None, open_pipes=frozenset(), mount_namespace=None)


def read_proc_details(pid: int) -> ProcDetails:
    """Tout ce qui est illisible (process d'un autre, disparu) reste à None ou vide."""
    process_dir = PROC / str(pid)
    if not process_dir.is_dir():
        return NO_DETAILS
    return ProcDetails(
        stdin_target=_readlink(process_dir / "fd" / "0"),
        open_pipes=_open_pipes(process_dir / "fd"),
        mount_namespace=_readlink(process_dir / "ns" / "mnt"),
    )


def own_mount_namespace() -> str | None:
    return _readlink(PROC / "self" / "ns" / "mnt")


def _open_pipes(fd_dir: Path) -> frozenset[str]:
    try:
        descriptors = os.listdir(fd_dir)
    except OSError:
        return frozenset()
    targets = (_readlink(fd_dir / descriptor) for descriptor in descriptors)
    return frozenset(
        target for target in targets if target is not None and target.startswith(PIPE_PREFIX)
    )


def _readlink(link: Path) -> str | None:
    try:
        return os.readlink(link)
    except OSError:
        return None
