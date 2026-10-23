---
paths:
  - "**/*.py"
---
<!-- Written by kiln and kept current by `kiln update`: do not edit, it would be overwritten. -->
# Python

- **[MODERN-PYTHON]** Python 3.12+ syntax: PEP 695 generics (`def first[T](items: list[T]) -> T`,
  `type Alias = …`), `X | None` rather than `Optional[X]`, `@override` on every override, `match`
  to branch on a status, `Self` for chained returns.
- **[TYPING]** Annotations on every signature (parameters and return). `Any` only at an untyped
  edge (raw payload of a third-party API, `**kwargs` of a framework override); elsewhere a
  `TypedDict`, a `Protocol`, a union or a generic.
- **[STRICT-TYPING]** mypy `strict` on every module; no `# type: ignore` without a precise error
  code and a reason.
- Tooling: ruff (lint and format) and mypy run through `uv run` in the project's directory; the
  edit hook runs ruff on each file Claude writes, `kiln check` runs everything.
