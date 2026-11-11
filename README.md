# Embed_WF — an AI-assisted ESP32 workflow on hobby hardware

You write specifications and tests. An AI agent (**pi**, pi.dev) writes the
firmware, builds it, flashes the board, reads the serial output, runs the tests
and fixes its own mistakes, until the tests pass.

Built for: the pi coding agent with the model provider of your choice, a Windows
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
| [prompts/](prompts/) | pi prompt templates = the slash commands `/define` `/commission` `/build-loop` `/datasheet` `/change-request` `/wrap-up` `/new-project` |
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
new-embedded-project hello-board && cd ~/projects/hello-board && pi
```

Then type `/commission` in pi.

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
| pi install + prompt templates | written from pi's documentation; not yet run on your T480s |

Inspired by the "10 levels" / embedded AI harness approach described in the
reference videos (see `docs/GUIDE.md` §1).
