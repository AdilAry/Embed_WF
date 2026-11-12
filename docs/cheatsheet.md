# Cheat sheet

## Connect

```bash
ssh embdev@<t480s-ip>
```

```bash
tmux new -s work        # or: tmux attach -t work
```

VS Code: `F1` → *Remote-SSH: Connect to Host* → open `~/projects/<name>`.

## The short loop (every session, any project)

| Step | Type | Your part |
|---|---|---|
| Begin one task | `/start` (takes "Next" from PROGRESS.md), or `/start REQ-010`, `/start fix the export` | read the 5-bullet plan and its **done when**; correct it or say OK |
| Work | nothing: the agent loops on its own until "done when" passes | answer when it stops and asks |
| End | `/wrap` | check what it tells you to check |
| Next task | `/new`, then `/start` | |
| Fresh-eyes review | `/judge` in a **new** session (`/judge final` at the end) | pick which issues get fixed |

Around 40% context: finish the step and `/wrap`. Wrong path: go back (`/tree`) instead of correcting.

## Project lifecycle (embedded)

| Step | Type |
|---|---|
| New project | `new-embedded-project <name>` in the shell, or `/new-project <name>` |
| Idea → spec → plan | write `docs/IDEA.md`, then `/define`, then `/wrap` |
| Prove the setup | `/commission`, then `/wrap` |
| Build one plan item | `/start` … `/wrap` |
| Add a part | put the PDF in `datasheets/`, then `/datasheet <file>.pdf` |
| Change something | `/change-request <what>`, `/wrap`, then `/start` on the new item |
| Any other software project | `new-project <name>` in the shell (see SHORT-LOOP.md) |
| Resume last session | `pi -c` (latest) or `pi -r` (pick one) |

## make targets (in a project)

```
make host-test     tier 1 (seconds)
make compile       build firmware
make check         host-test + compile (= CI)
make upload        flash
make boot-check    reset + verify clean boot
make target-test   tier 2, on-board selftest
make bench-test    tier 3, pytest
make loop          host → compile → upload → boot-check → target
make info          one-line device status
make monitor SECS=30
make trace         requirement -> test -> last result table (STALE = passed on older code)
make trace RUN=1 REQS="REQ-010 REQ-020"   must say TRACE:OK before ticking a plan item
make ci-fw         download the firmware CI built for this commit (then make upload)
make boards        connected boards, and which is registered as R / C
make open-check    does opening the serial port reset the board? (must say OPENCHECK:OK)

Any target takes BOARD=R or BOARD=C (or PORT=/dev/ttyACM1): make loop BOARD=C
```

## Serial console (115200 baud)

`help` · `ping` · `info` · `selftest` · `text <msg>` · `bl <0-255>` · `touch` · `reboot`

```bash
python3 tools/esp_serial.py cmd text Hello there
```

```bash
python3 tools/esp_serial.py monitor -s 30 --expect "Wi-Fi connected"
```

## Bench

```
bench-wifi up | down | status | clients | channel 11
bench-mqtt start | stop | status | sub '#' | pub topic msg
bench-ble-scan [--name X] [-s 10]
```

## Prompts that work well (plain words are fine)

- "/start" and then, to the plan it proposes: "OK, but do the parser test first."
- "The display flickers when the temperature updates. Add debugging, find out why, fix it."
- "Add a host test for the case where the sensor returns 0xFFFF."
- "Explain what `src/hal/touch.cpp` does, briefly."
- "What would you test that the FSD doesn't cover yet?"
- "Show me `make trace` and explain every line that isn't PASS."
- "Break the wrap logic on purpose and show me the test catches it, then undo it."
- "Update the docs, commit and push."

## pi keys / commands

`Esc` stop the agent · `/new` new topic · `/resume` older session · `/session` tokens + cost ·
`/compact` shrink context · `/model` (Ctrl+L) switch model · `/reload` re-read prompts · `/hotkeys` · `/quit`
