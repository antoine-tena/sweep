"""Ce dont le cœur a besoin de la machine : un `Protocol`, que les tests remplacent."""

from collections.abc import Sequence
from typing import Protocol

from sweep.host_status import HostStatus
from sweep.memory_status import MemoryStatus
from sweep.platforms import Platform
from sweep.process_info import ProcessInfo


class Machine(Protocol):
    def platform(self) -> Platform: ...

    def read_processes(self) -> list[ProcessInfo]: ...

    def read_memory(self) -> MemoryStatus: ...

    def read_host(self) -> HostStatus | None: ...

    def mount_namespace(self) -> str | None:
        """Espace de montage de sweep (Linux), pour reconnaître un process de conteneur."""
        ...

    def terminate(self, targets: Sequence[ProcessInfo]) -> list[int]:
        """Arrête les process encore identiques à leur photo ; renvoie les pid survivants."""
        ...
