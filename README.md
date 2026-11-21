# Embed_WF — an AI-assisted ESP32 workflow on hobby hardware

You write specifications and tests. An AI agent (**Claude Code**) writes the
firmware, builds it, flashes the board, reads the serial output, runs the tests
and fixes its own mistakes, until the tests pass: one plan item per short
session, with you approving the plan before and checking the result after.
Nothing counts as finished until you have checked it.

Built for: Claude Code on a Claude plan (pi later, for self-hosted models), a Windows
laptop to supervise from, an old Linux Mint laptop as the agent's sandbox and
test bench, and Guition JC4827W543 (ESP32-S3, 4.3" touch) boards in both the
resistive and capacitive variants.

**Start here → [docs/GUIDE.md](docs/GUIDE.md)** · What has and hasn't been
verified → [docs/REVIEW.md](docs/REVIEW.md)

| | |
|---|---|
| [docs/GUIDE.md](docs/GUIDE.md) | Full setup + workflow guide (read once) |
| [docs/cheatsheet.md](docs/cheatsheet.md) | Daily commands and prompts |
| [docs/testing.md](docs/testing.md) | The four test tiers: host → target → bench → field |
| [docs/troubleshooting.md](docs/troubleshooting.md) | When something doesn't work |
| [docs/planning-chat.md](docs/planning-chat.md) | Using a chat app as the planning side of the workflow |
| [docs/REVIEW.md](docs/REVIEW.md) | Review history: findings, fixes, what still needs your boards |
| [hardware/](hardware/) | Your machines and the board reference |
| [template/](template/) | Starter project: working firmware, tests, serial tool, requirement tracing (`make trace`), CI |
| [prompts/](prompts/) | The embedded slash commands: `/define` `/commission` `/datasheet` `/change-request` `/new-project` |
| [devbox/](devbox/) | Setup scripts for the Linux dev box |
| [bench/](bench/) | Test-bench commands: Wi-Fi hotspot, MQTT broker, BLE scan |

## Built on the short-loop workflow

The session method (`/start` … `/wrap`, `/judge`, PROGRESS.md and the files
around it) is the **short-loop workflow**, a separate repository. This kit
doesn't carry a copy. It uses only what the workflow's WORKFLOW.md §8,
"Building a kit on this workflow", lists, and finds the workflow through
`WORKFLOW_DIR`, which the workflow's own installer sets.

**Written against the contract of 21 November 2026.** If your workflow's §8
shows a later date, check what changed there before relying on this kit.

## Quick start (dev box, after reading the guide)

```bash
sudo bash devbox/setup-root.sh embdev         # once, from your admin account
```

As embdev: clone the short-loop workflow repository, run its `install.sh`
once, and open a new terminal (that sets `WORKFLOW_DIR`). Then:

```bash
bash ~/Embed_WF/devbox/setup-user.sh          # once, as embdev
```

```bash
new-embedded-project hello-board && cd ~/projects/hello-board && claude
```

Then type `/commission` in Claude Code, `/wrap` when it finishes, and from then on
`/start` … `/wrap` for one plan item at a time.

## Status

| Part | State |
|---|---|
| Host tests, project generator | tested |
| Serial tool (pass / fail / panic / boot-loop paths, board selection, open-reset check) | unit-tested in CI, and run end to end against a **simulated** board. Never against a real one yet. |
| Requirement tracing (`make trace`), stale-result detection, per-board results | unit-tested in CI (`tests/`) |
| Firmware compile | checked by CI on every push (`template` workflow) |
| On-board run, R board (XPT2046) | display/touch code taken from your proven sketch; first full run happens at your first `/commission` |
| On-board run, C board (GT911) | **unverified**, so it gets checked and fixed during your first `/commission` |
| Bench scripts (hotspot / MQTT / BLE) | written for Mint + NetworkManager; not yet run on your T480s |
| Claude Code install + allowlist + slash commands | installer and project generator run in a throwaway home; the allowlist (`template/.claude/settings.json`) is valid JSON but has not yet carried a real `/start` … `/wrap` loop. Not yet on your T480s |
| Short-loop workflow | external (`WORKFLOW_DIR`), relied on only through its §8 contract of 21 Nov 2026. `tools/install-workflow.sh` was run against it in a throwaway home; no agent has yet run `/start` … `/wrap` on an embedded project |

Inspired by the "10 levels" / embedded AI harness approach described in the
reference videos (see `docs/GUIDE.md` §1).
