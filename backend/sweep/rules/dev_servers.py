"""Serveurs de développement dont le dossier a disparu (worktree supprimé)."""

from sweep.candidate import Candidate
from sweep.process_info import ProcessInfo
from sweep.rules.orphans import is_reparented
from sweep.rules.patterns import DEV_SERVER_COMMAND
from sweep.rules.scan_context import ScanContext

RULE = "serveur-dev-orphelin"


def is_dev_server(process: ProcessInfo) -> bool:
    return DEV_SERVER_COMMAND.search(process.command_text) is not None


def find_dev_server_candidates(context: ScanContext) -> list[Candidate]:
    candidates = []
    for process in context.tree.by_pid.values():
        if not _lost_its_folder(context, process) or _parent_is_dev_server(context, process):
            continue
        pids = context.tree.subtree_pids(process.pid)
        # Sans terminal ni lanceur, personne ne le regarde tourner ; sinon, peut-être quelqu'un.
        is_certain = process.terminal is None and is_reparented(context, process)
        reason = f"son dossier a disparu : {process.cwd}"
        if not is_certain:
            reason += " (encore attaché à un terminal ou à son lanceur)"
        rss_bytes = context.tree.rss_of(pids)
        candidates.append(
            Candidate(RULE, process.command_text, reason, pids, rss_bytes, is_certain)
        )
    return candidates


def _lost_its_folder(context: ScanContext, process: ProcessInfo) -> bool:
    """Seuls les chemins vus depuis l'espace de montage de sweep se vérifient (pas un conteneur)."""
    return (
        process.is_own
        and is_dev_server(process)
        and process.cwd is not None
        and context.in_own_mounts(process)
        and not context.path_exists(process.cwd)
    )


def _parent_is_dev_server(context: ScanContext, process: ProcessInfo) -> bool:
    parent = context.tree.by_pid.get(process.ppid)
    return parent is not None and is_dev_server(parent)
