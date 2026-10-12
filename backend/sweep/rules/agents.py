"""Agents : sans terminal ni lanceur (sûr), vieux et inactifs ou en double (à vérifier)."""

from collections import defaultdict
from datetime import timedelta

from sweep.candidate import Candidate
from sweep.process_info import ProcessInfo
from sweep.rules.orphans import is_reparented
from sweep.rules.patterns import (
    AGENT_PROGRAMS,
    AGENT_SCRIPT,
    HEADLESS_ARGUMENTS,
    IDLE_CPU_PERCENT,
    SESSION_FLAGS,
)
from sweep.rules.scan_context import ScanContext

RULE_ORPHAN = "agent-sans-terminal"
RULE_IDLE = "agent-inactif"
RULE_DUPLICATE = "conversation-en-double"
SECONDS_PER_HOUR = 3600


def is_agent(process: ProcessInfo) -> bool:
    if process.program in AGENT_PROGRAMS:
        return True
    return any(AGENT_SCRIPT.search(argument) for argument in process.cmdline[1:2])


def find_agent_candidates(context: ScanContext) -> list[Candidate]:
    agents = [
        process
        for process in context.tree.by_pid.values()
        if process.is_own and is_agent(process) and not _has_agent_ancestor(context, process)
    ]
    duplicates = _older_duplicates(agents)
    candidates = []
    for agent in agents:
        if _is_orphan(context, agent):
            candidates.append(_candidate(context, agent, RULE_ORPHAN, _orphan_reason(agent), True))
        elif agent in duplicates:
            candidates.append(_candidate(context, agent, RULE_DUPLICATE, duplicates[agent], False))
        elif _is_idle(context, agent):
            reason = _idle_reason(context, agent)
            candidates.append(_candidate(context, agent, RULE_IDLE, reason, False))
    return candidates


def session_id(process: ProcessInfo) -> str | None:
    arguments = process.cmdline
    for index, argument in enumerate(arguments[:-1]):
        following = arguments[index + 1]
        if argument in SESSION_FLAGS and not following.startswith("-"):
            return following
    return None


def _is_orphan(context: ScanContext, agent: ProcessInfo) -> bool:
    """Interactif, sans terminal, lanceur mort, inactif : personne ne peut plus lui parler."""
    is_headless = any(argument in HEADLESS_ARGUMENTS for argument in agent.cmdline[1:])
    return (
        not is_headless
        and agent.terminal is None
        and is_reparented(context, agent)
        and agent.cpu_percent < IDLE_CPU_PERCENT
    )


def _has_agent_ancestor(context: ScanContext, process: ProcessInfo) -> bool:
    return any(is_agent(ancestor) for ancestor in context.tree.ancestors(process.pid))


def _older_duplicates(agents: list[ProcessInfo]) -> dict[ProcessInfo, str]:
    by_session: defaultdict[tuple[str, str], list[ProcessInfo]] = defaultdict(list)
    for agent in agents:
        if (session := session_id(agent)) is not None:
            by_session[(agent.program, session)].append(agent)
    duplicates = {}
    for (program, session), same_session in by_session.items():
        newest = max(same_session, key=lambda agent: agent.started_at)
        for agent in same_session:
            if agent is not newest:
                duplicates[agent] = (
                    f"{program} : conversation {session[:8]} ouverte aussi par le pid {newest.pid}"
                )
    return duplicates


def _age(context: ScanContext, process: ProcessInfo) -> timedelta:
    return context.now - process.started_at


def _is_idle(context: ScanContext, agent: ProcessInfo) -> bool:
    return _age(context, agent) >= context.idle_agent_age and agent.cpu_percent < IDLE_CPU_PERCENT


def _idle_reason(context: ScanContext, agent: ProcessInfo) -> str:
    hours = _age(context, agent).total_seconds() / SECONDS_PER_HOUR
    return f"{agent.program} lancé il y a {hours:.0f} h, sans activité (attend-il une réponse ?)"


def _orphan_reason(agent: ProcessInfo) -> str:
    return f"{agent.program} sans terminal et sans lanceur : plus personne ne peut lui parler"


def _candidate(
    context: ScanContext, agent: ProcessInfo, rule: str, reason: str, is_certain: bool
) -> Candidate:
    pids = context.tree.subtree_pids(agent.pid)
    return Candidate(rule, agent.command_text, reason, pids, context.tree.rss_of(pids), is_certain)
