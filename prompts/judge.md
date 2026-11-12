---
description: Review the project with fresh eyes, as a sceptical user or judge - run it in a new session, never in the one that built the work
argument-hint: empty for the judge pass, "final" for the final review
---
Review type: $ARGUMENTS (empty means the judge pass)

You are reviewing, not building. If this session wrote any of the code under review, stop
and tell me to start a fresh one.

1. Before opening the code, read the brief I attach. If nothing is attached, use the Project
   section of AGENTS.md and the spec it points to. Take the role of the person in "For"; if
   there is none, a sceptical user who has to rely on this next week.
2. Then open the repo. Run Check and, if the project has one, the whole Done gate. Use the
   product the way that person would. For anything you can't do yourself (hardware, a
   screen, a real account) ask me, one request at a time.
3. Score it, with evidence for each score. Use "Judged on" from AGENTS.md if it is there.
   Otherwise: does what the spec says (per requirement: the evidence, or the gap), sound
   method, clear result, usable next week, data and secrets handled properly.
4. If AGENTS.md has a "First question": ask it and read the top results. Do they answer it
   usefully? Does every user group named there get something it can use?
5. List the issues ranked by value per hour of fixing. Don't fix anything; I decide.
6. If this is the final review, also: check every item in "Hand-in" if there is one; if
   there's a deck, export it to PDF and read the PDF; if there's a video, look at one still
   per scene and read the narration; compare with the last judge pass in docs/history.md.
7. Append the result to docs/history.md and add one line to PROGRESS.md. Commit those two
   files only.
