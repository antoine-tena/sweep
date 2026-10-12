from sweep.rules.tree import ProcessTree
from tests.factories import make_process


def test_subtree_lists_root_first_and_sums_memory() -> None:
    tree = ProcessTree(
        [
            make_process(10, "npm exec @playwright/mcp", rss_mib=90),
            make_process(11, "node playwright-mcp", ppid=10, rss_mib=110),
            make_process(12, "chromium --headless", ppid=11, rss_mib=200),
            make_process(20, "bash", rss_mib=5),
        ]
    )

    pids = tree.subtree_pids(10)

    assert pids[0] == 10
    assert set(pids) == {10, 11, 12}
    assert tree.rss_of(pids) == 400 * 1024**2


def test_ancestors_stop_on_a_cycle() -> None:
    tree = ProcessTree([make_process(10, "a", ppid=11), make_process(11, "b", ppid=10)])

    assert [ancestor.pid for ancestor in tree.ancestors(10)] == [11]
