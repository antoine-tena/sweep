from sweep.process_info import ProcessInfo
from sweep.rules.dev_servers import find_dev_server_candidates
from tests.factories import (
    CONTAINER_MOUNTS,
    INIT_PID,
    OWN_MOUNTS,
    TERMINAL,
    make_context,
    make_process,
)

GONE = "/code/app/.claude/worktrees/tresorerie/frontend"
MISSING = frozenset({GONE})


def _nuxt(
    ppid: int, terminal: str | None = None, mount_namespace: str = OWN_MOUNTS
) -> list[ProcessInfo]:
    return [
        make_process(
            10,
            "sh -c nuxt dev --port 3010",
            ppid=ppid,
            cwd=GONE,
            terminal=terminal,
            mount_namespace=mount_namespace,
        ),
        make_process(11, "node /x/nuxt.mjs dev --port 3010", ppid=10, cwd=GONE),
    ]


def test_detached_dev_server_whose_folder_was_deleted_is_certain() -> None:
    context = make_context(_nuxt(ppid=INIT_PID), missing_paths=MISSING)

    [candidate] = find_dev_server_candidates(context)

    assert (candidate.main_pid, set(candidate.pids), candidate.is_certain) == (10, {10, 11}, True)
    assert GONE in candidate.reason


def test_dev_server_still_in_a_terminal_is_only_to_check() -> None:
    context = make_context(_nuxt(ppid=INIT_PID, terminal=TERMINAL), missing_paths=MISSING)

    assert [candidate.is_certain for candidate in find_dev_server_candidates(context)] == [False]


def test_dev_server_whose_launcher_lives_is_only_to_check() -> None:
    context = make_context(_nuxt(ppid=700), missing_paths=MISSING)

    assert [candidate.is_certain for candidate in find_dev_server_candidates(context)] == [False]


def test_container_paths_are_not_checked_from_the_host() -> None:
    context = make_context(
        _nuxt(ppid=INIT_PID, mount_namespace=CONTAINER_MOUNTS)[:1], missing_paths=MISSING
    )

    assert find_dev_server_candidates(context) == []


def test_detached_dev_server_in_an_existing_folder_is_kept() -> None:
    server = make_process(10, "python manage.py runserver", ppid=INIT_PID, cwd="/code/app")

    assert find_dev_server_candidates(make_context([server])) == []
