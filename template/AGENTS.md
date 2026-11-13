# AGENTS.md: [project name]

Loaded in every session, by whichever agent runs here (pi reads this file; Claude Code reads it through `CLAUDE.md`). Keep it under ~120 lines: only facts that hold for the whole project. Detail lives in docs/, behind "Read only when needed".

## Project
- **What:** [one line, filled in by /define].
- **Boards:** two Guition JC4827W543 (ESP32-S3): one **R** (resistive XPT2046), one **C** (capacitive GT911). Code must work on both unless `docs/FSD.md` says otherwise.
- **Dev box:** you run on the ThinkPad T480s as user `embdev`. The boards are on its USB ports; its Wi-Fi, MQTT broker and Bluetooth are the test bench.

## Stack
- Arduino (arduino-esp32 core 3.x) built with arduino-cli. Use the make targets below; never improvise long arduino-cli lines.
- **Check:** `make check` (host tests + firmware compile).
- **Done gate:** `make trace RUN=1 REQS="<the task's REQ IDs>"` prints `TRACE:OK`. That means: each of those requirements names a test, the test exists, and it passed **on the current code**.
- **Run limit:** 10 runs of `make loop`, `make target-test` or `make bench-test` in one session without the task's tests passing. Then stop and report. `make host-test` doesn't count: it is cheap, run it often.
- **Push:** in /wrap. GitHub CI compiles every push; nothing is deployed. Pushing is not finishing: an item awaiting the owner's check is pushed unticked.

```
make host-test     # tier 1: logic on the PC, seconds
make compile       # build firmware
make loop          # host-test -> compile -> upload -> boot-check -> target-test
make target-test   # tier 2: on-board `selftest`
make bench-test    # tier 3: pytest with the real board + dev-box Wi-Fi/MQTT/BLE
make boot-check    # reset + verify clean boot
make info          # one-line device status        make monitor SECS=30
make trace         # FSD requirement -> test -> last result
make boards        # connected boards and which is registered as R / C
```
`BOARD=R` or `BOARD=C` (or `PORT=/dev/ttyACM1`) on any target picks the board. Use `BOARD=` whenever both are plugged in. Serial output of every tool call is appended to `build/serial.log`.

## Workflow: one task per session
- `/start <plan item or REQ IDs>` begins a session, `/wrap` ends it, then the owner clears the session. A fresh session must be able to continue from PROGRESS.md alone.
- A task is **one item of `docs/PLAN.md`**, not a whole phase. If an item doesn't fit one session, propose splitting it.
- Between the owner's OK and `/wrap` you work the item in a closed loop, without asking:
  1. Write or extend the tests first, at the fastest tier that can prove the requirement (host > target > bench). Pure logic goes in `firmware/src/logic/` so it can be host-tested.
  2. Implement.
  3. `make host-test` until green. Don't compile firmware while host tests fail.
  4. `make compile`. Fix errors and new warnings.
  5. `make upload && make boot-check && make target-test`, then `make bench-test` if the item has bench requirements. On a failure read the output and `build/serial.log`, form one hypothesis, add `Serial.printf("[subsystem] ...")` if unsure, fix, rerun.
  6. Run the Done gate. `STALE` means the source changed after that tier last ran: rerun the tier, don't argue with it.
- Stop and ask the owner when: a test needs a physical action (wiring, a board that isn't plugged in, a button); the same failure survives 3 different fixes; the Run limit is reached; a requirement is ambiguous, contradicts another, or you want to change the FSD (that is `/change-request`).
- **Flashing a board that drives something.** A bare board on USB may be flashed without asking. If FSD §3 says the board drives anything that can move, heat, switch mains or charge a battery (motor, relay, heater, pump, a load on a free pin), put "this session flashes the board" in the /start plan and flash only after the owner's OK for this session. The firmware must leave those outputs off at boot and during `selftest`.

## At /wrap also
- `python3 tools/trace.py --out docs/STATUS.md`, and name every row that is `STALE` or `NOT RUN` in your reply: those are not proven for the code being committed.
- Something true for the **board**, not just this project (a pin quirk, a library bug, a proven init sequence): show the owner the text and suggest adding it to `~/Embed_WF/hardware/boards/`.
- An item has **checks only the owner can do** if it covers a `field` or `manual` requirement or changes what is on the screen (no test can see the display). Such an item stays "awaiting my check" as /wrap describes: name each thing to look at on the real device, and what the owner should see.

## Read only when needed
| File | Read when |
|---|---|
| `docs/hardware/guition-jc4827w543.md` | before writing or changing any hardware code: pin map, proven init code, traps. Its §10 rules apply to you, whichever model you are |
| `docs/FSD.md` | starting a task: the rows of its REQ IDs, plus the section they refer to. It is the single source of truth |
| `docs/PLAN.md` | starting a task: its phase only |
| `docs/decisions.md` | a decision is questioned or about to change |
| `docs/history.md` | the owner asks what happened earlier, or a failure looks familiar |
| `datasheets/*.summary.md` | the task uses that part. Read the summary, not the PDF text |
| `docs/IDEA.md` | only in /define. It is the owner's text; don't edit it |

## Files
```
firmware/          Arduino sketch. src/logic = pure C++ (no Arduino.h), src/hal = drivers, src/app = console + selftest
test/host/         tier 1 tests, compiled with g++ on the PC
test/bench/        tier 3 pytest tests
tools/             esp_serial.py (non-interactive serial; never use an interactive monitor), trace.py
docs/              IDEA -> FSD (spec) -> PLAN (items); history, decisions; hardware/ board reference
datasheets/        PDFs, extracted text, summaries
build/             results and logs (gitignored)
```

## Rules
- The FSD is the boss. If code and FSD disagree, ask; don't silently change either.
- Never weaken, skip or delete a test to get green. If a test is wrong, say why and ask.
- Never edit files under `build/`, and never write a result log or `build_id.h` by hand. They are evidence; only the make targets produce them.
- Every target test has a stable ID (`T-XXXX`), printed as `TEST:<id>:PASS|FAIL:<detail>` and named in the FSD's Test column, as are host test names and bench test functions: `make trace` only counts tests the FSD names. A target test that must hold on both boards is written `T-XXXX@R, T-XXXX@C`.
- A test must be able to fail. Break the code once (or reason it through) before trusting a new test.
- Bench tests that wait for a change use `device.wait_for(...)`, not a single `device.command(..., until=...)`.
- Keep `src/logic/` free of Arduino and ESP-IDF headers.
- Credentials only in the git-ignored `firmware/src/secrets.h`, and only the throw-away bench ones. Never test against the owner's home Wi-Fi or real MQTT broker: use `bench-wifi` / `bench-mqtt`.
- No `sudo`. If something needs root, give the owner the exact command. Stay inside this project folder. Never force-push.
- Board unresponsive after flashing: tell the owner to hold BOOT, tap RESET, release BOOT, then `make upload`.
