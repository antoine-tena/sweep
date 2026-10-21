import json
from pathlib import Path

import pytest

from sweep.windows_host import parse_host_answer, read_wsl_memory_limit, windows_to_wsl_path


def test_windows_path_becomes_a_wsl_mount_path() -> None:
    assert windows_to_wsl_path(r"C:\Users\antoine") == "/mnt/c/Users/antoine"


@pytest.mark.parametrize("raw_answer", ["", "not json", "[]", '{"total_kib": "12"}'])
def test_unexpected_powershell_answers_are_rejected(raw_answer: str) -> None:
    assert parse_host_answer(raw_answer) is None


def test_valid_answer_gives_host_memory() -> None:
    answer = json.dumps({"total_kib": 22_000_000, "free_kib": 6_000_000, "profile": r"Z:\none"})

    host = parse_host_answer(answer)

    assert host is not None
    assert (host.total_bytes, host.wsl_memory_limit) == (22_000_000 * 1024, None)


def test_memory_limit_is_read_from_wslconfig(tmp_path: Path) -> None:
    wslconfig = tmp_path / ".wslconfig"
    wslconfig.write_text("[wsl2]\nmemory=14GB\nswap=8GB\n", encoding="utf-8-sig")

    assert read_wsl_memory_limit(wslconfig) == "14GB"
    assert read_wsl_memory_limit(tmp_path / "absent") is None
