---
description: Handle a change or new feature for an existing project - update the FSD first (new/changed REQ IDs, version bump, change log), add plan items and tests, then hand over to /start in a fresh session. Use when the owner wants to change behaviour, add a feature, or fix a spec-level problem.
argument-hint: <what should change>
---

# /change-request — spec first, then code

Requested change: $ARGUMENTS

1. Read `docs/FSD.md` and find every requirement the change touches. If the request is vague,
   ask up to 3 short clarifying questions (one at a time, with a recommended option).
2. Propose the FSD diff to the owner in plain words: requirements added / changed / removed (with
   IDs), new tests and their tier, anything that becomes out of scope. Wait for OK.
3. Apply it: edit `docs/FSD.md`, bump the minor version, add a change-log row (date, summary,
   REQ IDs). Never reuse a removed REQ ID.
4. Add a new phase (or items) to `docs/PLAN.md` referencing the REQ IDs.
5. `make trace`: the new/changed requirements show `NO TEST` or `NOT RUN`; nothing else should
   change status.
6. Stop here. Tell the owner to type `/wrap` (it puts the first new plan item under "Next" in
   `PROGRESS.md`); the implementation is a fresh session: `/start <that item>`.
