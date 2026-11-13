# AGENTS.md — working on the Embed_WF repo itself

This repo is the **workflow kit**, not a project. It has two layers:

- `workflow/` — the owner's short-loop workflow for any software project (one
  task per session, files as memory). It is self-contained and is also shipped
  on its own as a zip, so **nothing in it may mention this kit, ESP32, `make`
  targets or the FSD**.
- everything else — the embedded layer built on it: ESP32 project template,
  embedded commands, test bench, dev-box setup.

Real projects are created into `~/projects/<name>`, never inside this repo:
agents load `AGENTS.md` from every parent folder too.

Owner: embedded systems engineer (ESP32, KiCad), comfortable with C and Python.
Prefer simple, well-commented scripts over clever ones.

## Layout

- `workflow/WORKFLOW.md` — the method, and what changed between versions and why.
- `workflow/templates/commands/` — `/start`, `/wrap`, `/judge`. They only use the
  words a project's AGENTS.md defines: Check, Done gate, Run limit, Push, and
  the optional "At /start also" / "At /wrap also" steps.
- `workflow/templates/user-level/AGENTS.md` — the owner's "How I work" file,
  installed as each harness's global instructions.
- `workflow/templates/project/` — starter for a non-embedded project. One
  template; whole sections marked `[IF ...]` are deleted when they don't apply.
- `workflow/install.sh`, `workflow/new-project.sh` — installer and generator
  for the generic layer. `tools/build-workflow-zip.sh` packs `workflow/`.
- `prompts/` — embedded-only commands (`/define`, `/commission`, `/datasheet`,
  `/change-request`, `/new-project`). Same file format as the generic ones:
  frontmatter `description` + `argument-hint`, `$ARGUMENTS` in the body, which
  both pi prompt templates and Claude Code commands accept.
- `tools/install-workflow.sh` — installs both command sets (links them).
- `template/` — embedded starter project. Must always pass `make host-test`,
  `make compile` and `python3 tools/trace.py --strict` (the `template` GitHub
  workflow enforces this). Nothing in it may depend on a particular harness.
- `hardware/boards/*.md` — board references, shared across projects.
  `template/docs/hardware/` holds a **copy** that CI checks is identical; edit
  `hardware/boards/` and copy it over.
- `docs/` — human guide for the embedded layer (GUIDE, cheatsheet, testing,
  troubleshooting, REVIEW).
- `tests/` — pytest tests for `template/tools/*.py`. Run `python3 -m pytest -q tests`.
- `devbox/` — Mint setup scripts (root part / user part). Must stay idempotent.
- `bench/` — dev-box test-bench commands, linked into `~/.local/bin`.

## Rules

- A change to how sessions work belongs in `workflow/` first, then in the
  embedded files that build on it. Never fix it only in the embedded layer.
- The always-loaded files are a budget: a project `AGENTS.md` under ~120 lines,
  `PROGRESS.md` under ~60, the user-level file ~50. Point to detail, don't
  paste it. One fact, one place.
- `workflow/templates/project/` uses the bracket markers from WORKFLOW.md §2
  and no other square brackets, so `grep '\['` finds what is unfilled.
- Keep the pinned versions in `template/Makefile` the single source of truth
  (`devbox/setup-user.sh` reads them from there).
- When a project discovers something true for the whole board, it goes into
  `hardware/boards/…md` with **(unverified)** removed only once it has run on the
  owner's hardware.
- Shell scripts: `bash -n` clean, `set -euo pipefail`, no `sudo` inside user scripts.
- Python: standard library + pyserial/pytest/bleak only.
