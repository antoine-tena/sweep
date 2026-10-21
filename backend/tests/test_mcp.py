from sweep.process_info import ProcessInfo
from sweep.rules.mcp import find_mcp_candidates, is_mcp_server
from tests.factories import INIT_PID, make_context, make_process

AGENT_PID = 10
AGENT_PIPE = "pipe:[777]"
INTERNAL_PIPE = "pipe:[888]"
NPM_EXEC = "npm exec @playwright/mcp@0.0.83"


def _mcp_group(ppid: int, stdin_target: str | None = AGENT_PIPE) -> list[ProcessInfo]:
    """npm exec → sh → node, qui lisent tous le canal que l'agent leur a donné."""
    is_pipe = stdin_target is not None and stdin_target.startswith("pipe:")
    held = frozenset({stdin_target}) if is_pipe and stdin_target is not None else frozenset()
    commands = [
        (20, NPM_EXEC, ppid),
        (21, "sh -c playwright-mcp", 20),
        (22, "node playwright-mcp", 21),
    ]
    return [
        make_process(pid, command, ppid=parent, stdin_target=stdin_target, open_pipes=held)
        for pid, command, parent in commands
    ]


def test_mcp_server_nobody_writes_to_is_certain_with_its_launchers() -> None:
    [candidate] = find_mcp_candidates(make_context(_mcp_group(ppid=INIT_PID)))

    assert (candidate.main_pid, candidate.is_certain) == (20, True)
    assert set(candidate.pids) == {20, 21, 22}


def test_mcp_server_of_a_live_parent_is_kept_whatever_the_parent() -> None:
    unknown_host = make_process(
        AGENT_PID, "/opt/zed/zed-editor", open_pipes=frozenset({AGENT_PIPE})
    )
    context = make_context([unknown_host, *_mcp_group(ppid=AGENT_PID)])

    assert find_mcp_candidates(context) == []


def test_reparented_mcp_whose_pipe_is_still_held_elsewhere_is_kept() -> None:
    writer = make_process(30, "claude", open_pipes=frozenset({AGENT_PIPE}))

    assert find_mcp_candidates(make_context([writer, *_mcp_group(ppid=INIT_PID)])) == []


def test_detached_daemon_with_internal_pipes_is_only_to_check() -> None:
    daemon = make_process(
        40, "mcp-server-http --port 9000", ppid=INIT_PID, stdin_target="/dev/null"
    )
    child = make_process(
        41,
        "node worker",
        ppid=40,
        stdin_target=INTERNAL_PIPE,
        open_pipes=frozenset({INTERNAL_PIPE}),
    )

    [candidate] = find_mcp_candidates(make_context([daemon, child]))

    assert (candidate.main_pid, candidate.is_certain) == (40, False)


def test_unverifiable_platforms_only_report_to_check() -> None:
    context = make_context(_mcp_group(ppid=999, stdin_target=None), can_trace_orphans=False)

    assert [candidate.is_certain for candidate in find_mcp_candidates(context)] == [False]


def test_other_users_mcp_servers_are_ignored() -> None:
    server = make_process(50, "mcp-server-x", ppid=INIT_PID, is_own=False)

    assert find_mcp_candidates(make_context([server])) == []


def test_mcp_lookalikes_are_not_servers() -> None:
    lookalikes = [
        make_process(30, "postgres: annski_mcp_lecture annski 172.21.96.128 idle"),
        make_process(31, "python -c from_sweep.rules.mcp_import_x"),
        make_process(32, "vim notes/mcp.md"),
    ]

    assert not [process for process in lookalikes if is_mcp_server(process)]


def test_stdio_toolbox_is_a_server() -> None:
    assert is_mcp_server(make_process(40, "/npx/bin/toolbox --prebuilt postgres --stdio"))
