---
name: build-loop
description: Implement the next phase of docs/PLAN.md in a closed loop - write tests, implement, host-test, compile, flash, boot-check, run target and bench tests, diagnose failures, fix, repeat until green, then commit. Use when the owner says build, implement, continue, or next phase.
argument-hint: "[phase number or REQ IDs - default: next unchecked phase]"
---

# /build-loop — spec → firmware, closed loop

Target: $ARGUMENTS (if empty: the first phase in `docs/PLAN.md` with unchecked items).

Follow "The development loop" in `CLAUDE.md` exactly. Summary:

```
for each plan item in the phase:
    read the REQs it covers in docs/FSD.md
    write the test(s) first at the tier the FSD names
    implement (pure logic -> firmware/src/logic, hardware -> src/hal, glue -> src/app)
    make host-test   -> fix until green (never compile while red)
    make compile     -> fix errors and new warnings
    make upload && make boot-check && make target-test      (board connected)
    make bench-test  (only for bench-tier REQs)
    on failure: read the output + build/serial.log, form ONE hypothesis,
                add targeted Serial.printf("[subsystem] ...") if unsure, fix, rerun
    tick the item in docs/PLAN.md, git commit -m "REQ-xxx: <what>"
```

## Guard rails

- **Budget**: if the same test still fails after 3 genuinely different fixes, stop. Summarise what
  you tried, what the logs show, and your best hypothesis; ask the owner.
- **Physical actions** (swap board, press a button, wire something, walk to a sensor): stop and ask,
  saying precisely what to do and why.
- **Never** delete, skip or loosen a test to get green. If you believe the test or the FSD is wrong,
  explain and ask.
- **FSD drift**: if implementation reveals a gap or contradiction in the FSD, stop and propose the
  FSD change (or suggest `/change-request`). Don't silently decide.
- Prefer small commits. Each commit must leave `make check` green.
- Keep `docs/NOTES.md` updated with anything a future session would need (pin conflicts, library
  bugs, timing quirks). Board-wide findings: suggest adding them to the board reference.
- Usage limits are real on the Pro plan: don't re-read big files unnecessarily, use
  `datasheets/*.summary.md` before full datasheet text, and keep serial captures short (`SECS=`).

## When the phase is green

Print a short report: items done (REQ IDs), tests added per tier, total pass counts from the last
run, binary size, anything the owner should test by hand (manual/field REQs), and the next phase.
Ask whether to push to GitHub.
