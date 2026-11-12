# Profile: competition, hackathon or client demo

Use this when someone else judges the result against criteria and a deadline. It is the part of the original short-loop template that came from the LoadLedger hackathon. Paste the blocks below into the project's files, fill the brackets, and delete this heading text.

## Into AGENTS.md, under "Project"
```
- **First question:** [what the judge or user asks first, and what a useful answer looks like].
- **Judged on:** [criteria with weights | none given].
- **Hand-in:** [what must be delivered, with limits | none].
- **Demo moment:** [one concrete thing shown live or found in real data].
- **Look:** [background, text and accent colours; light or dark]. Fixed at M0, used unchanged by the app, deck and video.
- **Team:** [me (solo) | names and roles].
```

## Into AGENTS.md, as its own section
```
## Budget
Budget: [16] h of work.
M0 skeleton 5% · M1 foundation 15% · M2 core feature 25% · first-question check · M3 [extra layer] 10% · M4 polish 20% · judge pass + fixes 25% · freeze
- Log start and end times in PROGRESS.md (a "Time" table: milestone, budget, start, end). When a milestone reaches its budget, stop and tell me what's left and what you'd cut; I decide.
- **After freeze:** bug fixes only; question any other change before doing it. For any change visible on screen, list the screenshots and clips that need retaking.
```

## Into AGENTS.md, under "Read only when needed"
```
| `docs/ai_log.md` | writing the README or disclosures; at /wrap, add a row when a new AI tool or purpose was used |
| `docs/PITCH.md` | only when I say "write the presentation materials" or "write the README"; then read it in full |
```
Copy `profiles/ai_log.md` from the kit to `docs/ai_log.md`.

## Into docs/plan.md, after the core feature
```
## First-question check (10 min, fresh session)
Read the results as the person in "For" would, and answer the First question from them. If the answer is weak, tell me before going on.

## M4 Polish
- The demo moment, layout on the target screen, wording without jargon.
- Error states: [the ones you expect, e.g. missing data, no key, no connection].
- No function or variable names on screen, including loading messages.

## Judge pass + fixes (fresh session)
Run `/judge`. It reports issues ranked by value per hour; I pick which ones get fixed.

## Freeze
After the judge pass, when the budget is used up, or when I say so. From then on, bug fixes only.
[IF deck or video] After the presentation materials are done: `/judge final` in a fresh session.
```
