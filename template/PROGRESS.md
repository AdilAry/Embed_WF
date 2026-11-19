# PROGRESS: [project name]
Updated: [date and time]. Current state only, under ~60 lines. Finished work is in docs/history.md.

## Now
- **Task:** none yet. The project was just created from the Embed_WF template.
- **State:** template firmware (display, touch detection, serial console, self test), not yet run on a board in this project.

## Next
1. Write the idea in `docs/IDEA.md`, then `/define` (it writes `docs/FSD.md` and `docs/PLAN.md`).
2. `/commission` with a board on USB (Phase 0 of `docs/PLAN.md`).
3. `/start` on the first item of Phase 1.

## Broken
- nothing known.

## Waiting on me
- The idea in `docs/IDEA.md`.

## Done
- nothing yet.

## How to run
```
make check                 # host tests + compile, no board needed
make loop BOARD=R          # ... + flash, boot check and on-board tests
make trace                 # which requirement is proven by what
```
