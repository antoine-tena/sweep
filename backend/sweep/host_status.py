"""Mémoire de Windows vue depuis WSL, et la limite que `.wslconfig` donne à WSL."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HostStatus:
    total_bytes: int
    available_bytes: int
    wslconfig_path: str | None
    # Valeur brute de `memory=` dans la section [wsl2] (`14GB`), None si absente.
    wsl_memory_limit: str | None
