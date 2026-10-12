from datetime import timedelta

from sweep.rules import find_candidates
from tests.factories import make_context, make_process

LONG_AGO = timedelta(hours=8)


def test_protected_processes_are_never_candidates() -> None:
    context = make_context(
        [make_process(10, "claude", age=LONG_AGO)], protected_pids=frozenset({10})
    )

    assert find_candidates(context) == []


def test_candidates_are_sorted_heaviest_first_without_overlap() -> None:
    context = make_context(
        [
            make_process(10, "agy", age=LONG_AGO, rss_mib=100),
            make_process(11, "npm exec context7-mcp", ppid=10, rss_mib=50),
            make_process(20, "claude", age=LONG_AGO, rss_mib=400),
        ]
    )

    candidates = find_candidates(context)

    assert [candidate.main_pid for candidate in candidates] == [20, 10]
    assert sorted(pid for candidate in candidates for pid in candidate.pids) == [10, 11, 20]
