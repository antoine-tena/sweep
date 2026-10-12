"""La vraie machine : psutil, PowerShell sous WSL."""

from collections.abc import Sequence

from sweep.host_status import HostStatus
from sweep.linux_proc import own_mount_namespace
from sweep.memory_status import MemoryStatus
from sweep.platforms import Platform, detect_platform
from sweep.process_info import ProcessInfo
from sweep.system import HAS_PROC, read_memory, read_processes
from sweep.terminate import terminate_processes
from sweep.windows_host import read_windows_host


class LocalMachine:
    def platform(self) -> Platform:
        return detect_platform()

    def read_processes(self) -> list[ProcessInfo]:
        return read_processes()

    def read_memory(self) -> MemoryStatus:
        return read_memory()

    def read_host(self) -> HostStatus | None:
        return read_windows_host() if detect_platform() is Platform.WSL else None

    def mount_namespace(self) -> str | None:
        return own_mount_namespace() if HAS_PROC else None

    def terminate(self, targets: Sequence[ProcessInfo]) -> list[int]:
        return terminate_processes(targets)
