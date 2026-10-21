"""Ce que chaque règle reçoit : la photo des process et ce qui ne se touche pas."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from sweep.process_info import ProcessInfo
from sweep.rules.patterns import IDLE_AGENT_AGE
from sweep.rules.tree import ProcessTree


@dataclass(frozen=True)
class ScanContext:
    tree: ProcessTree
    now: datetime
    # sweep lui-même et ses ancêtres (le terminal, l'agent qui l'a lancé) : jamais candidats.
    protected_pids: frozenset[int]
    path_exists: Callable[[str], bool]
    idle_agent_age: timedelta = IDLE_AGENT_AGE
    # Faux sous Windows : un orphelin y garde le pid de son parent mort, parfois réattribué.
    can_trace_orphans: bool = True
    own_mount_namespace: str | None = None

    def in_own_mounts(self, process: ProcessInfo) -> bool:
        """Même espace de montage que sweep : ses chemins se vérifient d'ici (pas un conteneur)."""
        return (
            process.mount_namespace is None or process.mount_namespace == self.own_mount_namespace
        )
