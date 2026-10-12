"""Preuves qu'un process est abandonné : son lanceur est mort, plus personne ne lui parle."""

from sweep.process_info import ProcessInfo
from sweep.rules.scan_context import ScanContext

INIT_PID = 1
# Ceux qui recueillent les orphelins : `/init` de WSL (un « Relay » par terminal, et le pid 1
# sans systemd) et `systemd --user` des bureaux Linux.
REAPER_PROGRAMS = frozenset({"init"})
USER_REAPER_PROGRAM = "systemd"
USER_REAPER_FLAG = "--user"


def is_reparented(context: ScanContext, process: ProcessInfo) -> bool:
    """Rattaché à un process qui recueille les orphelins : son lanceur est mort.

    Ne prouve pas un abandon à lui seul : un serveur lancé exprès en fond l'est aussi.
    """
    if not context.can_trace_orphans:
        return False
    if process.ppid == INIT_PID:
        return True
    parent = context.tree.by_pid.get(process.ppid)
    if parent is None:
        return False
    is_user_reaper = parent.program == USER_REAPER_PROGRAM and USER_REAPER_FLAG in parent.cmdline
    return parent.program in REAPER_PROGRAMS or is_user_reaper


def pipe_is_abandoned(context: ScanContext, pipe: str, group_pids: tuple[int, ...]) -> bool:
    """Aucun process hors du groupe ne tient ce canal : personne ne peut plus y écrire."""
    group = frozenset(group_pids)
    return not any(
        pipe in process.open_pipes
        for process in context.tree.by_pid.values()
        if process.pid not in group
    )
