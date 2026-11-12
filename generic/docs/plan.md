# Plan: [project name]

Read only the section of the current task. One section = one session; if a section turns out bigger, split it (M2a, M2b) rather than stretching the session. Every section says how its result is proven, so `/start` can quote it and `/wrap` can run it.

## M0 Skeleton
- Repo structure, dependency file, `.gitignore`, PROGRESS.md from its template, LICENSE ([MIT | the client's or employer's terms | none, private repo]).
- The smallest thing that runs end to end and shows one real result: [e.g. a page showing one number from the data | firmware printing one sensor reading | a scene where the player moves].
- **Done when:** `[the Check command]` passes and [what I see when I run it].

## M1 [Foundation: what everything else depends on]
- [e.g. load and clean the data, plus its rules | drivers behind a hardware abstraction layer | core game loop and state].
- Tests on known cases, including the edge cases: [the ones you already know].
- **Done when:** `[command, e.g. pytest tests/test_load.py]` passes.

## M2 [Core feature]
- [The core feature from the MVP].
- **Done when:** `[command]` passes; by hand I check [what only a person can judge | nothing].

## [Further sections as needed, same shape]

## Review (fresh session)
Run `/judge`. It reports issues ranked by value per hour; I pick which ones get fixed, and each fix is its own `/start`.
