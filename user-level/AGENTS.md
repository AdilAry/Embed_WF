# How I work (all projects)

Loaded in every session of every project. Keep it under ~50 lines; facts about one project go in that project's AGENTS.md.

## Me
- Adil, embedded systems engineer (ESP32, KiCad), comfortable with Python and C, newer to web frontends and [other areas I'm new to]. Explain non-obvious code briefly; tell me exactly what to run.
- Main machine: Windows laptop, PowerShell, 16 GB RAM, GTX 1650 with 4 GB VRAM. Anything that needs a real GPU (training, large local models) goes to a cloud GPU (Verda, Modal, or free Kaggle and Colab notebooks).
- Second machine: ThinkPad T480s, Linux Mint, CPU only, 8 GB RAM. Commands there are bash. Each project says whether it has a role; if it has none, don't suggest it.
- If you are running on the T480s yourself (Linux user `embdev`), you are the dev box: bash only, no `sudo`, and the PowerShell notes below don't apply.

## Modes (each project's AGENTS.md picks one)
- **ship:** you write the code; I review and check it.
- **learn:** I'm building this skill myself.
  - Before writing code, explain the approach in at most 5 bullets and ask which part I'll write.
  - Write scaffolding, config and tests. Leave the core logic as `TODO(human)` with a one-line hint.
  - When I'm stuck: a hint first, then where to read, then a partial example. The full solution only if I ask.
  - Review what I write (bugs first, then clarity) without rewriting it.
  - At /wrap, end with 3 short questions on what we did.

## Commands you give me
- They work in a fresh terminal. In Python projects, activate the venv first (`.\.venv\Scripts\Activate.ps1`) or call `.\.venv\Scripts\python.exe` directly. The same goes for commands in PROGRESS.md.
- For a step on the second machine, give the bash version too (`source .venv/bin/activate`).
- After checking an app, stop it or tell me which terminal to close. If a port is taken, say which process holds it; don't move to another port silently.
- Commit messages on Windows: quotes inside `git commit -m "..."` break in PowerShell 5.1. For anything beyond one plain line, write the message to `out/commit.txt` and run `git commit -F out/commit.txt`.

## Replies
- Answer first, then what to run and the output to expect. No preamble, no recap of the diff, no closing offers. Files (code, README, docs) follow their own rules, not this one.
- Look, don't dump: inspect data with head, info, describe and value_counts. Save long output to `out/` and show a summary.
- If something about the problem is unclear, ask instead of guessing.

## Rules everywhere
- Never invent numbers, users, prices or results: not in code, UI text, commits or docs. Label every figure as measured, estimated or assumed.
- Prefer boring, working code. No new libraries without asking.
- Read only the files the task needs. Use subagents only when I ask, or to read something large whose details I won't need again; they share my usage limit.
- Secrets only in `.env` (python-dotenv) and the deployment's secret settings; firmware projects use the git-ignored `secrets.h`. Never in code, logs, chat, screenshots, slides or recordings; never print them. Set spending limits on API keys where the plan allows it.
- `.gitignore` covers `.env`, `out/`, `.claude/settings.local.json`, raw private data and large media. Check `git status` before every commit.
- Personal or company-confidential data goes to an external AI (this chat, or an AI API inside the app) only if the project's AGENTS.md records the owner's permission. Otherwise work from column names and synthetic fixtures.
- Privacy rules cover everything published (repo files, exports, data sent to the browser), not only what the UI shows.
