"""Agents oubliés (vieux et inactifs) et conversations ouvertes deux fois."""

from collections import defaultdict
from datetime import timedelta

from sweep.candidate import Candidate
from sweep.process_info import ProcessInfo
from sweep.rules.patterns import (
    AGENT_PROGRAMS,
    AGENT_SCRIPT,
    IDLE_CPU_PERCENT,
    SESSION_FLAGS,
)
from sweep.rules.scan_context import ScanContext

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
        if is_agent(process) and not _has_agent_ancestor(context, process)
    ]
    duplicates = _older_duplicates(agents)
    idle = [agent for agent in agents if _is_idle(context, agent) and agent not in duplicates]
    candidates = [
        _candidate(context, agent, RULE_DUPLICATE, duplicates[agent]) for agent in duplicates
    ]
    candidates += [
        _candidate(context, agent, RULE_IDLE, _idle_reason(context, agent)) for agent in idle
    ]
    return candidates


def session_id(process: ProcessInfo) -> str | None:
    arguments = process.cmdline
    for index, argument in enumerate(arguments[:-1]):
        following = arguments[index + 1]
        if argument in SESSION_FLAGS and not following.startswith("-"):
            return following
    return None


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
                    f"{program} : conversation {session[:8]} rouverte (pid {newest.pid})"
                )
    return duplicates


def _age(context: ScanContext, process: ProcessInfo) -> timedelta:
    return context.now - process.started_at


def _is_idle(context: ScanContext, agent: ProcessInfo) -> bool:
    return _age(context, agent) >= context.idle_agent_age and agent.cpu_percent < IDLE_CPU_PERCENT


def _idle_reason(context: ScanContext, agent: ProcessInfo) -> str:
    hours = _age(context, agent).total_seconds() / SECONDS_PER_HOUR
    return f"{agent.program} lancé il y a {hours:.0f} h, sans activité"


def _candidate(context: ScanContext, agent: ProcessInfo, rule: str, reason: str) -> Candidate:
    pids = context.tree.subtree_pids(agent.pid)
    return Candidate(rule, agent.command_text, reason, pids, context.tree.rss_of(pids))
