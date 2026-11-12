# The short-loop workflow

How every project in this kit is worked, embedded or not: short sessions, with files carrying the memory between them. One session does one task and ends; the next starts clean and reads what it needs from files.

This is the owner's short-loop workflow (November 2026), with four changes that are argued in §8. It runs the same under **pi** and **Claude Code**.

---

## 1. The idea

A session gets worse as its context fills up. So each session does one task and ends, and the next one starts clean. That only works if the files it starts from stay small, so files are split by **how often they are read**:

| File | Holds | Loaded | Size | Edited by |
|---|---|---|---|---|
| User-level "How I work" file | About you, your machines, rules for every project, the two modes | Every session, every project | ~50 lines | You, once |
| `AGENTS.md` (project) | Facts about this project, Check, Done gate, read-when pointers | Every session in this project | under ~120 lines | You at setup; the agent only when asked |
| `PROGRESS.md` | Current state only | Start of every session | under ~60 lines | Agent, via `/wrap` |
| Plan (`docs/plan.md`, embedded: `docs/PLAN.md` + `docs/FSD.md`) | What each task must deliver and how it is proven | At a task's start, its section only | Any | You at setup |
| `docs/history.md` | Finished tasks, judge passes | Only when asked | Any (append only) | Agent |
| `docs/decisions.md` | Decisions with reasons and rejected options | When a decision is questioned | Any | Agent |
| `docs/notes/`, `datasheets/*.summary.md` | Short summaries of long sources | When a task needs one | Short each | Agent |
| Slash commands | `/start`, `/wrap`, `/judge` (+ the embedded ones) | When you type them | Short | Installed once per machine |

**Five rules that keep the files small:**
1. **PROGRESS.md is a snapshot, not a log.** `/wrap` rewrites "Now" and "Next" every session.
2. **Delete, don't strike through.** Once something is resolved it leaves PROGRESS.md; history.md keeps the record.
3. **Point, don't paste.** Long material lives in `docs/`, and AGENTS.md says when to read it.
4. **One fact, one place.** If AGENTS.md and PROGRESS.md both say it, one of them will go stale.
5. **Rules for every project go in the user-level file once**, not in each project.

---

## 2. A session

**Start:** `/start M2` (or a requirement, `/start REQ-020`, or any task, `/start fix the export`). The agent pulls, reads PROGRESS.md and that task's part of the plan, and replies with a plan of at most 5 bullets that ends in **done when:** the exact command that will prove it. Correct the plan or OK it. Nothing is changed before your OK. *(Gate 1: you approve the plan.)*

**Work.** After the OK the agent loops on its own (edit, run, read the failure, fix) until the "done when" command passes. It stops and asks if it needs to go outside the plan, if the same failure survives three different fixes, or if something needs your hands or a decision. This inner loop is where the tokens go, so it is bounded by one task and one objective stop condition.

**End:** `/wrap`. It runs Check and the Done gate, rewrites PROGRESS.md, moves finished work to history.md, commits, and replies with the files changed, what to run, the output you should see and what to check by hand. Check it, then clear the session. *(Gate 2: you check the result.)*

Ending in the middle of a task is fine: `/wrap` records exactly where it stopped.

**Review with fresh eyes:** `/judge` in a **new** session. A reviewer that watched the work being built ends up grading its own work.

---

## 3. Habits that keep context clean

| Habit | pi | Claude Code |
|---|---|---|
| New task, new session | `/new` | `/clear` |
| Wrong path? Go back to before the attempt and re-prompt with what you learned. A correction ("no, try B") leaves the failed attempt in context | `/tree`, pick the earlier point | Esc Esc (rewind) |
| See how full the context is; wrap around 40% | footer, `/session` | `/context` |
| Shrink a long session you can't end yet | `/compact` | `/compact <what to keep>` |
| Same mistake twice | stop, `/wrap`, new session with what you learned in the first prompt | same |
| Big reading (spec, datasheet, another codebase) | its own session that only writes a summary (`/datasheet`), then `/new` | a subagent, or the same |

Check `/hotkeys` (pi) or the docs if a command behaves differently: both tools change fast.

---

## 4. Which agent, on which machine

The project files are the same for every agent: `AGENTS.md` is the real instruction file, and `CLAUDE.md` is one line (`@AGENTS.md`) that makes Claude Code read it. The slash commands are one set of files in `prompts/`, copied to each agent by `tools/install-workflow.sh`.

So the choice of agent is about billing and risk, not about the project:

- **Claude Code** runs on a Claude subscription and asks before running commands.
- **pi** runs on an OpenAI login, GitHub Copilot or an API key from most providers. A Claude Pro/Max plan's limits do not cover pi: Anthropic bills third-party harnesses separately (extra usage or API rates; the terms changed several times in 2026, so check before relying on it). pi **never asks** before running a command, so it belongs in an account where a mistake costs nothing (the `embdev` user on the T480s; see GUIDE §6).

You can switch agent between sessions of the same project: the memory is in the files, not in the agent.

---

## 5. Setup

**Once per machine (Linux, the T480s):**

```bash
bash ~/Embed_WF/tools/install-workflow.sh
```

It copies the commands to every agent it finds and installs `user-level/AGENTS.md` as the agent's global file if there is none yet. Open that file once and fill its one bracket. Run the script again after `git pull`; it never overwrites your edited global file.

**Once per machine (Windows, Claude Code), from the folder where you cloned the kit:**

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\commands" | Out-Null
```
```powershell
Copy-Item prompts\*.md "$env:USERPROFILE\.claude\commands\"
```
```powershell
if (-not (Test-Path "$env:USERPROFILE\.claude\CLAUDE.md")) { Copy-Item user-level\AGENTS.md "$env:USERPROFILE\.claude\CLAUDE.md" }
```

**Per project:**

| | Command | Then |
|---|---|---|
| ESP32 project | `new-embedded-project <name>` | write `docs/IDEA.md`, `/define`, `/commission`, `/start …` (GUIDE §5) |
| Anything else | `new-project <name>` | fill `AGENTS.md` and `docs/plan.md`, `/start M0` |

On Windows, copy the `generic/` folder by hand instead.

### Markers in the generic starter

| Marker | Meaning |
|---|---|
| `[text]` | Fill in: replace the brackets and everything inside |
| `[value]` | Suggested default: keep or change it, then remove the brackets |
| `[a \| b \| c]` | Choose one; delete the rest |
| `[IF condition]` | Keep the line only if the condition holds; delete the marker either way |

The starter contains no other square brackets, so before the first session any `[` left over means something is unfinished: `grep -n '\[' AGENTS.md docs/plan.md` (PowerShell: `Select-String -Pattern '\[' -Path AGENTS.md, docs\plan.md`).

### Profiles

The starter is deliberately small. Two optional blocks live in `profiles/` and are pasted in only when the project is that kind:

- `profiles/competition.md`: first question, judging criteria, hand-in, time budget, freeze, AI-use log, pitch materials.
- `profiles/data.md`: data sources, rules, licences, `docs/data.md`.

The embedded template is a third, bigger profile: it adds the FSD, the four test tiers, `make trace` as the Done gate, and the commands `/define`, `/commission`, `/datasheet`, `/change-request`.

---

## 6. When things go wrong

| Symptom | Fix |
|---|---|
| A session starts with a lot of context already used | Trim AGENTS.md and PROGRESS.md; move detail to `docs/`. |
| The agent works from stale information | PROGRESS.md contradicts itself: rewrite "Now" and "Next", delete resolved items. |
| A task doesn't fit in one session | Split it in the plan (M2a, M2b; two plan items instead of one). |
| The plan keeps being wrong at Gate 1 | The plan section is too vague. Add its "done when" and edge cases there, not in chat. |
| The same mistake keeps coming back | Add one line to AGENTS.md (or the user-level file if it happens in every project). Remove rules again once models stop needing them. |
| The agent keeps asking what to do next | "Next" in PROGRESS.md isn't concrete enough to start from. |
| `/start` isn't offered | The commands aren't installed for this agent: run `tools/install-workflow.sh`, then `/reload` (pi) or a new session. |

---

## 7. How the embedded workflow maps onto it

| Short loop | In an embedded project |
|---|---|
| Task | one item of `docs/PLAN.md` (a requirement or two with their tests) |
| Plan section | that item, plus its rows in `docs/FSD.md` |
| Check | `make check` (host tests + compile) |
| Done gate | `make trace RUN=1 REQS="…"` prints `TRACE:OK` |
| Inner loop | host-test → compile → upload → boot-check → target-test → bench-test → fix |
| "What I check by hand" | the `field` / `manual` requirements; anything on the screen |
| Notes on long sources | `datasheets/*.summary.md`, the board reference |

---

## 8. What changed from the owner's original version, and why

| Original | Now | Why |
|---|---|---|
| `CLAUDE.md` is the instruction file; commands in each project's `.claude/commands/`; switching agent "later" means renaming files in every project | `AGENTS.md` is the file, `CLAUDE.md` is a one-line shim; one `prompts/` folder installed per machine for every agent | The original only ran under Claude Code, and pi is in use now. Neutral files cost nothing today and make the agent a per-session choice. One installed copy also means an update is one `git pull`, not an edit in every repo. |
| One project template shaped by a hackathon data app (first question, judged on, hand-in, look, budget percentages, freeze, AI log); other project types delete most of it | A small core, plus `profiles/` pasted in when they apply | "Applies to most software work" by composition, not by deletion. The always-loaded file drops from a ~120-line cap to ~80, and nothing in it is irrelevant. |
| `/start` ends at "wait for my OK"; what counts as finished is decided at the end | The plan must name **done when:** a command; the agent may loop only until it passes, and must stop when it leaves the plan | The loop gets an objective stop condition agreed before any token is spent on code. It bounds the session and makes Gate 2 a check of evidence, not of the agent's summary. |
| `/wrap` always updates PROGRESS, history, decisions, the AI log and the time table, and its reply has no list of what changed | `/wrap` touches only files that have something new, the time table and AI log live in the competition profile, and the reply lists the files changed | With short sessions, wrap is a real share of every session's cost. And a reviewer needs to know where to look. |
| `/start` logged the start time by editing PROGRESS.md before the OK | No file changes before the OK | It contradicted the command's own last step. |
| `/judge` assumed a judged, presented product | The same command, with the competition steps conditional | It now also reviews firmware against its spec. |

Kept as they were: the split of files by read frequency, the five rules, the snapshot PROGRESS.md, the ship/learn modes, the fresh-session review, the bracket markers.
