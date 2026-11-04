# Review of the Embed_WF pipeline (November 2026)

The pipeline under review is the first version on branch
`claude/pensive-knuth-wgzlag`. I checked it against your notes on the three
videos, your two laptops and your Guition boards. This branch
(`claude/happy-hamilton-x60pej`) builds on it. Nothing was thrown away.

## Verdict: keep it, it's worth building on

It already does what video 3 calls a *harness*: spec → tests → build → flash →
observe → fix, with the agent safely boxed in. The parts that matter most are
done well:

- **Right machine split.** Agent and bench on the spare T480s as an
  unprivileged `embdev` user, and you supervising from the Legion. This replaces
  the video's Proxmox VM + Raspberry Pi with hardware you already own. The T480s
  has real USB, Wi-Fi, Bluetooth and Ethernet, so it can be dev box **and** bench.
- **A template that actually runs.** Display, R/C touch auto-detect, and a serial
  console with `selftest` are the "firmware hooks" the videos talk about. It
  starts from your proven VirtualPetNetSec code, not from guesswork.
- **Four test tiers with a parseable output contract** (`HOSTTEST:` / `TEST:` /
  pytest), all behind `make`, so the agent gets objective pass/fail.
- **Skills mirroring the videos** (`/define` ≈ video 3's /define, the template ≈
  /harness, `/commission`, `/build-loop` ≈ /build, `/change-request`), with sensible
  guard rails: a 3-attempt budget, never weakening tests, and stopping for anything
  physical.
- **CI was green** on its first push: host tests pass and the firmware compiles
  with the pinned core 3.3.10 and Arduino_GFX 1.6.8.

## What was missing or wrong, and what this branch changes

| # | Finding | Why it matters | Change |
|---|---|---|---|
| 1 | No link from requirement to evidence. Nothing checked that each FSD requirement has a test, or whether that test passed. | That link is video 3's main point ("every requirement says how it will be proven"). Without it, "done" is the agent's opinion. | New `tools/trace.py` / `make trace`. The make targets keep each tier's last result in `build/`. `/build-loop` needs `TRACE:OK` for a plan item's REQs before ticking it, `/wrap-up` writes `docs/STATUS.md`, and project CI puts the table on the run's summary page. |
| 2 | The FSD template's REQ-001 pointed at test `T-BOOT`, which didn't exist. (`make trace` found it on its first run.) | A spec that cites a missing test teaches the agent that's OK. | Added `T-BOOT` (setup must finish in < 3 s, boot time also printed on the `BOOT:OK` line). The template FSD now lists baseline REQ-001…006 for everything the template's tests prove, and CI enforces that the template stays fully traceable. |
| 3 | The serial tool's crash detector missed common S3 watchdog resets (`TG0WDT_SYS_RST`, `TG1WDT_SYS_RST`), task-watchdog messages, failed asserts and stack overflows. | A crash the tool doesn't recognise looks like a quiet, healthy board to the agent. | Broader crash patterns, covered by unit tests. |
| 4 | `make boot-check` passed as soon as `BOOT:OK` appeared. | Firmware that boots, prints OK, then crashes 2 s later (typically when Wi-Fi starts) was reported as a clean boot. | After a good boot it keeps listening (default 4 s) for a crash or a reboot. |
| 5 | A FAIL line could be outvoted: selftest trusted the `SELFTEST:DONE fail=0` count over the `TEST:…:FAIL` lines it had just seen. | A counting bug in firmware would show as green. | Any FAIL line now makes the run fail. |
| 6 | GT911 (C board) detection relied on the chip answering without a reset. | If the C board's touch controller doesn't come up on its own, the code would silently fall back to the resistive driver. | If the first probe fails, the firmware runs the GT911 datasheet reset sequence (address 0x5D) and probes again. This is harmless on the R board (explained in `touch.cpp`). **Still unverified on your C board.** |
| 7 | The permission allowlist included `cat`, `grep`, `ls`. | `cat firmware/src/secrets.h` would bypass the "don't read secrets" rule, and Claude Code doesn't need these anyway (it has its own read and search tools). | Removed. Added read-only `gh run …` commands so the agent can check CI without asking. GUIDE §6 now says plainly that the allowlist is convenience and `embdev` is the security boundary. |
| 8 | The guide didn't use the app you actually use: Claude Desktop. | Your daily tool should be part of the flow. | New `docs/claude-desktop-project.md` (project instructions plus the hand-over between chat and Claude Code). GUIDE covers Claude Desktop's Code tab over SSH to the T480s, and Remote Control for checking in from your phone while you're out on a job. |
| 9 | Video 3's "let GitHub compile" wasn't usable from the bench. | It's useful when the T480s is busy, and essential later for ESP-IDF. | `make ci-fw` downloads the CI-built binaries for the current commit, then you run `make upload`. |
| 10 | Windows 10 status was out of date. | The free EU extended-update year ended in October 2026, so the Legion is unpatched. Its i5-9300H qualifies for Windows 11. | `hardware/machines.md` and GUIDE updated with this. Not part of the pipeline, but worth doing. |
| 11 | Small things | | The `bench-wifi` hotspot no longer auto-starts after a reboot. Stale `setup.sh` references fixed. The serial tool's helpers can now be imported without pyserial, so they're unit-tested in CI (`tests/`). |

## What I could not verify (needs your hands)

Nothing here has touched your real boards. On your first `/commission`:

1. **R board**: `make loop`. T-BOOT is new. If it fails, look at the `boot_ms=`
   value. The 2 s USB wait in `setup()` counts toward it, so a value just under
   3000 is plausible. If it's over, tell Claude whether 3 s is really what you want.
2. **C board**: is it detected as `gt911`? If the serial log says "GT911 answered
   after reset", the new fallback was needed. Record that in the board file.
3. `make boot-check` on both boards. The new settle window must not trip on a
   healthy board.
4. On the T480s: `bench-wifi up` / `down` and `bench-mqtt start` once by hand
   before trusting bench tests.

## Not changed, on purpose

- **No Wi-Fi/MQTT code in the template.** Adding untested network code to every
  project would make the starting point less trustworthy. The first project that
  needs it writes it through `/define` → `/build-loop`, with bench tests. The
  fixtures for that (`wifi_ap`, `mqtt_broker`) are already in place.
- **No ESP-IDF switch yet.** Arduino + arduino-cli is the right level for now
  (video 1's level 10 is "later"). `make ci-fw` is the first step toward it.
- **The polkit rule is broad** (all NetworkManager actions for `embdev`).
  Narrowing it to just the hotspot actions is possible, but I can't test it here.
  On a spare machine the risk is "the agent could mess up the network settings",
  which you can undo.

## Suggested next steps for you

1. Set up the T480s (GUIDE §4). Allow an evening.
2. `new-embedded-project hello-board`, then `/commission` with the R board, then the
   C board. Read `make trace` at the end: REQ-001…005 should show PASS.
3. Pick a small first real project with one external part (a desk clock with a
   temperature sensor is a good one), so `/datasheet`, host tests and target tests
   all get used once.
4. The first project that uses Wi-Fi is where the bench (video 3's real power)
   comes in: captive portal, Wi-Fi loss and broker-down tests.
