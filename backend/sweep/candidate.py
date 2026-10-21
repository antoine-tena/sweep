"""Un groupe de process qui encombre, avec la raison qui le désigne et le degré de certitude."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Candidate:
    rule: str
    label: str
    reason: str
    pids: tuple[int, ...]
    rss_bytes: int
    # Sûr : une preuve dit qu'il ne peut plus servir, `--kill` l'arrête. Sinon « à vérifier » :
    # affiché, arrêté seulement si on le désigne (`--kill --pid`).
    is_certain: bool

    @property
    def main_pid(self) -> int:
        return self.pids[0]
