---
description: Verify the toolchain, the connected ESP32 board(s), the serial link, the dev-box test bench and CI before feature work starts, so later failures can be blamed on the firmware and not the setup. Use once per project (Phase 0 of docs/PLAN.md) or after changing hardware/wiring.
---

# /commission — prove the bench before trusting it

Work through Phase 0 of `docs/PLAN.md`. Report each step as ✅ / ❌ with the evidence (command +
key output line). Stop at the first ❌ you can't fix in software and tell the owner exactly what
to do physically.

1. **Toolchain**: `arduino-cli version`, `arduino-cli core list` (esp32 present at the version in
   the Makefile), `arduino-cli lib list` (GFX Library for Arduino). If missing: `make deps`.
2. **Host tests**: `make host-test`.
3. **Compile**: `make compile`. Keep the binary size from `make size` for the history entry.
4. **Board connected**: `make boards`. Expect a `303A:1001` (Espressif USB) device. If nothing:
   ask the owner to check the USB-C cable is a *data* cable, try another port, and that `id`
   shows the `dialout` group (log out/in after setup).
5. **Which board is it?** If `make boards` shows `board=-`, ask the owner whether the plugged-in
   board is the **R** (resistive, soft plastic screen) or the **C** (capacitive, glass). With only
   that board plugged in, run `python3 tools/esp_serial.py register R` (or `C`). This is needed
   once per board per dev box. From then on the tools know which touch controller to expect, and
   `BOARD=R` / `BOARD=C` picks a board when both are plugged in.
6. **Flash + boot**: `make upload` then `make boot-check`. If upload fails to connect, ask the owner
   for the BOOT/RESET sequence (hold BOOT, tap RESET, release BOOT) and retry once.
7. **Serial link**: `make open-check`. It must print `OPENCHECK:OK`. If it prints
   `OPENCHECK:RESETS`, opening the serial port restarts the board: stop, tell the owner, and note
   it under "Broken" in `PROGRESS.md` (see "Board restarts when the port is opened" in the Embed_WF
   troubleshooting page). Single commands still work, but multi-step bench tests can't be trusted
   until that is fixed.
8. **Target tests**: `make target-test`. All must pass, including `T-BOOT` (setup done in < 3 s)
   and `T-TOUCH` (the detected touch controller is the one this board must have). Record the
   `make info` line.
9. **Second board**: ask the owner to plug in the other board (it may stay plugged in next to the
   first one), register it (step 5), then repeat 6–8 with `BOARD=<its letter>` on every make
   command. The GT911 (C) code is unverified — if `T-TOUCH` fails on C or touch coordinates are
   wrong, fix it now, keep what you learned for the history entry and suggest copying it into the
   board file.
10. **Touch sanity (manual)**: ask the owner to tap the four corners while you run
    `make monitor SECS=20`; check `[touch] press x=.. y=..` values are near the corners. For R,
    update the XPT_* calibration in `firmware/src/config.h` from the raw values (`touch` command).
    This is the only check that proves the resistive controller really works.
11. **Bench**: `make bench-test`. The template's own bench tests only need the USB cable. Bring up
    the rest only if the FSD has Wi-Fi / MQTT / BLE requirements: `bench-wifi up` (Ethernet must be
    connected — the script refuses otherwise), `bench-mqtt start`, `bench-ble-scan -s 5`.
12. **Traceability**: `make trace RUN=1`. The baseline requirements REQ-001…006 must show `PASS`
    and the last line must be `TRACE:OK`. REQ-003 needs a target-test run on **both** boards.
    `STALE` means the code changed after that tier last ran: run `make loop` (and
    `make bench-test`) again.
13. **CI**: if the repo is on GitHub, `git push` (ask first) and check with `gh run list -L 1` /
    `gh run watch` that the `firmware` workflow is green.

Finish: tick the Phase 0 items in `docs/PLAN.md` that passed. Then tell the owner the result in
5 lines or fewer and to type `/wrap`, which writes the commissioning entry (binary size, the
`make info` line of each board, anything learned) to `docs/history.md` and sets the next step
in `PROGRESS.md`: `/start` on the first item of Phase 1.
