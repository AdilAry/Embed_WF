# AGENTS.md: [project name]

Loaded in every session. Keep it under ~80 lines: only facts that hold for the whole project. Detail lives in docs/, behind "Read only when needed". Blocks for a competition or a data project are in the kit's `profiles/` folder: paste one in only if this project is that kind.

## Project
- **What:** [one line].
- **Why:** [portfolio piece | work prototype | tool for myself | client demo | fixing an existing codebase].
- **For:** [the person who will use it].
- **Mode:** [ship | learn | learn for the area named here, ship for the rest]. The modes are defined in my user-level file.
- **Second machine:** [no role in this project | its role, e.g. demo backup or budget-hardware tests].

## Scope
- **MVP:** [3–5 bullets].
- **Not doing:** [e.g. login, payments, native app].
- **Constraints:** [platforms, languages, data access, legal, hardware | none].

## Stack
- **Language and tools:** [e.g. Python 3.12 + pandas | C + PlatformIO | Godot 4 + GDScript].
- **Run:** `[command that starts it, in a fresh terminal]`
- **Check:** `[the command that says whether it works: tests, build, linter]`. Run it before calling anything done.
- **Done gate:** [Check passes and the task's named test exists and passes | a stricter command].
- **Push:** [in /wrap | only after I've checked the result]. [IF deployed] Never deploy before I've checked.

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
