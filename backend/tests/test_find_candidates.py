from datetime import timedelta

from sweep.rules import find_candidates
from tests.factories import INIT_PID, TERMINAL, make_context, make_process

LONG_AGO = timedelta(hours=8)


def test_protected_processes_are_never_candidates() -> None:
    context = make_context(
        [make_process(10, "claude", ppid=INIT_PID, age=LONG_AGO)], protected_pids=frozenset({10})
    )

    assert find_candidates(context) == []


def test_certain_come_first_then_heaviest_without_overlap() -> None:
    context = make_context(
        [
            make_process(10, "agy", ppid=INIT_PID, age=LONG_AGO, rss_mib=100),
            make_process(11, "npm exec context7-mcp", ppid=10, rss_mib=50),
            make_process(20, "claude", age=LONG_AGO, rss_mib=400, terminal=TERMINAL),
        ]
    )

    candidates = find_candidates(context)

    assert [(candidate.main_pid, candidate.is_certain) for candidate in candidates] == [
        (10, True),
        (20, False),
    ]
    assert sorted(pid for candidate in candidates for pid in candidate.pids) == [10, 11, 20]
