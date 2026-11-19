# Testing: four tiers, fastest first

Video 3's main point: **the AI needs objective feedback**. A test that prints PASS
or FAIL is something an agent can act on. "Looks fine to me" is not. This page
explains how the template gives it that feedback.

## The rule

> Prove each requirement at the **fastest tier that can prove it**. Run the tiers
> in order, and don't start a slower tier while a faster one is red.

| Tier | Command | Where it runs | Time | Proves |
|---|---|---|---|---|
| 1 host | `make host-test` | PC (g++) | < 1 s | logic: parsing, formatting, maths, state machines, protocol decoding |
| 2 target | `make target-test` | ESP32 (`selftest` command) | 1–2 min incl. compile + flash | the hardware-dependent parts work on the chip: PSRAM, flash size, NVS, display init, touch controller |
| 3 bench | `make bench-test` | ESP32 + dev box (pytest) | minutes | behaviour with the outside world: Wi-Fi join/loss, MQTT, BLE, captive portal, fault injection |
| 4 field / manual | checklist in FSD §8 | the real world | — | end-to-end in the real place; anything only a human can judge |

`make loop` = host → compile → upload → boot-check → target, stopping at the first failure.

## Tier 1 — host tests

- The code under test lives in `firmware/src/logic/` and **must not include
  `Arduino.h`** or ESP-IDF headers. Then it compiles with plain `g++` on the PC.
- Tests are in `test/host/test_main.cpp`, using a tiny built-in framework
  (`test/host/mini_test.h`): `TEST(name) { CHECK(...); CHECK_EQ(a, b); }`.
- Output: `HOSTTEST:<name>:PASS|FAIL`, and `HOSTTEST:DONE pass=N fail=M`.
- **Design consequence:** keep "decide what to do" (pure logic, host-testable)
  separate from "do it to the hardware" (hal). Example: a sensor driver has
  `logic/bme280_math.cpp` (compensation formulas from the datasheet, tested with
  the datasheet's example values) and `hal/bme280.cpp` (the I2C reads).

When the agent writes host tests, check the expected values yourself sometimes.
A test the agent wrote to match its own buggy code proves nothing. (While
building this template, the first host run caught a wrong expectation in a
test. That's the system working.)

## Tier 2 — target tests

- The firmware has a serial console. Its `selftest` command runs
  `firmware/src/app/selftest.cpp` and prints one line per test:
  ```
  SELFTEST:BEGIN build=85560f84830a
  TEST:T-PSRAM:PASS:psram=8388608
  TEST:T-TOUCH:PASS:type=gt911 expected=gt911
  SELFTEST:DONE pass=7 fail=0
  ```
- `tools/esp_serial.py selftest` sends the command, parses the lines, and exits
  0 or 1. It also exits with an error if it sees a crash signature (`Guru
  Meditation`, `Backtrace:`, a watchdog or brownout reset).
- `make boot-check` resets the board and confirms a clean boot. If it misses the
  `BOOT:OK` line (the S3's USB port drops out during reset), it asks the device
  for `info` and checks that the last reset reason wasn't a panic or watchdog.
  Either way it then keeps listening for a few seconds (`--settle`, default 4 s).
  A firmware that crashes or reboots right after printing `BOOT:OK` (for
  example when Wi-Fi starts) counts as a failed boot, not a green one.
- Add one `report("T-XXXX", ok, "...")` per target-tier requirement and put the
  ID in the FSD's Test column.

Why a console instead of a separate test firmware? It's the same binary you
ship, so you're testing the real thing. The console also stays useful for
debugging by hand (`help` at 115200 baud in any serial monitor).

## Tier 3 — bench tests

pytest files in `test/bench/`. Fixtures in `conftest.py` give each test:

- `device`: send console commands, read `info`, and `device.wait_for(cmd, pattern)` to
  ask again until the answer matches (skips if no board is connected)
- `wifi_ap`: the test hotspot `embtest` on the dev box, brought up for the test
  and torn down after (the dev box is `10.42.0.1` on it)
- `mqtt_broker`: a private Mosquitto on the dev box, which the test may stop to
  simulate an outage

Example fault-injection test (in `test_smoke.py`, commented until your firmware has Wi-Fi):

```python
def test_req_020_reconnects_after_wifi_loss(device, wifi_ap):
    device.wait_for("wifi status", "^WIFI connected", timeout=30)
    subprocess.run(["bench-wifi", "down"], check=True)
    device.wait_for("wifi status", "^WIFI disconnected", timeout=15)
    subprocess.run(["bench-wifi", "up"], check=True)
    device.wait_for("wifi status", "^WIFI connected", timeout=30)
```

Pattern: **the firmware exposes its state through console commands** (`wifi status`,
`mqtt status`, `sensor read` …) so tests can observe it, and **the bench changes
the world** around it.

Other things the T480s bench can do:

| Want to test | How |
|---|---|
| Captive portal | the dev box joins the ESP32's AP with `nmcli dev wifi connect <esp-ap>`, then submits the form with `curl` (or Python `requests`) |
| Wrong Wi-Fi password | flash with a wrong `secrets.h`, or change the hotspot password with `BENCH_WIFI_PASS=… bench-wifi up` |
| Channel change | `bench-wifi channel 11` |
| MQTT payloads | `bench-mqtt sub 'mydevice/#'`, `bench-mqtt pub mydevice/cmd reboot` |
| Broker outage | `bench-mqtt stop` … `bench-mqtt start` |
| BLE advertising | `bench-ble-scan --name MyDevice` |
| GPIO / buttons | not available on a laptop; use a second ESP32 as a "stimulus board" over USB serial, or a Pi later |

## Traceability: which requirement is proven by what

`make trace` (`tools/trace.py`) joins the three things that matter:

1. the FSD's requirements table (`REQ-xxx`, tier, test names),
2. the tests that actually exist (`TEST(name)` in `test/host/`, `report("T-XXX")`
   in the firmware, `def test_xxx` in `test/bench/`),
3. the last result of each tier, which the make targets save in `build/`
   (`host-test.log`, `target-test.log`, `bench-test.xml`).

| Status | Meaning | What to do |
|---|---|---|
| PASS | every test for it passed on its last run | nothing |
| FAIL | at least one of its tests failed last time | fix the code (or, with your OK, the test/FSD) |
| NOT RUN | tests exist but haven't run on this machine (board not connected?) | run that tier |
| SKIPPED | bench test skipped (no board, no hotspot) | fix the bench, rerun |
| NO TEST | the FSD names a test that doesn't exist | write it; this is the to-do list |
| MANUAL | field/manual tier | your checklist in FSD §8 |
| STALE | the tests passed, but on **older code** than what is in the folder now | rerun that tier (`make host-test`, `make loop`, `make bench-test`) |

`make trace` alone only reports. `STRICT=1` fails on NO TEST or FAIL (CI uses this
for the template). `RUN=1 REQS="REQ-010 REQ-020"` also fails on NOT RUN, SKIPPED
and STALE. That is the **Done gate**: `/start` names it in the plan, and `/wrap` runs it before a plan item is ticked.

### How a result is tied to the code

A PASS only counts for the code it was produced from:

- **host**: `make host-test` writes a fingerprint of `firmware/src/logic` and
  `test/host` into its log. Change either and the old result is STALE.
- **target**: `make compile` bakes a fingerprint of the whole `firmware/` folder
  into the firmware (`FW_BUILD_ID`). The board prints it in `selftest` and
  `info`, so the result says what was *really on the board*, whichever machine
  or board it was. Edit the firmware without re-flashing and it is STALE.
- **bench**: `make bench-test` records the board's build id and a fingerprint of
  `test/bench`.

Documentation, the FSD and `PLAN.md` are not part of any fingerprint, so ticking
a plan item doesn't make anything stale.

### Two boards

Register each board once (`python3 tools/esp_serial.py register R`, or `C`;
`/commission` does it). The registration is the USB serial number of the board,
kept in `~/.config/embwf/boards` on the dev box. After that:

- `make loop BOARD=C` flashes and tests the C board, even with both plugged in.
- The self test is told which touch controller the board must have, so a C
  board whose GT911 isn't detected **fails** `T-TOUCH` instead of quietly
  running as an R board.
- Each registered board keeps its own result (`build/target-test.R.log`,
  `.C.log`). Write a test as `T-XXX@R, T-XXX@C` in the FSD to demand a pass on
  both. The template does this for REQ-003.

Known limits, so you're not misled by green:
- The resistive controller (XPT2046) can't be detected electrically. `T-TOUCH`
  on the R board proves "no GT911 answered and this is the board we expected",
  not "the resistive touch works". The corner-tap step in `/commission` does that.
- A PASS is only as good as the test. Now and then, ask the agent to break the
  code on purpose and show you the test going red.

## Tier 4 — field and manual

Some things only you can judge: brightness, readability, touch feel, a sensor
in its real spot. List them in FSD §8 as a checklist. `/wrap` reminds you
of the ones belonging to the item just finished.

## Regression for free

Once tests exist, `make loop && make bench-test` re-checks **everything** after
every change. Video 3 makes this point: you'd never re-test by hand that
thoroughly. Now it's one command, and CI runs tier 1 plus the compile on every
push.
