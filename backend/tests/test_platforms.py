from pathlib import Path

import pytest

from sweep import platforms, windows_host
from sweep.platforms import Platform, detect_platform

WSL_KERNEL = "Linux version 6.18.33.2-microsoft-standard-WSL2 (root@1d2f) gcc 13\n"
LINUX_KERNEL = "Linux version 6.8.0-45-generic (buildd@lcy02) gcc 13\n"


@pytest.mark.parametrize(
    ("system_platform", "platform"), [("win32", Platform.WINDOWS), ("darwin", Platform.MACOS)]
)
def test_windows_and_macos_are_detected_without_reading_proc(
    monkeypatch: pytest.MonkeyPatch, system_platform: str, platform: Platform
) -> None:
    monkeypatch.setattr("sys.platform", system_platform)
    monkeypatch.setattr(platforms, "PROC_VERSION", Path("/n'existe/pas"))

    assert detect_platform() is platform


@pytest.mark.parametrize(
    ("kernel", "platform"), [(WSL_KERNEL, Platform.WSL), (LINUX_KERNEL, Platform.LINUX)]
)
def test_wsl_is_told_apart_from_linux_by_its_kernel(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, kernel: str, platform: Platform
) -> None:
    proc_version = tmp_path / "version"
    proc_version.write_text(kernel)
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr(platforms, "PROC_VERSION", proc_version)

    assert detect_platform() is platform


def test_unreadable_proc_means_plain_linux(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.platform", "linux")
    monkeypatch.setattr(platforms, "PROC_VERSION", Path("/n'existe/pas"))

    assert detect_platform() is Platform.LINUX


def test_windows_host_is_skipped_without_powershell(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(windows_host, "POWERSHELL", Path("/n'existe/pas/powershell.exe"))

    assert windows_host.read_windows_host() is None
