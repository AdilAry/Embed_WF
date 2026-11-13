# AGENTS.md: [project name]

Loaded in every session. Keep it under ~120 lines once filled in: only facts that hold for the whole project. Detail lives in docs/, behind "Read only when needed". A heading that carries an [IF ...] marker makes its whole section optional: delete the section if the condition doesn't hold.

## Project
- **What:** [one line].
- **Why:** [portfolio piece | work prototype | tool for myself | client demo | fixing an existing codebase | competition: name, dates, deadline].
- **For:** [the person who will use or judge it].
- **Second machine:** [no role in this project | its role, e.g. demo backup or budget-hardware tests].

## Problem [IF it has users other than me]
- **Who has it:** [users, in plain words].
- **Pain points:** [1–3, in their words if I have them].
- **They want / don't want:** [e.g. mobile first, no jargon, runs offline, no subscription].

## Scope
- **One sentence:** [A ___ that ___, so that ___ without ___].
- **MVP:** [3–5 bullets].
- **Not doing:** [e.g. login, payments, native app].
- **Constraints:** [platforms, languages, legal, hardware, data access | none].

## Stack
- **Language and tools:** [e.g. Python 3.12 + Streamlit, pandas | C + PlatformIO | Godot 4 + GDScript].
- **Run:** `[command that starts it, in a fresh terminal]`
- **Check:** `[the command that says whether it works: tests, build, linter]`. Run it before calling anything done.
- **Done gate:** the task's "Done when" in docs/plan.md passes. For a task that isn't in the plan: Check passes, and a named test covers the change.
- **Run limit:** [10] failed runs of "done when" in one session. Then stop and report.
- **Push:** [in /wrap | only after I've checked the result].
- **Hardware:** [none | board, notes file in docs/].
- **Deploy:** [local only | where]. [IF deployed] Never deploy before I've checked the result.

## Competition [IF someone else judges the result against criteria and a deadline]
- **First question:** [what the judge or user asks first, and what a useful answer looks like].
- **Judged on:** [criteria with weights | none given].
- **Hand-in:** [what must be delivered, with limits | none].
- **Demo moment:** [one concrete thing shown live or found in real data].
- **Look:** [background, text and accent colours; light or dark]. Fixed at M0, used unchanged by the app, deck and video.
- **Team:** [me (solo) | names and roles].
- **Budget:** [16] h of work. M0 skeleton 5% · M1 foundation 15% · M2 core feature 25% · first-question check · M3 [extra layer] 10% · M4 polish 20% · judge pass + fixes 25% · freeze. When a milestone reaches its budget, stop and tell me what's left and what you'd cut; I decide.
- **After freeze:** bug fixes only; question any other change before doing it. For any change visible on screen, list the screenshots and clips that need retaking.
- **At /start also:** log the start time in the Time table of PROGRESS.md (`Get-Date` on Windows, `date` on Linux).
- **At /wrap also:** log the end time in the Time table and put the time spent in the history entry. If a new AI tool or purpose was used this session, add a row to docs/ai_log.md.

## Data [IF the project uses data]
- **Source:** [files, API or sensor, and where they live].
- **Rules that always hold:** [at most 5 lines; anything longer goes in docs/data.md].
- **Licences:** [each source, its licence and the attribution text].
- **Sending data to an external AI:** [not allowed: work from column names and synthetic fixtures | allowed by the owner, named here, for what].
- **AI in the product:** [none | provider, key name in .env, notes file in docs/]. Rules and real data decide; AI only explains results the code has verified. It works without keys: cached answers, labelled as cached.
- `data/raw/` is never committed if it holds personal, company-internal or unlicensed data.

## Workflow
- One task per session: `/start <task>` begins it, `/wrap` ends it, then I clear the session. A fresh session must be able to continue from PROGRESS.md alone.
- PROGRESS.md holds the current state only. Finished work goes to docs/history.md.
- `/judge` reviews in a fresh session, never in the one that built the work.

## Read only when needed
| File | Read when |
|---|---|
| `docs/plan.md` | starting a task: its section only |
| `docs/decisions.md` | a decision is questioned or about to change |
| `docs/history.md` | I ask what happened earlier, or a judge pass compares results |
| `docs/notes/` | the task needs a source summarised there |
| [IF data] `docs/data.md` | before changing code that loads, joins or computes data |
| [IF competition] `docs/ai_log.md` | writing the README or disclosures |
| [IF competition] `docs/PITCH.md` | only when I say "write the presentation materials" or "write the README"; then read it in full |
| [another file] | [when] |

## Files
```
[entry point, e.g. app.py | src/main.c | project.godot]   [what it is]
core/          [logic, no UI code]
tests/         what the Check command runs
docs/          plan, history, decisions; notes/ holds short summaries of long sources
out/           long output and commit messages (gitignored)
[other folder] [what lives there]
```
