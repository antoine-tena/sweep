"""Photo d'un process, prise une fois : le reste du code ne parle jamais à psutil."""

import re
from dataclasses import dataclass
from datetime import datetime

PATH_SEPARATORS = re.compile(r"[/\\]")


@dataclass(frozen=True)
class ProcessInfo:
    pid: int
    ppid: int
    name: str
    cmdline: tuple[str, ...]
    rss_bytes: int
    started_at: datetime
    cpu_percent: float
    cwd: str | None

    @property
    def program(self) -> str:
        """Programme sans chemin ni `.exe` : `claude`, `agy`, `node`, `npm`.

        Lu dans la ligne de commande d'abord : le nom système peut être celui d'un fil
        (`MainThread` pour node) ou un titre réécrit (`npm exec @toolb…`).
        """
        source = self.cmdline[0] if self.cmdline else self.name
        first_word = source.split(maxsplit=1)[0] if source.strip() else ""
        return PATH_SEPARATORS.split(first_word)[-1].removesuffix(".exe").lower()

    @property
    def command_text(self) -> str:
        return " ".join(self.cmdline) or self.name
