# Implementation plan

> Created by `/define` from `docs/FSD.md`.
> **One item = one session** (`/start` … `/wrap`): a requirement or two with their tests,
> ending with `make trace RUN=1 REQS="…"` green. Split anything bigger.

## Phase 0 — Commissioning (done once per project)

- [ ] `make host-test` green
- [ ] `make compile` green
- [ ] Both boards registered (`make boards` shows `board=R` and `board=C`)
- [ ] Board flashed, `make boot-check` green
- [ ] `make open-check` prints `OPENCHECK:OK`
- [ ] `make target-test BOARD=R` green
- [ ] `make target-test BOARD=C` green
- [ ] `make bench-test` green
- [ ] `make trace RUN=1` prints `TRACE:OK`
- [ ] CI green on GitHub

## Phase 1 — …

- [ ] REQ-… …

## Phase 2 — …

- [ ] …
