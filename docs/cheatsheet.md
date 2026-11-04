# Cheat sheet

## Connect

```bash
ssh embdev@<t480s-ip>
```

```bash
tmux new -s work        # or: tmux attach -t work
```

VS Code: `F1` → *Remote-SSH: Connect to Host* → open `~/projects/<name>`.

## Project lifecycle (in Claude Code)

| Step | Type |
|---|---|
| New project | `new-embedded-project <name>` in the shell, or `/new-project <name>` |
| Idea → spec → plan | write `docs/IDEA.md`, then `/define` |
| Prove the setup | `/commission` |
| Build the next phase | `/build-loop` |
| Add a part | put the PDF in `datasheets/`, then `/datasheet <file>.pdf` |
| Change something | `/change-request <what>` |
| End of session | `/wrap-up` |
| Resume last session | `claude --continue` |

## make targets (in a project)

```
make host-test     tier 1 (seconds)
make compile       build firmware
make check         host-test + compile (= CI)
make upload        flash (PORT=/dev/ttyACM1 to choose)
make boot-check    reset + verify clean boot
make target-test   tier 2, on-board selftest
make bench-test    tier 3, pytest
make loop          host → compile → upload → boot-check → target
make info          one-line device status
make monitor SECS=30
make trace         requirement -> test -> last result table
make trace RUN=1 REQS="REQ-010 REQ-020"   must say TRACE:OK before ticking a plan item
make ci-fw         download the firmware CI built for this commit (then make upload)
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

- "Implement phase 2 from the plan."
- "The display flickers when the temperature updates. Add debugging, find out why, fix it."
- "Add a host test for the case where the sensor returns 0xFFFF."
- "Explain what `src/hal/touch.cpp` does like I'm new to embedded."
- "What would you test that the FSD doesn't cover yet?"
- "Show me `make trace` and explain every line that isn't PASS."
- "Break the wrap logic on purpose and show me the test catches it, then undo it."
- "Update the docs, commit and push."

## Claude Code keys / commands

`Esc` stop · `Esc Esc` rewind · `Shift+Tab` cycle permission mode · `/clear` new topic ·
`/compact` shrink context · `/model` switch model · `/help`
