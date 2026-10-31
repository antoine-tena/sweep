# Sweep

Finds what clogs RAM and swap (forgotten agents, orphan servers), proposes what to kill, on Linux, WSL, macOS, Windows.

## Repo map

- `backend/sweep/`: `cli.py`, `__main__.py`, business logic; `system.py`, `linux_proc.py`, `windows_host.py` (machine reads); `terminate.py` (kills).
- `backend/sweep/rules/`: detection rules (agents, MCP, dev servers), one per module; `patterns.py`.
- `backend/tests/`: simulated processes (`factories.py`).
- `docs/backlog/`; `charter.toml`; `.claude/rules/kiln/`.
