from sweep.rules.dev_servers import find_dev_server_candidates
from tests.factories import make_context, make_process

GONE = "/code/app/.claude/worktrees/tresorerie/frontend"


def test_dev_server_whose_folder_was_deleted_is_a_candidate() -> None:
    context = make_context(
        [
            make_process(10, "sh -c nuxt dev --port 3010", cwd=GONE),
            make_process(11, "node /x/nuxt.mjs dev --port 3010", ppid=10, cwd=GONE),
        ],
        missing_paths=frozenset({GONE}),
    )

    [candidate] = find_dev_server_candidates(context)

    assert (candidate.main_pid, set(candidate.pids)) == (10, {10, 11})
    assert GONE in candidate.reason


def test_dev_server_in_an_existing_folder_is_kept() -> None:
    context = make_context([make_process(10, "python manage.py runserver", cwd="/code/app")])

    assert find_dev_server_candidates(context) == []
