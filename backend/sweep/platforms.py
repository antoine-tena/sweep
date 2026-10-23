"""Plateforme du poste : une détection unique ([MULTI-PLATFORM])."""

import sys
from enum import StrEnum
from pathlib import Path

PROC_VERSION = Path("/proc/version")
WSL_MARKER = "microsoft"


class Platform(StrEnum):
    LINUX = "linux"
    WSL = "wsl"
    MACOS = "macos"
    WINDOWS = "windows"


def detect_platform() -> Platform:
    if sys.platform == "win32":
        return Platform.WINDOWS
    if sys.platform == "darwin":
        return Platform.MACOS
    try:
        kernel_version = PROC_VERSION.read_text().lower()
    except OSError:
        return Platform.LINUX
    return Platform.WSL if WSL_MARKER in kernel_version else Platform.LINUX
