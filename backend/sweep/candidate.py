"""Un groupe de process qu'il serait sûr de tuer, avec la raison qui le désigne."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    rule: str
    label: str
    reason: str
    pids: tuple[int, ...]
    rss_bytes: int

    @property
    def main_pid(self) -> int:
        return self.pids[0]
