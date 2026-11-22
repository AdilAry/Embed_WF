# AGENTS.md — working on the Embed_WF repo itself

This repo is the **embedded kit**, not a project: an ESP32 project template,
embedded commands, a test bench and dev-box setup, built on the owner's
short-loop workflow (one task per session, files as memory).

The workflow is a **separate repository** and an external dependency. Its
location on a machine is `$WORKFLOW_DIR`, which the workflow's own installer
sets. This kit relies only on the contract in the workflow's WORKFLOW.md §8,
"Building a kit on this workflow" (the README names the contract date it was
written against): the commands `/start`, `/wrap`, `/judge`, the AGENTS.md
fields, the PROGRESS.md sections, `docs/history.md` and `docs/decisions.md`,
the plan, `WORKFLOW_DIR` and the install line. Nothing else from the workflow
is copied or restated here.

Real projects are created into `~/projects/<name>`, never inside this repo:
agents load `AGENTS.md` from every parent folder too.

Owner: embedded systems engineer (ESP32, KiCad), comfortable with C and Python.
Prefer simple, well-commented scripts over clever ones.

## Layout

- `prompts/` — embedded-only commands (`/define`, `/commission`, `/datasheet`,
  `/change-request`, `/new-project`). Same file format as the workflow's
  commands: frontmatter `description` + `argument-hint`, `$ARGUMENTS` in the
  body.
- `tools/install-workflow.sh` — installs the workflow's commands and these,
  through `"$WORKFLOW_DIR/install.sh"`. Stops if `WORKFLOW_DIR` isn't set.
- `tools/new_project.sh` — creates an embedded project from `template/`.
- `template/` — embedded starter project. Must always pass `make host-test`,
  `make compile` and `python3 tools/trace.py --strict` (the `template` GitHub
  workflow enforces this). Nothing in it may depend on a particular harness.
- `hardware/boards/*.md` — board references, shared across projects.
  `template/docs/hardware/` holds a **copy** that CI checks is identical; edit
  `hardware/boards/` and copy it over.
- `docs/` — human guide for the embedded layer (GUIDE, cheatsheet, testing,
  troubleshooting, REVIEW).
- `tests/` — pytest tests for `template/tools/*.py`. Run `python3 -m pytest -q tests`.
- `devbox/` — Debian 13 setup scripts (root part / user part). Must stay idempotent.
- `bench/` — dev-box test-bench commands, linked into `~/.local/bin`.

## Rules

- A change to how sessions work belongs in the workflow repository first.
  Never fix it only here, and never restate the loop or its stop rules here.
  If this kit needs a word the §8 list doesn't have, list it for the owner,
  who adds it there. Don't edit the workflow repository from here.
- The always-loaded files are a budget: `template/AGENTS.md` under ~120 lines,
  `template/PROGRESS.md` under ~60 (CI checks both). Point to detail, don't
  paste it. One fact, one place.
- Keep the pinned versions in `template/Makefile` the single source of truth
  (`devbox/setup-user.sh` reads them from there).
- When a project discovers something true for the whole board, it goes into
  `hardware/boards/…md` with **(unverified)** removed only once it has run on the
  owner's hardware.
- Shell scripts: `bash -n` clean, `set -euo pipefail`, no `sudo` inside user scripts.
- Python: standard library + pyserial/pytest/bleak only.
