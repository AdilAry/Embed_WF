---
name: commission
description: Verify the toolchain, the connected ESP32 board(s), the dev-box test bench and CI before feature work starts, so later failures can be blamed on the firmware and not the setup. Use once per project (Phase 0 of docs/PLAN.md) or after changing hardware/wiring.
---

# /commission — prove the bench before trusting it

Work through Phase 0 of `docs/PLAN.md`. Report each step as ✅ / ❌ with the evidence (command +
key output line). Stop at the first ❌ you can't fix in software and tell the owner exactly what
to do physically.

1. **Toolchain**: `arduino-cli version`, `arduino-cli core list` (esp32 present at the version in
   the Makefile), `arduino-cli lib list` (GFX Library for Arduino). If missing: `make deps`.
2. **Host tests**: `make host-test`.
3. **Compile**: `make compile`. Note the binary size from `make size` in `docs/NOTES.md`.
4. **Board connected**: `python3 tools/esp_serial.py list`. Expect a `303A:1001` (Espressif USB)
   device. If nothing: ask the owner to check the USB-C cable is a *data* cable, try another port,
   and that `id` shows the `dialout` group (log out/in after setup).
5. **Flash + boot**: `make upload` then `make boot-check`. If upload fails to connect, ask the owner
   for the BOOT/RESET sequence (hold BOOT, tap RESET, release BOOT) and retry once.
6. **Target tests**: `make target-test`. All must pass. Record the `info` line (`make info`),
   especially `touch=` — it tells you which variant (R = xpt2046, C = gt911) is plugged in.
7. **Second variant**: ask the owner to swap to the other board (R ↔ C), then repeat 5–6.
   The GT911 (C) code is unverified — if T-TOUCH or touch coordinates are wrong on C, fix it now
   and record what you learned in `docs/NOTES.md` and suggest copying it into the board file.
8. **Touch sanity (manual)**: ask the owner to tap the four corners while you run
   `make monitor SECS=20`; check `[touch] press x=.. y=..` values are near the corners. For R,
   update the XPT_* calibration in `firmware/src/config.h` from the raw values (`touch` command).
9. **Bench** (only if the FSD has `bench` requirements): `bench-wifi status`/`up` (Ethernet must
   be connected — the script refuses otherwise), `bench-mqtt start`, `bench-mqtt status`,
   `bench-ble-scan -s 5` if BLE is used. Then `make bench-test`.
10. **CI**: if the repo is on GitHub, `git push` (ask first) and check with `gh run list -L 1` /
    `gh run watch` that the `firmware` workflow is green.

Finish: tick Phase 0 items in `docs/PLAN.md`, add a dated commissioning entry to `docs/NOTES.md`,
commit `"Phase 0: commissioning"`. Next step for the owner: `/build-loop`.
