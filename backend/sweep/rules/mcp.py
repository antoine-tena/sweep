"""Serveurs MCP orphelins : plus aucun agent ni éditeur au-dessus d'eux."""

from sweep.candidate import Candidate
from sweep.process_info import ProcessInfo
from sweep.rules.agents import is_agent
from sweep.rules.patterns import (
    EDITOR_MARKERS,
    LAUNCHER_PROGRAMS,
    MCP_ARGUMENTS_SCANNED,
    MCP_NAME,
    MCP_STDIO_PROGRAMS,
    STDIO_FLAG,
)
from sweep.rules.scan_context import ScanContext

RULE = "mcp-orphelin"


def is_mcp_server(process: ProcessInfo) -> bool:
    if process.program in MCP_STDIO_PROGRAMS and STDIO_FLAG in process.cmdline:
        return True
    return any(_names_mcp_server(argument) for argument in _leading_arguments(process))


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


def find_mcp_candidates(context: ScanContext) -> list[Candidate]:
    roots = {
        _launch_root(context, process).pid
        for process in context.tree.by_pid.values()
        if is_mcp_server(process)
    }
    candidates = []
    for root_pid in sorted(roots):
        root = context.tree.by_pid[root_pid]
        if any(_is_owner(ancestor) for ancestor in context.tree.ancestors(root_pid)):
            continue
        pids = context.tree.subtree_pids(root_pid)
        reason = "serveur MCP dont l'agent est fermé"
        candidates.append(
            Candidate(RULE, root.command_text, reason, pids, context.tree.rss_of(pids))
        )
    return candidates


def _launch_root(context: ScanContext, process: ProcessInfo) -> ProcessInfo:
    """Remonte les lanceurs (`npm exec`, `sh -c`, autre MCP) : on tue le groupe entier."""
    root = process
    for ancestor in context.tree.ancestors(process.pid):
        if _is_owner(ancestor) or not (
            ancestor.program in LAUNCHER_PROGRAMS or is_mcp_server(ancestor)
        ):
            break
        root = ancestor
    return root


def _is_owner(process: ProcessInfo) -> bool:
    return is_agent(process) or any(marker in process.command_text for marker in EDITOR_MARKERS)
