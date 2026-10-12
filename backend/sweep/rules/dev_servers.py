"""Serveurs de développement lancés depuis un dossier qui n'existe plus (worktree supprimé)."""

from sweep.candidate import Candidate
from sweep.process_info import ProcessInfo
from sweep.rules.patterns import DEV_SERVER_COMMAND
from sweep.rules.scan_context import ScanContext

RULE = "serveur-dev-orphelin"


def is_dev_server(process: ProcessInfo) -> bool:
    return DEV_SERVER_COMMAND.search(process.command_text) is not None


def find_dev_server_candidates(context: ScanContext) -> list[Candidate]:
    candidates = []
    for process in context.tree.by_pid.values():
        if not is_dev_server(process) or _parent_is_dev_server(context, process):
            continue
        if process.cwd is None or context.path_exists(process.cwd):
            continue
        pids = context.tree.subtree_pids(process.pid)
        reason = f"son dossier a disparu : {process.cwd}"
        candidates.append(
            Candidate(RULE, process.command_text, reason, pids, context.tree.rss_of(pids))
        )
    return candidates


def _parent_is_dev_server(context: ScanContext, process: ProcessInfo) -> bool:
    parent = context.tree.by_pid.get(process.ppid)
    return parent is not None and is_dev_server(parent)
