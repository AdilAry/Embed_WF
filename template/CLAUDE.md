# CLAUDE.md — project instructions for the AI agent

This file is loaded automatically at the start of every Claude Code session in
this folder. Keep it short and true. Project facts live in `docs/`.

## The board

@docs/hardware/guition-jc4827w543.md

The owner has **two boards: one R (resistive XPT2046) and one C (capacitive GT911)**.
Code must work on both unless `docs/FSD.md` says otherwise.

## Where things are

| Path | What |
|---|---|
| `docs/IDEA.md` | The owner's rough idea in plain words. Read-only for you unless asked. |
| `docs/FSD.md` | Functional Specification. **Single source of truth.** Every requirement has an ID and a verification tier. |
| `docs/PLAN.md` | Implementation phases and their status. You keep this up to date. |
| `docs/NOTES.md` | Findings, decisions, gotchas discovered while working (append, dated). |
| `datasheets/` | PDFs and their extracted `.txt` / summaries. Read the summary first. |
| `firmware/` | Arduino sketch. `src/logic` = pure C++ (no Arduino.h!), `src/hal` = drivers, `src/app` = console + selftest. |
| `test/host/` | Tier 1 tests, compiled with g++ on the PC. |
| `test/bench/` | Tier 3 pytest tests using the real board + dev-box Wi-Fi/MQTT/BLE. |
| `tools/esp_serial.py` | Non-interactive serial tool. Never use an interactive monitor. |

## Commands (always use these, never improvise long arduino-cli lines)

```
make host-test     # tier 1, seconds
make compile       # build firmware
make upload        # flash (auto-detects port)
make boot-check    # reset + verify clean boot (exit != 0 on panic/watchdog)
make target-test   # tier 2, on-board `selftest`
make bench-test    # tier 3, pytest
make loop          # host-test -> compile -> upload -> boot-check -> target-test
make info          # one-line device status
make monitor SECS=30
```

Serial output from every tool call is appended to `build/serial.log`.

## The development loop (follow it every time)

1. Pick the next unchecked item in `docs/PLAN.md`. Re-read the FSD requirements it covers.
2. Write/extend tests **first** at the fastest tier that can prove the requirement
   (host > target > bench). Pure logic goes in `firmware/src/logic/` so it can be host-tested.
3. Implement.
4. Run `make host-test`. Fix until green. Do not compile firmware while host tests fail.
5. Run `make compile`. Fix all errors and new warnings.
6. If a board is connected: `make upload && make boot-check && make target-test`, then
   `make bench-test` if the phase needs it. Read failures, add debug output
   (`Serial.printf("[subsystem] ...")`) if the cause is unclear, fix, repeat.
7. When green: tick the item in `docs/PLAN.md`, note anything surprising in
   `docs/NOTES.md`, and `git commit` with a message naming the requirement IDs.
8. Stop and ask the owner if: a requirement is ambiguous or contradicts another,
   a test needs physical action (press a button, swap a cable, change board),
   the same failure survives 3 different fix attempts, or you want to change the FSD.

## Rules

- The FSD is the boss. If code and FSD disagree, ask; don't silently change either.
- Never weaken, skip, or delete a test to make the loop green. If a test is wrong, say why and ask.
- Follow §10 "Rules for Claude on this board" in the board file.
- Every new target test gets a stable ID (`T-XXXX`) printed as `TEST:<id>:PASS|FAIL:<detail>`
  and is referenced from the FSD verification column.
- Keep `src/logic/` free of Arduino/ESP-IDF headers.
- Never put credentials in tracked files. Use `firmware/src/secrets.h` (git-ignored).
- Never test against the owner's home Wi-Fi or production MQTT. Use `bench-wifi` / `bench-mqtt`.
- Don't run `sudo`. If something needs root, tell the owner the exact command.
- `git push` only when the owner asks (or at the end of a `/wrap-up`).
- Board unresponsive after flashing? Tell the owner: hold BOOT, tap RESET, release BOOT, then `make upload`.
