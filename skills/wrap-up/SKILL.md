---
name: wrap-up
description: End-of-session housekeeping - bring README, FSD status, PLAN and NOTES up to date with what was actually done, run make check, commit and push. Use when the owner says wrap up, update documentation and push, or is about to stop working.
disable-model-invocation: true
---

# /wrap-up — leave the project ready for next time

1. `git status` / `git log --oneline -10` to see what changed this session.
2. Update, only where something actually changed:
   - `docs/PLAN.md` — tick finished items, add discovered follow-ups.
   - `docs/FSD.md` — Status field; open questions answered/added. (Don't change requirements here;
     that is `/change-request`.)
   - `docs/NOTES.md` — dated entry: what was done, what was learned, what's next, known issues.
   - `README.md` — "What it does" in 2–5 lines for a human visitor; build instructions if they changed.
3. Board-wide lessons (a pin quirk, a library bug, a proven init sequence): show the owner the text
   and suggest adding it to `~/Embed_WF/hardware/boards/guition-jc4827w543.md` (and committing there).
4. `make check` must be green. If it isn't, say so and don't push.
5. Commit `"Docs: session wrap-up"` and `git push`. Then `gh run list -L 1` to show CI status.
6. Give the owner a 5-line summary: done, test counts, CI status, next step, anything needing their hands.
