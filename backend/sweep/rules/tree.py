"""Arbre des process : parents, descendants, et mémoire d'un sous-arbre."""

from collections import defaultdict
from collections.abc import Iterator, Mapping

from sweep.process_info import ProcessInfo


class ProcessTree:
    def __init__(self, processes: list[ProcessInfo]) -> None:
        self.by_pid: Mapping[int, ProcessInfo] = {process.pid: process for process in processes}
        children: defaultdict[int, list[int]] = defaultdict(list)
        for process in processes:
            if process.ppid != process.pid:
                children[process.ppid].append(process.pid)
        self._children = children

    def ancestors(self, pid: int) -> Iterator[ProcessInfo]:
        """Les parents successifs, du plus proche au plus lointain."""
        seen = {pid}
        current = self.by_pid.get(pid)
        while current is not None and current.ppid not in seen:
            seen.add(current.ppid)
            current = self.by_pid.get(current.ppid)
            if current is not None:
                yield current

    def subtree_pids(self, pid: int) -> tuple[int, ...]:
        """Le process et tous ses descendants, la racine en tête."""
        ordered, pending = [], [pid]
        while pending:
            current_pid = pending.pop()
            if current_pid in ordered:
                continue
            ordered.append(current_pid)
            pending.extend(self._children.get(current_pid, ()))
        return tuple(ordered)

    def rss_of(self, pids: tuple[int, ...]) -> int:
        return sum(self.by_pid[pid].rss_bytes for pid in pids if pid in self.by_pid)
