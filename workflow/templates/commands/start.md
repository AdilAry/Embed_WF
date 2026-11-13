---
description: Start a short session on one task - a plan section, an ID, or free text
argument-hint: task, e.g. M2 or "fix the export" (empty = Next in PROGRESS.md)
---
Task for this session: $ARGUMENTS

The project's AGENTS.md defines **Check**, **Done gate**, **Run limit** and **Push**.

1. Run `git pull` (skip it if the repo has no remote). Read PROGRESS.md. If no task was given,
   take item 1 under "Next".
2. If PROGRESS.md and the code disagree, tell me before anything else.
3. If "Waiting on me" lists work awaiting my check, ask me whether each one passed, before you
   plan. One that I reject becomes this session's task.
4. Read only what the task needs: its own section of the plan (AGENTS.md "Read only when
   needed" says where). Not the whole file, not the whole codebase.
5. Reply with a plan of at most 5 bullets:
   - the steps, smallest first, tests before the code they prove, and the files you expect to touch;
   - **done when:** the exact command that will prove it works: the plan's "Done when" if the
     section has one, otherwise the Done gate. For a task with no code (docs, research, a
     decision) there is no command: name the file that must exist and what it must say, and
     that I approve it. Never invent a check;
   - what only I can check by hand;
   - anything that needs my hands or a decision from me.
   If the task doesn't fit one session, don't plan it: propose the split.
6. Wait for my OK. Change no file before it.
7. After my OK, do the bookkeeping first: record the checks I confirmed in step 3 (tick the
   item where the plan lives, append its entry to docs/history.md, move it from "Waiting on me"
   to "Done"), and do every "At /start also" step AGENTS.md lists. Then work the plan. You may
   loop on your own (edit, run, read the failure, fix, run again) until "done when" passes.
   Stop and report when:
   - you need to change something that isn't in the plan and isn't a small consequence of it;
   - the same failure has survived 3 different fixes;
   - "done when" has failed as many times as the Run limit (10 if AGENTS.md gives none);
   - something needs my hands, or the plan or spec is ambiguous, contradictory or wrong.
8. When it passes, or you stopped: report in 5 lines or fewer (the result, the output line that
   proves it, what's left). Then tell me what to check and to type /wrap.
