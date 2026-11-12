# Review history of the Embed_WF kit

Four passes so far. The newest is first. None of them has touched your real
boards or the T480s, so the last section is the list that matters most.

## Pass 4 (November 2026): the short loop

Your generic short-loop workflow (short sessions, files as memory, `/start` …
`/wrap`, `/judge` in a fresh session) was reviewed and made the way every
project in this kit is worked. The embedded workflow changed shape to fit it.

| # | Finding | Why it matters | Change |
|---|---|---|---|
| 1 | The embedded kit ran long: `/build-loop` implemented a whole phase with no plan approval, the opposite of a short loop. | Long sessions cost more per step as context fills, and your only gates were physical actions and failures. | `/build-loop` and `/wrap-up` are gone. One plan item per session: `/start` proposes a plan and waits, the agent loops against the tests inside it, `/wrap` ends it. The closed test loop is still there, just bounded. |
| 2 | The embedded kit had no current-state file. `docs/NOTES.md` was an append-only log the agent was pointed at every session. | That is the growing-file problem your workflow was written to fix. | `PROGRESS.md` (snapshot, rewritten every `/wrap`), `docs/history.md` (append-only, read on request) and `docs/decisions.md` replace `NOTES.md`. |
| 3 | The short-loop workflow only ran under Claude Code (`CLAUDE.md`, `.claude/commands/` per project, `~/.claude/CLAUDE.md`). | pi is in use here, and pi reads none of those. | `AGENTS.md` is the instruction file, `CLAUDE.md` a one-line shim. One `prompts/` folder serves both agents; `tools/install-workflow.sh` installs it and the user-level file per machine. |
| 4 | The project template was shaped by a hackathon data app; other project types had to delete most of it. | "Applies to most software work" by deletion is fragile, and the always-loaded file carried fields most projects don't have. | A small generic starter (`generic/`), with the competition and data parts as optional `profiles/`. The embedded template is the third profile. |
| 5 | `/start` had no agreed stop condition, and `/wrap` rewrote several files every session. | The inner loop is where tokens go; it needs an objective end. Wrap overhead matters when sessions are short. | The plan must name **done when:** a command. `/wrap` only touches files with something new and lists the files changed. |
| 6 | The guide said pi accepts a Claude Pro/Max subscription login. | Your notes say it doesn't run on the plan, and that is right in effect: Anthropic bills third-party harnesses separately. | GUIDE §B3 corrected; SHORT-LOOP §4 explains which agent for which billing. |
| 7 | The kit called you a beginner. | Your own notes say embedded systems engineer. | Corrected in the instructions the agents read (`/define`, the kit's AGENTS.md, the planning-chat text). |

Full argument for items 3–5: `docs/SHORT-LOOP.md` §8.

## Pass 3 (November 2026): bugs reproduced and fixed, switch to pi

The kit was checked again against your notes, this time by running it: the tool
tests, the host tests, the project generator, and the serial tool against a
simulated board. Four bugs showed up, and the harness changed.

| # | Finding | Why it matters | Change |
|---|---|---|---|
| 1 | `make loop PORT=/dev/ttyACM1` flashed that port, but boot-check, the on-board tests and the bench tests talked to whichever board was auto-detected. | With both boards plugged in you flash one and test the other, and the result looks green. | `PORT=` and the new `BOARD=R\|C` are passed to every step, including pytest. Covered by a test. |
| 2 | `T-TOUCH` could not fail. Touch detection falls back to "resistive" whenever no GT911 answers, and the test only failed for "none", which never happens. | A C board whose GT911 isn't detected looked exactly like a healthy R board. "Works on both boards" passed from one board's run. | Each board is registered once by its USB serial number (`esp_serial.py register R`). The self test is told which controller that board must have and fails on a mismatch. REQ-003 is now `T-TOUCH@R, T-TOUCH@C` and needs a run on each board. An unregistered board only passes on a positively detected GT911. |
| 3 | The "done" gate accepted stale results: break the code after a test run and `make trace RUN=1` still printed `TRACE:OK`. | That gate is what `/build-loop` relies on before ticking a plan item. | Every result is stamped with a fingerprint of its source. The firmware carries its own (`build=` in `info` and `selftest`), so a target or bench result is tied to what is really on the board. A mismatch shows as `STALE` and fails the gate. |
| 4 | `new-embedded-project` failed halfway when git had no name/email yet, left the folder behind, then refused to re-run. | A first-time user hits this on step one. | It checks before creating anything and says what to run. |
| 5 | The harness was Claude Code. You use **pi**. | Skills, the permission allowlist and the setup script didn't apply. | The slash commands are now pi prompt templates in `prompts/` (same names: `/define`, `/commission`, …). `CLAUDE.md` became `AGENTS.md`. The setup script installs pi. The Claude Code allowlist is gone, because pi never asks before running a command. |
| 6 | The guide said the worst case was "re-clone the project". | pi runs everything unprompted, the agent's account may manage the network (which includes reading saved Wi-Fi passwords), and a normal `gh` login reaches every repo you own. | GUIDE §6 rewritten around this. New steps: forget the home Wi-Fi on the dev box, use a GitHub token limited to chosen repos. `setup-root.sh` warns about saved Wi-Fi networks. The polkit rule itself is unchanged (narrowing it can't be tested without the T480s). |
| 7 | The install steps pointed at an empty default branch. | "Download ZIP" and `gh repo clone` fetched a blank README. | The kit is merged to `master`, and the guide uses the folder name GitHub's ZIP really has. |
| 8 | Smaller things | | New `make open-check` (see below). `device.wait_for()` for bench tests that wait for a state change. Commissioning no longer needs Ethernet for the template's own bench tests. `make ci-fw` no longer claims to need no toolchain. |

## Pass 2 (November 2026): traceability and sturdier checks

- `tools/trace.py` / `make trace`: FSD requirement → named test → last result.
- `T-BOOT` added (the FSD cited it but it didn't exist); baseline REQ-001…006.
- Serial tool: more crash signatures (S3 watchdog resets, task watchdog, asserts,
  stack overflows); boot-check keeps watching after `BOOT:OK`; a FAIL line can't
  be outvoted by the `DONE` count.
- GT911 reset-sequence fallback before assuming the resistive board.
- `make ci-fw`: flash the binaries GitHub CI built.
- `bench-wifi` hotspot no longer auto-starts after a reboot.

## Pass 1 (November 2026): the first version

Guide, template project, setup scripts, bench scripts and the workflow commands,
mapped from the three videos onto your two laptops and two boards.

## What still needs your hands

Nothing here has run on real hardware. In the order you will meet them:

1. **pi and the slash commands.** After `setup-user.sh`, start `pi` in a project
   and type `/` : `/start`, `/wrap`, `/define` and the others should be offered. If
   not, see troubleshooting.
2. **The serial tool against a real board.** Everything in the loop goes through
   it. `/commission` exercises it step by step; the first one may need fixes.
3. **`make open-check`.** On the ESP32-S3's built-in USB the DTR/RTS lines double
   as reset signals, and Linux toggles them when a port is opened. If that resets
   your board, the check says so (`OPENCHECK:RESETS`). Single commands still
   work then, but multi-step bench tests would lose device state between steps.
4. **R board**: `make loop BOARD=R`. If `T-BOOT` fails, look at `boot_ms=`. The 2 s
   USB wait in `setup()` counts toward it, so a value just under 3000 is plausible.
5. **C board**: `make loop BOARD=C`. `T-TOUCH` now fails if the GT911 isn't found.
   If the serial log says "GT911 answered after reset", the fallback was needed;
   record that in the board file.
6. **The resistive controller itself** can't be detected electrically. The
   corner-tap step in `/commission` is its only proof.
7. On the T480s: `bench-wifi up` / `down` and `bench-mqtt start` once by hand
   before trusting bench tests.

## Not changed, on purpose

- **No Wi-Fi/MQTT code in the template.** The first project that needs it writes
  it through `/define` → `/start`, with bench tests. The fixtures
  (`wifi_ap`, `mqtt_broker`, `device.wait_for`) are in place.
- **No ESP-IDF switch yet.** Arduino + arduino-cli is the right level for now.
- **The polkit rule is still broad** (all NetworkManager actions for `embdev`).
  The mitigation is procedural: no saved home Wi-Fi on the dev box.
- **`bench-mqtt` listens on all interfaces without a password.** It is a
  throw-away test broker, but anything on your home network can reach it while
  it runs. Stop it when you're done (`bench-mqtt stop`).
