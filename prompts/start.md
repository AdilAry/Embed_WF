---
description: Start a short session on one task - a plan item, a requirement ID, or free text
argument-hint: task, e.g. "M2", "REQ-020" or "fix the export" (empty = Next in PROGRESS.md)
---
Task for this session: $ARGUMENTS

The project's AGENTS.md defines the words **Check**, **Done gate**, **Mode** and **Push** used below.

1. Run `git pull` (skip it if the repo has no remote). Read PROGRESS.md. If no task was given,
   take item 1 under "Next".
2. Read only what this task needs: its own section or rows of the plan and spec (AGENTS.md
   "Read only when needed" says where they are). Not the whole file, not the whole codebase.
3. If PROGRESS.md and the code disagree, tell me before anything else.
4. Reply with a plan of at most 5 bullets:
   - the steps, smallest first, tests before the code they prove;
   - the files you expect to touch;
   - **done when:** the exact command that will show it works (the Done gate for this task,
     or Check plus a named test), and what only I can check by hand;
   - anything that needs my hands or a decision from me.
   Follow the Mode; in learn mode, mark the parts I write. If the task doesn't fit one
   session, don't plan it: propose the split.
5. Wait for my OK. Change no file before it.
6. After my OK, work the plan. Inside it you may loop on your own (edit, run, read the
   failure, fix, run again) until the "done when" command passes. Stop and ask me when:
   - you need to change something that wasn't in the plan and isn't a small consequence of it;
   - the same failure has survived 3 different fixes;
   - something needs my hands, or the spec is ambiguous, contradictory or wrong.
7. When "done when" passes, or you stopped: report in 5 lines or fewer (result, the output
   line that proves it, what's left). Then tell me what to check and to type `/wrap`.
