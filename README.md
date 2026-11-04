# Embed_WF — an AI-assisted ESP32 workflow on hobby hardware

You write specifications and tests. An AI agent (Claude Code) writes the
firmware, builds it, flashes the board, reads the serial output, runs the tests
and fixes its own mistakes, until the tests pass.

Built for: a Claude Pro subscription, a Windows laptop to supervise from, an old
Linux Mint laptop as the agent's sandbox and test bench, and Guition JC4827W543
(ESP32-S3, 4.3" touch) boards in both the resistive and capacitive variants.

**Start here → [docs/GUIDE.md](docs/GUIDE.md)** · What changed in the review →
[docs/REVIEW.md](docs/REVIEW.md)

| | |
|---|---|
| [docs/GUIDE.md](docs/GUIDE.md) | Full setup + workflow guide (read once) |
| [docs/cheatsheet.md](docs/cheatsheet.md) | Daily commands and prompts |
| [docs/testing.md](docs/testing.md) | The four test tiers: host → target → bench → field |
| [docs/troubleshooting.md](docs/troubleshooting.md) | When something doesn't work |
| [docs/claude-desktop-project.md](docs/claude-desktop-project.md) | Set up Claude Desktop as the planning side of the workflow |
| [docs/REVIEW.md](docs/REVIEW.md) | Review of the first version: findings, fixes, what still needs your boards |
| [hardware/](hardware/) | Your machines and the board reference |
| [template/](template/) | Starter project: working firmware, tests, serial tool, requirement tracing (`make trace`), CI |
| [skills/](skills/) | Claude Code skills: `/define` `/commission` `/build-loop` `/datasheet` `/change-request` `/wrap-up` `/new-project` |
| [devbox/](devbox/) | Setup scripts for the Linux dev box |
| [bench/](bench/) | Test-bench commands: Wi-Fi hotspot, MQTT broker, BLE scan |

## Quick start (dev box, after reading the guide)

```bash
sudo bash devbox/setup-root.sh embdev         # once, from your admin account
```

```bash
bash ~/Embed_WF/devbox/setup-user.sh          # once, as embdev
```

```bash
new-embedded-project hello-board && cd ~/projects/hello-board && claude
```

Then type `/commission` in Claude Code.

## Status

| Part | State |
|---|---|
| Host tests, serial tool, project generator | tested |
| Requirement tracing (`make trace`), serial-tool crash/boot parsing | unit-tested in CI (`tests/`) |
| Firmware compile | checked by CI on every push (`template` workflow) |
| On-board run, R board (XPT2046) | display/touch code taken from your proven sketch; first full run happens at your first `/commission` |
| On-board run, C board (GT911) | **unverified**, so it gets checked and fixed during your first `/commission` |
| Bench scripts (hotspot / MQTT / BLE) | written for Mint + NetworkManager; not yet run on your T480s |

Inspired by the "10 levels" / embedded AI harness approach described in the
reference videos (see `docs/GUIDE.md` §1).
