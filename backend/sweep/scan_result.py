"""Ce qu'un passage de sweep a trouvé : mémoire, candidats, plus gros process, conseils."""

from dataclasses import dataclass

from sweep.candidate import Candidate
from sweep.host_status import HostStatus
from sweep.memory_status import MemoryStatus
from sweep.platforms import Platform
from sweep.process_info import ProcessInfo


@dataclass(frozen=True)
class ScanResult:
    platform: Platform
    memory: MemoryStatus
    host: HostStatus | None
    candidates: tuple[Candidate, ...]
    heaviest: tuple[ProcessInfo, ...]
    advice: tuple[str, ...]
    processes_by_pid: dict[int, ProcessInfo]

    @property
    def reclaimable_bytes(self) -> int:
        """Ce que libère `--kill` : les sûrs seulement."""
        return sum(candidate.rss_bytes for candidate in self.certain)

    @property
    def certain(self) -> tuple[Candidate, ...]:
        return tuple(candidate for candidate in self.candidates if candidate.is_certain)

    @property
    def uncertain(self) -> tuple[Candidate, ...]:
        return tuple(candidate for candidate in self.candidates if not candidate.is_certain)

    def chosen(self, main_pids: frozenset[int] | None) -> tuple[Candidate, ...]:
        """Les sûrs par défaut ; ceux qu'on désigne (`--pid`), sûrs ou non, sinon."""
        if main_pids is None:
            return self.certain
        return tuple(candidate for candidate in self.candidates if candidate.main_pid in main_pids)

    def targets(self, candidates: tuple[Candidate, ...]) -> list[ProcessInfo]:
        """Les process à arrêter, enfants compris, dans l'ordre des candidats."""
        return [
            self.processes_by_pid[pid]
            for candidate in candidates
            for pid in candidate.pids
            if pid in self.processes_by_pid
        ]
