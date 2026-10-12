from sweep.process_info import ProcessInfo
from sweep.rules.mcp import find_mcp_candidates, is_mcp_server
from tests.factories import make_context, make_process

AGENT_PID = 10


def _mcp_group(ppid: int) -> list[ProcessInfo]:
    return [
        make_process(20, "npm exec @playwright/mcp@0.0.83 --headless", ppid=ppid, rss_mib=90),
        make_process(21, "sh -c playwright-mcp", ppid=20, rss_mib=2),
        make_process(22, "node /npx/.bin/playwright-mcp --headless", ppid=21, rss_mib=110),
    ]


def test_mcp_server_left_by_a_closed_agent_is_killed_with_its_launchers() -> None:
    context = make_context(_mcp_group(ppid=1))

    [candidate] = find_mcp_candidates(context)

    assert candidate.main_pid == 20
    assert set(candidate.pids) == {20, 21, 22}


def test_mcp_server_of_a_live_agent_is_kept() -> None:
    context = make_context([make_process(AGENT_PID, "claude -r"), *_mcp_group(ppid=AGENT_PID)])

    assert find_mcp_candidates(context) == []


def test_mcp_server_of_an_editor_is_kept() -> None:
    editor = make_process(5, "/home/u/.vscode-server/bin/node --type=extensionHost")

    assert find_mcp_candidates(make_context([editor, *_mcp_group(ppid=5)])) == []


def test_mcp_lookalikes_are_not_servers() -> None:
    lookalikes = [
        make_process(30, "postgres: annski_mcp_lecture annski 172.21.96.128 idle"),
        make_process(31, "python -c from_sweep.rules.mcp_import_x"),
        make_process(32, "vim notes/mcp.md"),
    ]

    assert not [process for process in lookalikes if is_mcp_server(process)]


def test_stdio_toolbox_is_a_server() -> None:
    assert is_mcp_server(make_process(40, "/npx/bin/toolbox --prebuilt postgres --stdio"))
