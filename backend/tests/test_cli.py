import io
import json
from datetime import timedelta

import pytest

from sweep.cli import EXIT_FAILURE, EXIT_OK, main
from tests.factories import INIT_PID, NOW, TERMINAL, FakeMachine, make_process

ORPHAN_PID = 10
IDLE_PID = 20


def _machine() -> FakeMachine:
    """Un agent orphelin (sûr) et un agent inactif dans son terminal (à vérifier)."""
    return FakeMachine(
        [
            make_process(ORPHAN_PID, "agy", ppid=INIT_PID, age=timedelta(hours=9), rss_mib=300),
            make_process(IDLE_PID, "claude", age=timedelta(hours=5), terminal=TERMINAL),
        ]
    )


def _run(
    arguments: list[str], machine: FakeMachine, answer: str = "", expected: int = EXIT_OK
) -> str:
    out = io.StringIO()
    exit_code = main(arguments, out, machine, ask=lambda _prompt: answer, clock=lambda: NOW)
    assert exit_code == expected
    return out.getvalue()


def test_default_run_only_reports_both_tiers() -> None:
    machine = _machine()

    report = _run([], machine)

    assert report.index("Sûrs") < report.index("agy sans terminal") < report.index("À vérifier")
    assert "claude lancé il y a 5 h" in report
    assert machine.terminated == []


@pytest.mark.parametrize(
    ("arguments", "answer"), [(["--kill"], "n"), (["--kill"], ""), (["--kill", "--dry-run"], "o")]
)
def test_kill_needs_a_real_yes(arguments: list[str], answer: str) -> None:
    machine = _machine()

    _run(arguments, machine, answer)

    assert machine.terminated == []


@pytest.mark.parametrize(("arguments", "answer"), [(["--kill"], "oui"), (["--kill", "--yes"], "")])
def test_kill_stops_only_the_certain(arguments: list[str], answer: str) -> None:
    machine = _machine()

    report = _run(arguments, machine, answer)

    assert machine.terminated == [ORPHAN_PID]
    assert "Arrêtés : environ 300 Mo libérés." in report


def test_pid_stops_a_candidate_to_check_when_named() -> None:
    machine = _machine()

    _run(["--kill", "--pid", str(IDLE_PID), "--yes"], machine)

    assert machine.terminated == [IDLE_PID]


@pytest.mark.parametrize("pid", ["1", "12345"])
def test_pid_outside_the_candidates_kills_nothing(pid: str) -> None:
    machine = _machine()

    report = _run(["--kill", "--pid", pid, "--yes"], machine, expected=EXIT_FAILURE)

    assert "Pas un candidat" in report
    assert machine.terminated == []


def test_pid_without_kill_is_refused() -> None:
    with pytest.raises(SystemExit):
        main(["--pid", str(IDLE_PID)], io.StringIO(), _machine())


def test_json_report_is_stable_and_kills_nothing() -> None:
    machine = _machine()

    document = json.loads(_run(["--json", "--kill", "--yes"], machine))

    tiers = [(candidate["pids"], candidate["is_certain"]) for candidate in document["candidates"]]
    assert tiers == [([ORPHAN_PID], True), ([IDLE_PID], False)]
    assert machine.terminated == []


def test_idle_hours_lowers_the_threshold() -> None:
    machine = FakeMachine([make_process(10, "claude", age=timedelta(hours=1), terminal=TERMINAL)])

    assert "Rien à tuer" in _run([], machine)
    assert "claude lancé il y a 1 h" in _run(["--idle-hours", "0.5"], machine)


@pytest.mark.parametrize("raw_hours", ["0", "-2", "trois"])
def test_idle_hours_must_be_positive(raw_hours: str) -> None:
    with pytest.raises(SystemExit):
        main(["--idle-hours", raw_hours], io.StringIO(), FakeMachine([]))


def test_version_exits_cleanly(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])

    assert exit_info.value.code == EXIT_OK
    assert capsys.readouterr().out.startswith("sweep ")
