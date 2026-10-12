"""Conseils sur la mémoire du poste, calculés sans toucher à la machine."""

from sweep.host_status import HostStatus
from sweep.memory_status import MemoryStatus
from sweep.platforms import Platform
from sweep.sizes import BYTES_PER_GIB, format_size

SWAP_ALERT_PERCENT = 80
RAM_ALERT_PERCENT = 90
# Ce que Windows garde pour lui (navigateur, éditeur) quand on agrandit WSL.
WINDOWS_RESERVE_GIB = 8


def build_advice(memory: MemoryStatus, platform: Platform, host: HostStatus | None) -> list[str]:
    advice = []
    if memory.swap_percent >= SWAP_ALERT_PERCENT:
        advice.append(
            f"Swap plein à {memory.swap_percent:.0f} % : le système écrit la mémoire sur le "
            "disque, tout ralentit. Libérer de la RAM, puis `sudo swapoff -a && sudo swapon -a` "
            "pour le vider."
        )
    if memory.used_percent >= RAM_ALERT_PERCENT:
        advice.append(f"RAM occupée à {memory.used_percent:.0f} %.")
    if platform is Platform.WSL and host is not None:
        advice += _wsl_advice(memory, host)
    return advice


def _wsl_advice(memory: MemoryStatus, host: HostStatus) -> list[str]:
    if host.wsl_memory_limit is not None:
        return []
    suggested_gib = max(
        host.total_bytes // BYTES_PER_GIB - WINDOWS_RESERVE_GIB,
        memory.total_bytes // BYTES_PER_GIB,
    )
    if suggested_gib * BYTES_PER_GIB <= memory.total_bytes:
        return []
    return [
        f"WSL n'a que {format_size(memory.total_bytes)} sur les {format_size(host.total_bytes)} "
        "de Windows (la moitié, par défaut). Dans `.wslconfig` du profil Windows : "
        f"`[wsl2]` puis `memory={suggested_gib}GB`, et `wsl --shutdown` depuis Windows."
    ]
