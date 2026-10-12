import io
import json
from datetime import timedelta

import pytest

from sweep.cli import EXIT_OK, main
from tests.factories import NOW, FakeMachine, make_process


def _machine_with_leftover() -> FakeMachine:
    return FakeMachine([make_process(10, "agy", age=timedelta(hours=9), rss_mib=300)])


def _run(arguments: list[str], machine: FakeMachine, answer: str = "") -> str:
    out = io.StringIO()
    exit_code = main(arguments, out, machine, ask=lambda _prompt: answer, clock=lambda: NOW)
    assert exit_code == EXIT_OK
    return out.getvalue()


def test_default_run_only_reports() -> None:
    machine = _machine_with_leftover()

    report = _run([], machine)

    assert "agy lancé il y a 9 h" in report
    assert machine.terminated == []


@pytest.mark.parametrize(
    ("arguments", "answer"), [(["--kill"], "n"), (["--kill", "--dry-run"], "o")]
)
def test_kill_needs_a_real_yes(arguments: list[str], answer: str) -> None:
    machine = _machine_with_leftover()

    _run(arguments, machine, answer)

    assert machine.terminated == []


@pytest.mark.parametrize(("arguments", "answer"), [(["--kill"], "oui"), (["--kill", "--yes"], "")])
def test_confirmed_kill_stops_the_candidates(arguments: list[str], answer: str) -> None:
    machine = _machine_with_leftover()

    report = _run(arguments, machine, answer)

    assert machine.terminated == [10]
    assert "Arrêtés : environ 300 Mo libérés." in report


def test_json_report_is_stable_and_kills_nothing() -> None:
    machine = _machine_with_leftover()

    document = json.loads(_run(["--json", "--kill", "--yes"], machine))

    assert [candidate["pids"] for candidate in document["candidates"]] == [[10]]
    assert machine.terminated == []


def test_version_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == EXIT_OK
    assert capsys.readouterr().out.startswith("sweep ")


def test_idle_hours_lowers_the_threshold() -> None:
    machine = FakeMachine([make_process(10, "claude", age=timedelta(hours=1), rss_mib=50)])

    assert "Rien à tuer" in _run([], machine)
    assert "claude lancé il y a 1 h" in _run(["--idle-hours", "0.5"], machine)


@pytest.mark.parametrize("raw_hours", ["0", "-2", "trois"])
def test_idle_hours_must_be_positive(raw_hours: str) -> None:
    with pytest.raises(SystemExit):
        main(["--idle-hours", raw_hours], io.StringIO(), FakeMachine([]))
