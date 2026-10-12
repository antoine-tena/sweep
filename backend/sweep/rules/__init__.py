"""Les règles de détection : chacune lit la photo des process et désigne des candidats."""

from sweep.candidate import Candidate
from sweep.rules.agents import find_agent_candidates
from sweep.rules.dev_servers import find_dev_server_candidates
from sweep.rules.mcp import find_mcp_candidates
from sweep.rules.scan_context import ScanContext

RULES = (find_agent_candidates, find_mcp_candidates, find_dev_server_candidates)

__all__ = ["ScanContext", "find_candidates"]


def find_candidates(context: ScanContext) -> list[Candidate]:
    """Candidats de toutes les règles, sans process protégé ni doublon, les plus lourds d'abord."""
    claimed: set[int] = set()
    candidates = []
    for rule in RULES:
        for candidate in rule(context):
            pids = tuple(pid for pid in candidate.pids if pid not in context.protected_pids)
            if not pids or pids[0] != candidate.main_pid or candidate.main_pid in claimed:
                continue
            claimed.update(pids)
            rss_bytes = context.tree.rss_of(pids)
            candidates.append(
                Candidate(candidate.rule, candidate.label, candidate.reason, pids, rss_bytes)
            )
    return sorted(candidates, key=lambda candidate: candidate.rss_bytes, reverse=True)
