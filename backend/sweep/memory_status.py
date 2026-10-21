"""État de la mémoire vive et du swap, en octets."""

from dataclasses import dataclass

PERCENT = 100


@dataclass(frozen=True)
class MemoryStatus:
    total_bytes: int
    available_bytes: int
    swap_total_bytes: int
    swap_used_bytes: int

    @property
    def swap_percent(self) -> float:
        if not self.swap_total_bytes:
            return 0.0
        return PERCENT * self.swap_used_bytes / self.swap_total_bytes

    @property
    def used_percent(self) -> float:
        if not self.total_bytes:
            return 0.0
        return PERCENT * (self.total_bytes - self.available_bytes) / self.total_bytes
