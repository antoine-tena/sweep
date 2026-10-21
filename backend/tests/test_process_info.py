import pytest

from sweep.rules.agents import is_agent
from tests.factories import make_process


@pytest.mark.parametrize(
    ("command", "name", "program"),
    [
        ("/usr/bin/node /path/server.js", "MainThread", "node"),
        ("npm exec @toolbox-sdk/server@1.13.1", "npm exec @toolb", "npm"),
        (r"C:\Users\me\claude.exe --resume", "claude.exe", "claude"),
        ("agy --conversation abc", "agy", "agy"),
    ],
)
def test_program_comes_from_command_line(command: str, name: str, program: str) -> None:
    assert make_process(10, command, name=name).program == program


def test_windows_agent_is_recognised_from_its_exe_path() -> None:
    agent = make_process(10, r"C:\Users\me\AppData\Local\agy\agy.exe --conversation abc")

    assert is_agent(agent)
