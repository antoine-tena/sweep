"""Ce que chaque règle reçoit : la photo des process et ce qui ne se touche pas."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from sweep.rules.tree import ProcessTree


@dataclass(frozen=True)
class ScanContext:
    tree: ProcessTree
    now: datetime
    # sweep lui-même et ses ancêtres (le terminal, l'agent qui l'a lancé) : jamais candidats.
    protected_pids: frozenset[int]
    path_exists: Callable[[str], bool]
