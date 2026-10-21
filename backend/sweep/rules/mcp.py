"""Serveurs MCP dont l'agent est mort : sûr si plus personne ne tient leur canal d'entrée."""

from sweep.candidate import Candidate
from sweep.process_info import ProcessInfo
from sweep.rules.orphans import is_reparented, pipe_is_abandoned
from sweep.rules.patterns import (
    LAUNCHER_PROGRAMS,
    MCP_ARGUMENTS_SCANNED,
    MCP_NAME,
    MCP_STDIO_PROGRAMS,
    STDIO_FLAG,
)
from sweep.rules.scan_context import ScanContext

RULE = "mcp-orphelin"
REASON_CERTAIN = "serveur MCP dont l'agent est fermé : plus personne ne lui écrit"
REASON_UNCHECKED = "serveur MCP rattaché au système, canal d'entrée invérifiable ici"
REASON_DETACHED = "serveur MCP détaché, sans canal d'entrée : lancé à part exprès ?"


def is_mcp_server(process: ProcessInfo) -> bool:
    if process.program in MCP_STDIO_PROGRAMS and STDIO_FLAG in process.cmdline:
        return True
    return any(_names_mcp_server(argument) for argument in _leading_arguments(process))


def find_mcp_candidates(context: ScanContext) -> list[Candidate]:
    roots = {
        _launch_root(context, process).pid
        for process in context.tree.by_pid.values()
        if process.is_own and is_mcp_server(process)
    }
    candidates = []
    for root_pid in sorted(roots):
        root = context.tree.by_pid[root_pid]
        if not _lost_its_launcher(context, root):
            continue
        pids = context.tree.subtree_pids(root_pid)
        verdict = _verdict(context, root, pids)
        if verdict is None:
            continue
        reason, is_certain = verdict
        rss_bytes = context.tree.rss_of(pids)
        candidates.append(Candidate(RULE, root.command_text, reason, pids, rss_bytes, is_certain))
    return candidates


def _lost_its_launcher(context: ScanContext, root: ProcessInfo) -> bool:
    if not context.can_trace_orphans:
        return root.ppid not in context.tree.by_pid
    return is_reparented(context, root)


def _verdict(
    context: ScanContext, root: ProcessInfo, pids: tuple[int, ...]
) -> tuple[str, bool] | None:
    """(raison, sûr) ; None si quelqu'un hors du groupe tient encore son canal : il sert.

    Seul le canal d'entrée de la racine compte : c'est par lui que l'agent parlait au groupe.
    Les canaux internes (npm vers node) ne prouvent rien.
    """
    pipe = root.stdin_pipe
    if pipe is not None:
        return (REASON_CERTAIN, True) if pipe_is_abandoned(context, pipe, pids) else None
    if root.stdin_target is not None:
        return REASON_DETACHED, False
    return REASON_UNCHECKED, False


def _launch_root(context: ScanContext, process: ProcessInfo) -> ProcessInfo:
    """Remonte les lanceurs (`npm exec`, `sh -c`, autre MCP) : on arrête le groupe entier."""
    root = process
    for ancestor in context.tree.ancestors(process.pid):
        if not ancestor.is_own or not (
            ancestor.program in LAUNCHER_PROGRAMS or is_mcp_server(ancestor)
        ):
            break
        root = ancestor
    return root


def _leading_arguments(process: ProcessInfo) -> tuple[str, ...]:
    """npm et d'autres réécrivent leur titre en une seule chaîne (`npm exec @playwright/mcp`)."""
    arguments = process.cmdline
    if len(arguments) == 1:
        arguments = tuple(arguments[0].split())
    return arguments[:MCP_ARGUMENTS_SCANNED]


def _names_mcp_server(argument: str) -> bool:
    if any(character.isspace() for character in argument):
        return False
    last_segment = argument.rstrip("/").rsplit("/", 1)[-1]
    return MCP_NAME.search(last_segment) is not None
