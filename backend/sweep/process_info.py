"""Photo d'un process, prise une fois : le reste du code ne parle jamais à psutil."""

import re
from dataclasses import dataclass, field
from datetime import datetime

PATH_SEPARATORS = re.compile(r"[/\\]")
PIPE_PREFIX = "pipe:"


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
    # Appartient à l'utilisateur qui lance sweep : les autres ne sont jamais candidats.
    is_own: bool = True
    # Terminal de contrôle (`/dev/pts/3`), None s'il n'en a pas ou plus.
    terminal: str | None = None
    # Linux seulement (None ailleurs) : cible de l'entrée standard (`pipe:[123]`, `/dev/null`),
    # canaux ouverts par le process, espace de montage (un conteneur a le sien).
    stdin_target: str | None = None
    open_pipes: frozenset[str] = field(default_factory=frozenset)
    mount_namespace: str | None = None

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

    @property
    def stdin_pipe(self) -> str | None:
        """Le canal d'où il lit ses ordres, s'il en lit un (cas d'un serveur MCP stdio)."""
        target = self.stdin_target
        return target if target is not None and target.startswith(PIPE_PREFIX) else None
