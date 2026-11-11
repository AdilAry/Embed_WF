# AGENTS.md — working on the Embed_WF repo itself

This repo is the **workflow kit**, not a firmware project. Real projects are
created from `template/` into `~/projects/<name>` by `tools/new_project.sh`.

The agent harness is **pi** (pi.dev). Nothing in `template/` may depend on a
particular harness: the loop is plain `make` targets and Python tools. Only
`prompts/`, the `AGENTS.md` files and `devbox/setup-user.sh` know about pi.

Owner: beginner embedded engineer. Explain jargon briefly. Prefer simple,
well-commented scripts over clever ones.

## Layout

- `docs/` — human guide (GUIDE, cheatsheet, testing, troubleshooting, planning-chat)
- `hardware/boards/*.md` — board references, the shared knowledge across projects.
  `template/docs/hardware/` holds a **copy** that CI checks is identical; edit
  `hardware/boards/` and copy it over.
- `template/` — starter project. Must always pass `make host-test`, `make compile` and
  `python3 tools/trace.py --strict` (the `template` GitHub workflow enforces this).
- `tests/` — pytest tests for `template/tools/*.py`. Run `python3 -m pytest -q tests`.
- `prompts/<name>.md` — pi prompt templates, one per workflow step (`/define`,
  `/commission`, `/build-loop`, ...). `devbox/setup-user.sh` copies them into
  `~/.pi/agent/prompts/`; re-run it after editing one.
- `devbox/` — Mint setup scripts (root part / user part). Must stay idempotent.
- `bench/` — dev-box test-bench commands, linked into `~/.local/bin`.

## Rules

- Keep the pinned versions in `template/Makefile` the single source of truth
  (`devbox/setup-user.sh` reads them from there).
- When a project discovers something true for the whole board, it goes into
  `hardware/boards/…md` with **(unverified)** removed only once it has run on the
  owner's hardware.
- Shell scripts: `bash -n` clean, `set -euo pipefail`, no `sudo` inside user scripts.
- Python: standard library + pyserial/pytest/bleak only.
- Prompt templates use only what pi documents: `description` and `argument-hint`
  in the frontmatter, `$ARGUMENTS` / `$1` in the body.
