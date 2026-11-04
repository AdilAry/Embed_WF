# One command per step of the closed loop. The AI agent (and you) use these
# instead of remembering long arduino-cli lines. `make help` lists them.
#
# The fast-to-slow test tiers (see docs/FSD.md and Embed_WF docs/testing.md):
#   host-test   -> PC only, < 1 s       (pure logic in firmware/src/logic)
#   compile     -> PC only, ~1-3 min    (arduino-cli)
#   upload      -> needs the board on USB
#   target-test -> on the board         (`selftest` console command)
#   bench-test  -> board + dev-box Wi-Fi/MQTT/BLE (pytest, test/bench)

SKETCH      := firmware
BUILD       := build
PY          ?= python3
SERIAL      := $(PY) tools/esp_serial.py

# Board: Guition JC4827W543 (ESP32-S3-WROOM-1-N4R8). Same as the Arduino IDE
# Tools menu in the board reference. Use PartitionScheme=default if you need OTA.
FQBN ?= esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,CPUFreq=240,FlashMode=qio,FlashSize=4M,PSRAM=opi,PartitionScheme=huge_app,UploadSpeed=921600

# Pinned versions (known good on this board). Bump deliberately, then re-test.
ESP32_INDEX        := https://espressif.github.io/arduino-esp32/package_esp32_index.json
ESP32_CORE_VERSION ?= 3.3.10
GFX_LIB_VERSION    ?= 1.6.8
LIBS ?= "GFX Library for Arduino@$(GFX_LIB_VERSION)"

# Serial port: auto-detected (first Espressif USB device). Override: make upload PORT=/dev/ttyACM1
PORT ?= $(shell $(SERIAL) detect 2>/dev/null)

HOST_CXX    ?= g++
HOST_FLAGS  := -std=c++17 -Wall -Wextra -Werror -O1 -g -Ifirmware/src -Itest/host
HOST_SRCS   := $(wildcard firmware/src/logic/*.cpp) $(wildcard test/host/*.cpp)

.PHONY: help deps host-test compile upload monitor boot-check ping info target-test bench-test check loop size clean trace ci-fw

help:
	@echo "make deps         install ESP32 core + libraries (once per machine)"
	@echo "make host-test    tier 1: logic tests on the PC (fast, no board needed)"
	@echo "make compile      build firmware -> $(BUILD)/fw"
	@echo "make check        host-test + compile (what CI runs)"
	@echo "make upload       flash the board (PORT=$(PORT))"
	@echo "make boot-check   reset board, verify clean boot (no panic/watchdog)"
	@echo "make monitor      show serial output for 15 s (SECS=60 for longer)"
	@echo "make ping / info  quick liveness / status"
	@echo "make target-test  tier 2: run on-board selftest"
	@echo "make bench-test   tier 3: pytest bench tests (Wi-Fi, MQTT, BLE ...)"
	@echo "make loop         host-test -> compile -> upload -> boot-check -> target-test"
	@echo "make trace        requirement -> test -> last result matrix (STRICT=1 / RUN=1 to enforce)"
	@echo "make ci-fw        download the firmware GitHub CI built for HEAD (instead of compiling)"

deps:
	arduino-cli core update-index --additional-urls $(ESP32_INDEX)
	arduino-cli core install esp32:esp32@$(ESP32_CORE_VERSION) --additional-urls $(ESP32_INDEX)
	arduino-cli lib install $(LIBS)

# The result of the last run of each tier is kept in build/ for `make trace`.
host-test:
	@mkdir -p $(BUILD)
	$(HOST_CXX) $(HOST_FLAGS) $(HOST_SRCS) -o $(BUILD)/host_tests
	@./$(BUILD)/host_tests > $(BUILD)/host-test.log; rc=$$?; cat $(BUILD)/host-test.log; exit $$rc

compile:
	arduino-cli compile --fqbn $(FQBN) --warnings default \
		--build-path $(BUILD)/arduino --output-dir $(BUILD)/fw $(SKETCH)

size: compile
	@ls -l $(BUILD)/fw/*.bin

check: host-test compile

upload:
	@test -n "$(PORT)" || (echo "No ESP32 port found. Plugged in? In the 'dialout' group? Try: $(SERIAL) list" && exit 3)
	arduino-cli upload -p $(PORT) --fqbn $(FQBN) --input-dir $(BUILD)/fw $(SKETCH)

SECS ?= 15
monitor:
	$(SERIAL) monitor -s $(SECS)

boot-check:
	$(SERIAL) bootcheck

ping:
	$(SERIAL) cmd ping --until PONG

info:
	$(SERIAL) cmd info --until "^INFO"

target-test:
	$(SERIAL) selftest

bench-test:
	@mkdir -p $(BUILD)
	$(PY) -m pytest -v --junitxml=$(BUILD)/bench-test.xml test/bench

loop: host-test compile upload boot-check target-test
	@echo "LOOP:GREEN all tiers up to target passed"

# Requirement traceability (tools/trace.py). Plain `make trace` only reports.
#   STRICT=1  fail if a requirement has no test or a test failed
#   RUN=1     also fail on tests that have not been run (use at the end of a phase)
#   REQS="REQ-010 REQ-020"  only those requirements
trace:
	$(PY) tools/trace.py $(if $(RUN),--require-run,$(if $(STRICT),--strict)) $(REQS)

# Video 3's trick: let GitHub Actions compile, and only flash on the dev box.
# Needs `gh auth login`, the commit pushed, and its `firmware` workflow finished.
ci-fw:
	@mkdir -p $(BUILD)/fw
	gh run download --name firmware-$$(git rev-parse HEAD) --dir $(BUILD)/fw
	@ls -l $(BUILD)/fw
	@echo "Now: make upload"

clean:
	rm -rf $(BUILD)
