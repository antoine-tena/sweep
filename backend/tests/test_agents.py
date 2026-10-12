from datetime import timedelta

from sweep.rules.agents import RULE_DUPLICATE, RULE_IDLE, find_agent_candidates
from tests.factories import make_context, make_process

LONG_AGO = timedelta(hours=10)


def test_old_idle_agent_is_a_candidate_with_its_children() -> None:
    context = make_context(
        [
            make_process(10, "agy", age=LONG_AGO, cpu_percent=0.1),
            make_process(11, "node mcp-server-x", ppid=10),
        ]
    )

    [candidate] = find_agent_candidates(context)

    assert (candidate.rule, set(candidate.pids)) == (RULE_IDLE, {10, 11})
    assert "10 h" in candidate.reason


def test_recent_or_busy_agents_are_kept() -> None:
    context = make_context(
        [
            make_process(10, "claude -c", age=timedelta(minutes=20)),
            make_process(11, "claude -r", age=LONG_AGO, cpu_percent=35.0),
        ]
    )

    assert find_agent_candidates(context) == []


def test_same_conversation_opened_twice_keeps_the_newest() -> None:
    context = make_context(
        [
            make_process(10, "agy --conversation 2c3e3f13-a739", age=timedelta(hours=5)),
            make_process(20, "agy --conversation 2c3e3f13-a739 --yolo", age=timedelta(minutes=2)),
        ]
    )

    [candidate] = find_agent_candidates(context)

    assert (candidate.rule, candidate.main_pid) == (RULE_DUPLICATE, 10)
    assert "pid 20" in candidate.reason


def test_agent_started_by_another_agent_is_not_counted_twice() -> None:
    context = make_context(
        [
            make_process(10, "claude", age=LONG_AGO),
            make_process(11, "claude --print sub-task", ppid=10, age=LONG_AGO),
        ]
    )

    assert [candidate.main_pid for candidate in find_agent_candidates(context)] == [10]
