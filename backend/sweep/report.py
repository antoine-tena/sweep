"""Rendu d'un passage : texte pour un humain, JSON stable pour un script ([SORTIE-MACHINE])."""

import json

from sweep.candidate import Candidate
from sweep.memory_status import MemoryStatus
from sweep.scan_result import ScanResult
from sweep.sizes import format_size

LABEL_WIDTH = 70
JSON_INDENT = 2
NOTHING_FOUND = "Rien à tuer : aucun reste détecté."
CERTAIN_TITLE = "Sûrs, arrêtés par `sweep --kill` :"
UNCERTAIN_TITLE = (
    "À vérifier, peut-être encore utilisés (arrêter un seul : `sweep --kill --pid N`) :"
)


def render_text(result: ScanResult) -> str:
    lines = [_memory_line(result.memory)]
    if result.host is not None:
        lines.append(
            f"Windows : {format_size(result.host.available_bytes)} libres sur "
            f"{format_size(result.host.total_bytes)}"
        )
    if not result.candidates:
        lines += ["", NOTHING_FOUND]
    if result.certain:
        lines += ["", CERTAIN_TITLE, *_candidate_lines(result.certain)]
        lines.append(f"  Total récupérable : environ {format_size(result.reclaimable_bytes)}.")
    if result.uncertain:
        lines += ["", UNCERTAIN_TITLE, *_candidate_lines(result.uncertain)]
    lines += ["", "Plus gros process :"]
    lines += [
        f"  {format_size(process.rss_bytes):>8}  pid {process.pid:<8} "
        f"{_shorten(process.command_text)}"
        for process in result.heaviest
    ]
    if result.advice:
        lines += ["", "Conseils :", *(f"  - {advice}" for advice in result.advice)]
    return "\n".join(lines) + "\n"


def render_json(result: ScanResult) -> str:
    document = {
        "platform": str(result.platform),
        "memory": vars(result.memory),
        "host": vars(result.host) if result.host is not None else None,
        "candidates": [vars(candidate) for candidate in result.candidates],
        "reclaimable_bytes": result.reclaimable_bytes,
        "advice": list(result.advice),
    }
    return json.dumps(document, ensure_ascii=False, indent=JSON_INDENT) + "\n"


def _candidate_lines(candidates: tuple[Candidate, ...]) -> list[str]:
    lines = []
    for candidate in candidates:
        lines.append(
            f"  {format_size(candidate.rss_bytes):>8}  pid {candidate.main_pid:<8} "
            f"{candidate.reason}"
        )
        lines.append(f"            {_shorten(candidate.label)}")
    return lines


def _memory_line(memory: MemoryStatus) -> str:
    return (
        f"RAM : {format_size(memory.available_bytes)} libres sur "
        f"{format_size(memory.total_bytes)} · swap : {format_size(memory.swap_used_bytes)} "
        f"sur {format_size(memory.swap_total_bytes)} ({memory.swap_percent:.0f} %)"
    )


def _shorten(text: str) -> str:
    return text if len(text) <= LABEL_WIDTH else text[: LABEL_WIDTH - 1] + "…"
