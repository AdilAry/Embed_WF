# AGENTS.md — project instructions for the AI agent

The agent (pi) loads this file automatically at the start of every session in
this folder. Keep it short and true. Project facts live in `docs/`.

## The board

**Before you write or change any hardware code, read
`docs/hardware/guition-jc4827w543.md` in full.** It is the pin map, the proven
init code and the known traps for this board. Its §10 "Rules for Claude on this
board" are rules for you, whichever model you are.

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
| `tools/trace.py` | Requirement → test → result table behind `make trace`. |

## Commands (always use these, never improvise long arduino-cli lines)

```
make host-test     # tier 1, seconds
make compile       # build firmware
make upload        # flash
make boot-check    # reset + verify clean boot (exit != 0 on panic/watchdog)
make target-test   # tier 2, on-board `selftest`
make bench-test    # tier 3, pytest
make loop          # host-test -> compile -> upload -> boot-check -> target-test
make info          # one-line device status
make monitor SECS=30
make trace         # FSD requirement -> test -> last result (RUN=1 REQS="REQ-010 ..." to enforce)
make boards        # connected boards and which is registered as R / C
make open-check    # prove that opening the serial port does not reset the board
make ci-fw         # fetch the firmware GitHub CI built for HEAD, then `make upload`
```

Which board a command talks to: `BOARD=R` or `BOARD=C` (a registered board),
or `PORT=/dev/ttyACM1`, on **any** of the targets above. Without either, it is
the first board found. Use `BOARD=` whenever two boards are plugged in.

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
7. When green: run `make trace RUN=1 REQS="<the item's REQ IDs>"`. It must print
   `TRACE:OK`: each of those requirements has a test, and that test passed **on the
   current code**. `STALE` means the source changed after the tier last ran; rerun the tier.
   Then tick the item in `docs/PLAN.md`, note anything surprising in
   `docs/NOTES.md`, and `git commit` with a message naming the requirement IDs.
8. Stop and ask the owner if: a requirement is ambiguous or contradicts another,
   a test needs physical action (press a button, swap a cable, change board),
   the same failure survives 3 different fix attempts, or you want to change the FSD.

## Rules

- The FSD is the boss. If code and FSD disagree, ask; don't silently change either.
- Never weaken, skip, or delete a test to make the loop green. If a test is wrong, say why and ask.
- Never edit files under `build/`, and never write a result log or `build_id.h` by hand.
  They are evidence. Only the make targets produce them.
- Every new target test gets a stable ID (`T-XXXX`) printed as `TEST:<id>:PASS|FAIL:<detail>`
  and is referenced from the FSD Test column. Same for host test names and bench test
  functions: `make trace` only counts tests the FSD names. If a target test must hold on
  both boards, write it as `T-XXXX@R, T-XXXX@C` in the FSD.
- A test must be able to fail. Check it by breaking the code once (or reasoning it through)
  before trusting a new test; a test written to match buggy code proves nothing.
- Bench tests that wait for something to change use `device.wait_for(...)` (it asks again
  until the answer matches), not a single `device.command(..., until=...)`.
- You run every command without asking the owner first. That is deliberate, and it is why
  you live in the unprivileged `embdev` account on a spare machine. Stay inside this
  project folder, and don't touch network settings beyond `bench-wifi`.
- Keep `src/logic/` free of Arduino/ESP-IDF headers.
- Never put credentials in tracked files. Use `firmware/src/secrets.h` (git-ignored), and
  only ever put the throw-away bench credentials in it.
- Never test against the owner's home Wi-Fi or production MQTT. Use `bench-wifi` / `bench-mqtt`.
- Don't run `sudo`. If something needs root, tell the owner the exact command.
- `git push` only when the owner asks (or at the end of a `/wrap-up`). Never force-push.
- Board unresponsive after flashing? Tell the owner: hold BOOT, tap RESET, release BOOT, then `make upload`.
