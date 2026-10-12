"""Windows vu depuis WSL : PowerShell par son chemin complet, `.wslconfig` sur le disque C."""

import configparser
import json
import subprocess
from pathlib import Path, PureWindowsPath

from sweep.host_status import HostStatus

POWERSHELL = Path("/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
POWERSHELL_TIMEOUT_SECONDS = 15
BYTES_PER_KIB = 1024
HOST_QUERY = (
    "$os = Get-CimInstance Win32_OperatingSystem; "
    "@{total_kib = $os.TotalVisibleMemorySize; free_kib = $os.FreePhysicalMemory; "
    "profile = $env:USERPROFILE} | ConvertTo-Json -Compress"
)
WSL_SECTION = "wsl2"
MEMORY_KEY = "memory"
WSLCONFIG_NAME = ".wslconfig"
MOUNT_ROOT = "/mnt"


def read_windows_host() -> HostStatus | None:
    """None si PowerShell est injoignable ou répond hors du format attendu."""
    if not POWERSHELL.exists():
        return None
    try:
        completed = subprocess.run(
            [str(POWERSHELL), "-NoProfile", "-NonInteractive", "-Command", HOST_QUERY],
            capture_output=True,
            text=True,
            timeout=POWERSHELL_TIMEOUT_SECONDS,
            check=True,
        )
    except OSError, subprocess.SubprocessError:
        return None
    return parse_host_answer(completed.stdout)


def parse_host_answer(raw_answer: str) -> HostStatus | None:
    """Valide la réponse de PowerShell ([VALIDATION-AUX-FRONTIERES]) avant tout usage."""
    try:
        answer = json.loads(raw_answer)
    except ValueError:
        return None
    if not isinstance(answer, dict):
        return None
    total_kib, free_kib, profile = (
        answer.get("total_kib"),
        answer.get("free_kib"),
        answer.get("profile"),
    )
    if (
        not isinstance(total_kib, int)
        or not isinstance(free_kib, int)
        or not isinstance(profile, str)
    ):
        return None
    wslconfig = Path(windows_to_wsl_path(profile)) / WSLCONFIG_NAME
    return HostStatus(
        total_bytes=total_kib * BYTES_PER_KIB,
        available_bytes=free_kib * BYTES_PER_KIB,
        wslconfig_path=str(wslconfig) if wslconfig.exists() else None,
        wsl_memory_limit=read_wsl_memory_limit(wslconfig),
    )


def windows_to_wsl_path(windows_path: str) -> str:
    """`C:\\Users\\antoine` → `/mnt/c/Users/antoine`."""
    pure = PureWindowsPath(windows_path)
    drive = pure.drive.rstrip(":").lower()
    return "/".join([MOUNT_ROOT, drive, *pure.parts[1:]])


def read_wsl_memory_limit(wslconfig: Path) -> str | None:
    parser = configparser.ConfigParser()
    try:
        parser.read_string(wslconfig.read_text(encoding="utf-8-sig"))
    except OSError, configparser.Error:
        return None
    return parser.get(WSL_SECTION, MEMORY_KEY, fallback=None)
