---
description: End the session and leave PROGRESS.md ready for a fresh one
argument-hint: optional note on where we stopped
---
End this session. Note from me: $ARGUMENTS

1. Run Check from AGENTS.md (skip it if this session changed documentation only). If the
   task is being called finished, run its Done gate too. If either fails, say so plainly and
   treat the task as unfinished.
2. Rewrite "Now" and "Next" in PROGRESS.md from scratch. "Next" item 1 must be startable
   without asking: name the task or ID and the first file or command. If the task isn't
   finished, write exactly where it stopped.
3. Delete everything resolved or no longer true. Never strike through.
4. If a plan item or milestone is finished: tick it where the plan lives, append a short
   entry (built, checked, left open) to docs/history.md, and keep one line for it under
   "Done" in PROGRESS.md.
5. Only where there is something new: a decision someone might question later goes to
   docs/decisions.md. Don't open or rewrite files that have nothing new.
6. Do the steps under "At /wrap also" in AGENTS.md, if the project lists any.
7. Keep PROGRESS.md under ~60 lines; if it's longer, move the oldest detail to docs/history.md.
8. Check `git status`, then commit with a message that names the task or requirement IDs.
   Push only as "Push" in AGENTS.md says.
9. Reply with: the files changed (the list from `git show --stat`, nothing more), what to run
   to check the result, the output I should see, what I have to check by hand, and the next
   step. In learn mode, end with 3 short questions on what we did.
