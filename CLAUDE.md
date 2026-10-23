# Sweep

Trouve ce qui encombre la RAM et le swap (agents oubliés, serveurs orphelins) et propose quoi tuer, sous Linux, WSL, macOS et Windows.

<!-- This file belongs to the project: kiln wrote it once and never changes it. kiln's rules live
in .claude/rules/kiln/ and are kept current by `kiln update`. Write here what Claude cannot
guess about this project, and keep it under 200 lines: every session reads it. -->

## Repo map

Where to look, so as not to explore: read it before opening files, and update it in the commit
that adds, moves or removes a directory, a domain or an entry point. One line per place, what
it holds; no copy of the code.

- `backend/sweep/`: commands (`cli.py`, entry point `__main__.py`) and
  business logic; `backend/tests/`: tests.
- `docs/backlog/`: the work to do; `charter.toml`: the checked rules; `.claude/rules/kiln/`:
  kiln's rules for Claude.

## Notes

<!-- Decisions, conventions and pitfalls of this project that Claude cannot guess from the code:
"we never call X directly, always through Y", "the staging database is reset every night"… -->

## Carried over from the instructions of kiln 0.3

### From `CLAUDE.md`

#### Carte du repo

  logique métier ; `system.py`, `linux_proc.py`, `windows_host.py` : lecture de la machine ;
  `terminate.py` : arrêt des process.
- `backend/sweep/rules/` : règles de détection (agents, MCP, serveurs de dev), une par
  module ; `patterns.py` : ce qui reconnaît chaque sorte de process.
- `backend/tests/` : tests, sur des process simulés (`factories.py`).
