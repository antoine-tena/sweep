from datetime import timedelta

from sweep.rules.agents import RULE_DUPLICATE, RULE_IDLE, RULE_ORPHAN, find_agent_candidates
from tests.factories import INIT_PID, TERMINAL, make_context, make_process

LONG_AGO = timedelta(hours=10)


def test_agent_without_terminal_nor_launcher_is_certain_with_its_children() -> None:
    context = make_context(
        [
            make_process(10, "agy", ppid=INIT_PID, age=LONG_AGO),
            make_process(11, "node mcp-server-x", ppid=10),
        ]
    )

    [candidate] = find_agent_candidates(context)

    assert (candidate.rule, candidate.is_certain) == (RULE_ORPHAN, True)
    assert set(candidate.pids) == {10, 11}


def test_old_idle_agent_in_a_terminal_is_only_to_check() -> None:
    context = make_context([make_process(10, "claude -c", age=LONG_AGO, terminal=TERMINAL)])

    [candidate] = find_agent_candidates(context)

    assert (candidate.rule, candidate.is_certain) == (RULE_IDLE, False)
    assert "attend-il une réponse" in candidate.reason


def test_headless_agent_without_terminal_is_not_an_orphan() -> None:
    context = make_context(
        [make_process(10, "claude -p résume", ppid=INIT_PID, age=timedelta(minutes=30))]
    )

    assert find_agent_candidates(context) == []


def test_busy_or_recent_agents_are_kept() -> None:
    context = make_context(
        [
            make_process(10, "claude -c", age=timedelta(minutes=20), terminal=TERMINAL),
            make_process(11, "claude -r", age=LONG_AGO, cpu_percent=35.0, terminal=TERMINAL),
            make_process(12, "agy", ppid=INIT_PID, age=LONG_AGO, cpu_percent=12.0),
        ]
    )

    assert find_agent_candidates(context) == []


def test_agent_still_owned_by_its_shell_is_never_certain() -> None:
    context = make_context([make_process(10, "agy", age=LONG_AGO)])

    assert [candidate.is_certain for candidate in find_agent_candidates(context)] == [False]


def test_windows_never_proves_an_orphan_agent() -> None:
    context = make_context(
        [make_process(10, "agy", ppid=INIT_PID, age=LONG_AGO)], can_trace_orphans=False
    )

    assert [candidate.is_certain for candidate in find_agent_candidates(context)] == [False]


def test_same_conversation_opened_twice_is_only_to_check() -> None:
    context = make_context(
        [
            make_process(10, "agy --conversation 2c3e3f13-a739", age=timedelta(hours=5)),
            make_process(20, "agy --conversation 2c3e3f13-a739 --yolo", age=timedelta(minutes=2)),
        ]
    )

    [candidate] = find_agent_candidates(context)

    assert (candidate.rule, candidate.main_pid, candidate.is_certain) == (RULE_DUPLICATE, 10, False)
    assert "pid 20" in candidate.reason


def test_agent_started_by_another_agent_is_not_counted_twice() -> None:
    context = make_context(
        [
            make_process(10, "claude", age=LONG_AGO),
            make_process(11, "claude --print sub-task", ppid=10, age=LONG_AGO),
        ]
    )

    assert [candidate.main_pid for candidate in find_agent_candidates(context)] == [10]


def test_other_users_agents_are_ignored() -> None:
    context = make_context([make_process(10, "agy", ppid=INIT_PID, age=LONG_AGO, is_own=False)])

    assert find_agent_candidates(context) == []


def test_agent_recollected_by_a_wsl_relay_is_an_orphan() -> None:
    relay = make_process(5, "/init", ppid=4, name="Relay(6)")
    agent = make_process(10, "agy", ppid=5, age=LONG_AGO)

    [candidate] = find_agent_candidates(make_context([relay, agent]))

    assert candidate.is_certain
