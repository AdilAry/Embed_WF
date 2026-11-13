# Efficient AI Use: Tools and Setup

The tools from our conversation that keep context small and usage low. Main setup: **Claude Code on Claude Pro**, with **Pi** shelved for later (OpenAI and local models only).

As of November 2026. Commands and versions change; check each tool's docs before relying on a detail.

---

## 1. Claude Code built-ins

| Tool | What it does | How to use |
|---|---|---|
| `/context` | Shows what is filling the context window | Run it before a big task. Aim to finish below ~40%. |
| `/clear` | Starts a fresh session | Use between tasks: one task per session. |
| Rewind | Jumps back to an earlier message; everything after it is dropped from context | Esc Esc or `/rewind`. Use it instead of "no, try B": a correction leaves the failed attempt in context, a rewind removes it. Re-prompt with what you learned. |
| `/compact <what to keep>` | Summarizes the conversation to free space | Run it yourself, with instructions, before auto-compact kicks in. |
| Plan mode | Plans before touching code | Shift+Tab. Use it for big tasks only, not typos. |
| Output styles | Learning mode leaves `TODO(human)` markers for you to write | `/config` → Output style → Learning. Uses more tokens than Default. |
| `/btw` | Side question that is not added to the conversation | Ask "why did you do X?" without growing the context. |
| `!` shell mode | Runs a command yourself; Claude sees the output | Type `!` and the command, e.g. `! npm test`. |
| Subagents | Helpers with their own context window | Give simple ones a cheaper model: `model: haiku` or `model: sonnet` in the agent file. They use your quota fast on Pro. |
| Skills | Knowledge loaded only when relevant | Move specialized instructions out of CLAUDE.md into skills. Install a few, not dozens. |
| Prompt cache | Rereads of the conversation cost a fraction of normal | Automatic. On a subscription the cache lasts 1 hour within plan usage; subagents get 5 minutes. Coming back after hours = start fresh from PROGRESS.md. |
| Git worktrees | Separate checkout per session, so parallel sessions don't collide | `git worktree add ../myproj-feature feature-branch` |
| `/plugin` | Installs and toggles plugins (including mods) | Install, disable or remove add-ons. |

---

## 2. Project files (work in every harness)

| File | What it does | Setup |
|---|---|---|
| `AGENTS.md` | Instructions for any agent: build/test commands, conventions | Keep it short; every line is paid for in every session. |
| `CLAUDE.md` | Claude Code's instruction file | Make it one line: `@AGENTS.md` |
| `PROGRESS.md` | Handoff between short sessions: state, next step, decisions, dead ends | The agent updates it at the end of each session; the next session reads it first. |

---

## 3. Add-ons for Claude Code

### Mods (Claude Code 2.1.287+)
Small TypeScript functions, shipped inside plugins, that can change prompts, tool results, the UI and built-in features. They are **not sandboxed**: they run with your full permissions. Install only from sources you trust, and read the code first.

Mods from the "5 Claude Mods" video, and whether you need them:

| Mod | What it does | Built-in alternative / note |
|---|---|---|
| Input router | Large files and connector results go to Haiku first; Claude gets a short summary | Most useful for transcripts and connector dumps. Risky for code, where details matter. |
| Effort optimizer | Suggests a lower or higher effort level per prompt | Pick effort yourself: low for simple tasks, high for hard ones. |
| Subagent model selector | Routes each subagent to Haiku, Sonnet or Opus by difficulty | Set `model:` in your agent files yourself. |
| Cache clock | Shows when the cache expires; optional "keep warm" pings | Keep-warm pings also cost usage. A fresh session from PROGRESS.md is often cheaper. |
| Handoff | Offers a fresh chat with a detailed handoff prompt when a chat gets long | Same idea as PROGRESS.md, which you already use. |
| Efficient browser | Shrinks browser screenshots before Claude sees them | Only matters if you use browser automation. |

### TokenEconomizer (Microsoft Research)
Learns from your repeated sessions in a repo: remembers repo facts, drops unused tools, nudges stuck loops. Suits short-loop workflows.

```bash
git clone https://github.com/microsoft/TokenEconomizer.git
claude plugin marketplace add "$PWD/TokenEconomizer"
claude plugin install tokeneconomizer@tokeneconomizer
# inside Claude Code:
/tokeneconomizer:status
/tokeneconomizer:toolprune refresh-catalog
```
Check its supported Claude Code versions in the README first. Micro-skills is off by default; turn it on with `/tokeneconomizer:config set microskills=on`.

### Codex review plugin (OpenAI, official)
Runs OpenAI's Codex inside Claude Code for a second opinion: `/codex:review`, `/codex:adversarial-review`, `/codex:rescue`. Claude does the work on your Pro plan; the review runs on your OpenAI budget. Repo: https://github.com/openai/codex-plugin-cc (install via `/plugin`, see its README).

### grill-me skill (Matt Pocock)
Makes the agent interview you about your plan before it builds anything. Cheap insurance against long, wrong sessions. Find it on skills.sh or in Matt Pocock's skills repo.

---

## 4. Tools around the agent

| Tool | What it does | Setup |
|---|---|---|
| `glab` (GitLab CLI) | Issues, merge requests and pipelines from the terminal; agents can call it | `glab auth login`. For a self-hosted instance later, set `GITLAB_HOST`. Tell the agent to use `--output json`. `glab mcp serve` exists but is experimental; plain CLI calls use less context. |
| Claude Code in GitLab CI/CD | Runs Claude Code in GitLab pipelines (reviews, fixes on merge requests) | Docs: https://code.claude.com/docs/en/gitlab-ci-cd. Check how it bills before using it: pipelines usually need an API key, not your Pro plan. |
| Tests, linters, type checkers | The compact feedback agents loop against instead of you reviewing output | Put the exact commands in AGENTS.md. |

---

## 5. Later: Pi

| Tool | What it does | Setup |
|---|---|---|
| Pi | Minimal agent harness: four tools, small system prompt, any model provider | Windows: `powershell -c "irm https://pi.dev/install.ps1 \| iex"`; Linux: `curl -fsSL https://pi.dev/install.sh \| sh`. Then `/login` with OpenAI. |
| Local models | Small models on the GTX 1650 (roughly 3–8B, quantized) for offline questions | Run through an OpenAI-compatible local server and point Pi at it. Not strong enough for agent loops. |

Pi does **not** run on Claude subscriptions (Pro, Max or Team). Keep Claude in Claude Code. Pi has no permission system, so run it in a container or a separate user account.

---

## 6. Watch list (nothing to set up)

- **DeltaDB / Delta (Zed):** operation-level version control alongside Git; private beta.
- **Scion (Google):** runs multiple agents in isolated containers; experimental.
- **UTCP:** MCP alternative where agents call tools directly; small adoption so far.
- **SkillOpt (Microsoft):** trains a skill file against a scored task set and keeps only edits that improve held-out scores; outputs `best_skill.md`. Worth trying once you have a repeated task that tests can score (e.g. host-side tests for an ESP32 driver). Training runs use many agent calls, so use OpenAI as the optimizer to spare your Claude plan. SkillOpt-Sleep (preview) proposes skill updates from past sessions. https://github.com/microsoft/SkillOpt
