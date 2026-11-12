# AGENTS.md — working on the Embed_WF repo itself

This repo is the **workflow kit**, not a project. It holds the owner's short-loop
workflow (one task per session, files as memory; `docs/SHORT-LOOP.md`) and its
embedded profile. Real projects are created from `template/` (ESP32) or
`generic/` (anything else) into `~/projects/<name>` by `tools/new_project.sh`.

Owner: embedded systems engineer (ESP32, KiCad), comfortable with C and Python.
Prefer simple, well-commented scripts over clever ones.

## Layout

- `prompts/<name>.md` — the slash commands. One source for every agent harness:
  the format (frontmatter `description` + `argument-hint`, `$ARGUMENTS` in the
  body) is what both pi prompt templates and Claude Code commands accept.
  `/start`, `/wrap`, `/judge` are generic and must stay free of embedded terms:
  they only use the words a project's AGENTS.md defines (Check, Done gate, Mode,
  Push). The others are embedded-only.
- `user-level/AGENTS.md` — the owner's "How I work" file, installed as each
  harness's global instructions.
- `tools/install-workflow.sh` — copies the two things above to pi and Claude Code.
- `template/` — embedded starter project. Must always pass `make host-test`,
  `make compile` and `python3 tools/trace.py --strict` (the `template` GitHub
  workflow enforces this). Nothing in it may depend on a particular harness.
- `generic/` — small starter for non-embedded projects; `profiles/` — optional
  blocks (competition, data) pasted into a project that needs them.
- `hardware/boards/*.md` — board references, shared across projects.
  `template/docs/hardware/` holds a **copy** that CI checks is identical; edit
  `hardware/boards/` and copy it over.
- `docs/` — human guide (GUIDE, SHORT-LOOP, cheatsheet, testing, troubleshooting).
- `tests/` — pytest tests for `template/tools/*.py`. Run `python3 -m pytest -q tests`.
- `devbox/` — Mint setup scripts (root part / user part). Must stay idempotent.
- `bench/` — dev-box test-bench commands, linked into `~/.local/bin`.

## Rules

- The always-loaded files are a budget: project `AGENTS.md` under ~120 lines
  (generic: ~80), `PROGRESS.md` under ~60, the user-level file ~50. Point to
  detail, don't paste it. One fact, one place.
- `generic/` files use the bracket markers from SHORT-LOOP.md §5 and no other
  square brackets, so `grep '\['` finds what is unfilled.
- Keep the pinned versions in `template/Makefile` the single source of truth
  (`devbox/setup-user.sh` reads them from there).
- When a project discovers something true for the whole board, it goes into
  `hardware/boards/…md` with **(unverified)** removed only once it has run on the
  owner's hardware.
- Shell scripts: `bash -n` clean, `set -euo pipefail`, no `sudo` inside user scripts.
- Python: standard library + pyserial/pytest/bleak only.
