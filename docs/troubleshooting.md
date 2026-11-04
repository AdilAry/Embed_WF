# Troubleshooting

Before anything else, tell Claude what's wrong in plain words. It can usually
diagnose it. This page is for when you'd rather know yourself, or when Claude
itself can't run.

## Board / serial

| Symptom | Fix |
|---|---|
| `arduino-cli board list` shows nothing | Try another USB-C cable (many are charge-only) and another port. Run `dmesg -w`, then plug in: you should see `ttyACM0`. |
| `Permission denied: /dev/ttyACM0` | `id` must list `dialout`. Log out and back in after `setup-root.sh`. |
| Port appears then vanishes (CH340/CP210x boards) | `brltty` is stealing it: `sudo apt remove brltty` (the setup script does this). |
| Upload: "Failed to connect" / "No serial data received" | Hold **BOOT**, tap **RESET**, release **BOOT**, `make upload`, then press RESET. Usually caused by a firmware crash loop. |
| `make boot-check` reports `reset=panic` | The firmware crashes at boot. `make monitor SECS=20` and look for `Backtrace:`. Ask Claude to decode it. |
| No serial output at all | FQBN must contain `CDCOnBoot=cdc` (the Makefile does). In Arduino IDE: *USB CDC On Boot = Enabled*. |
| Garbled serial | Baud mismatch: the template uses 115200. |
| T-PSRAM fails | PSRAM must be **OPI**, not QSPI. Check FQBN `PSRAM=opi`. |
| Display stays black | Backlight on? `bl 200` in the console. Colours inverted? The `IPS` flag must be `true`. |
| Touch coordinates are wrong (R board) | Use `touch` command at four corners → update `XPT_*` in `firmware/src/config.h`. |
| Touch shows `xpt2046` on the C board | GT911 not found on I2C. Address may depend on INT level at reset; Claude can add a reset sequence on IO38. Record the fix in the board file. |
| Two boards plugged in | `make upload PORT=/dev/ttyACM1` (see `python3 tools/esp_serial.py list`). |

## Toolchain

| Symptom | Fix |
|---|---|
| `make deps` can't find `esp32:esp32` | Board index URL missing. Run `make deps` (it passes the URL), or `arduino-cli config set board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json`. |
| Pinned version not found | Version numbers in `template/Makefile` (`ESP32_CORE_VERSION`, `GFX_LIB_VERSION`) can be changed. Ask Claude to pick the newest 3.3.x / 1.6.x and re-run the tests. |
| `ledcSetup was not declared` | 2.x API in old code. Use `ledcAttach`/`ledcWrite` (core 3.x). |
| Sketch too big | `PartitionScheme=huge_app` is already the default. Need OTA? Then `default` partition and slimmer code. |
| CI red but local green | Open the Actions log on GitHub, or ask Claude: `gh run view --log-failed`. |

## Dev box / network

| Symptom | Fix |
|---|---|
| `bench-wifi: refusing - wlp… is this machine's internet connection` | Plug in Ethernet (or a USB Wi-Fi dongle) first. That's deliberate. |
| `bench-wifi up` asks for a password / "Not authorized" | The polkit rule from `setup-root.sh` didn't apply. Reboot once. Check that `/etc/polkit-1/rules.d/50-embwf-networkmanager.rules` exists. |
| ESP32 can't reach `bench-mqtt` at 10.42.0.1 | `bench-mqtt status`. If ufw is active: `sudo ufw allow from 10.42.0.0/24 to any port 1883`. |
| `bench-ble-scan` fails | `bluetoothctl show` → `Powered: yes`? Run `rfkill unblock bluetooth`. |
| SSH from Windows times out | Is the T480s asleep? Set the lid action to "Do nothing" and disable suspend on AC. Check the IP in the router. |
| Agent stopped when I closed my laptop | Run it inside `tmux` (see GUIDE §B5). |

## Claude Code

| Symptom | Fix |
|---|---|
| `claude: command not found` | Open a new terminal (PATH). Otherwise re-run `bash ~/Embed_WF/devbox/setup-user.sh`. |
| Skills like `/define` don't appear | `ls -l ~/.claude/skills` should show symlinks into `~/Embed_WF/skills`. Re-run setup-user.sh. Restart `claude`. |
| Usage limit reached | Wait for the window to reset. See GUIDE §7 for ways to use less. |
| Claude asks permission for everything | Start `claude` **inside the project folder**, so `.claude/settings.json` is picked up. |
| Claude goes in circles on a bug | Stop it (`Esc`). Ask it to summarise what it tried and its hypothesis. Often the FSD is ambiguous, or the problem is physical (cable, wrong board). |
