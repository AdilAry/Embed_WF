# template

ESP32 project for the Guition JC4827W543 (ESP32-S3, 4.3" touch display), built
with the [Embed_WF](https://github.com/adilary/embed_wf) AI-assisted workflow.

## What it does

See [`docs/FSD.md`](docs/FSD.md).

## Build & test

```bash
make deps          # once per machine
make check         # host tests + compile
make loop          # ... + flash + boot check + on-board tests (board on USB)
make bench-test    # Wi-Fi / MQTT / BLE tests on the dev box
```

Serial console at 115200 baud, type `help`. Or non-interactively:
`python3 tools/esp_serial.py cmd info`.

## Project layout

```
docs/        IDEA (your words) -> FSD (spec) -> PLAN (phases) -> NOTES (findings)
datasheets/  PDFs + extracted text + summaries for the agent
firmware/    Arduino sketch: src/logic (pure C++), src/hal (drivers), src/app
test/host/   tier 1 tests, run on the PC with g++
test/bench/  tier 3 tests, pytest + dev-box Wi-Fi/MQTT/BLE
tools/       esp_serial.py - non-interactive serial monitor / test runner
```
