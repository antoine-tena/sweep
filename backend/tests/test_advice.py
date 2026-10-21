from sweep.advice import build_advice
from sweep.host_status import HostStatus
from sweep.platforms import Platform
from tests.factories import GIB, make_memory

WINDOWS_22_GIB = HostStatus(22 * GIB, 6 * GIB, wslconfig_path=None, wsl_memory_limit=None)


def test_full_swap_is_reported() -> None:
    advice = build_advice(make_memory(swap_used_gib=3), Platform.LINUX, None)

    assert len(advice) == 1
    assert "Swap plein à 100 %" in advice[0]


def test_wsl_without_limit_gets_a_suggested_memory() -> None:
    advice = build_advice(make_memory(), Platform.WSL, WINDOWS_22_GIB)

    assert any("memory=14GB" in line for line in advice)


def test_wsl_with_a_limit_gets_no_memory_advice() -> None:
    host = HostStatus(22 * GIB, 6 * GIB, wslconfig_path="/mnt/c/x", wsl_memory_limit="14GB")

    assert build_advice(make_memory(), Platform.WSL, host) == []
