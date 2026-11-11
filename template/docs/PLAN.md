# Implementation plan

> Created by the agent from `docs/FSD.md` (ask: "plan the implementation in phases").
> Each phase ends with all its tests green and a commit. Keep phases small enough
> to finish in one session.

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
