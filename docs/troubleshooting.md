# Troubleshooting

Before anything else, tell the agent what's wrong in plain words. It can usually
diagnose it. This page is for when you'd rather know yourself, or when the agent
itself can't run.

## Board / serial

| Symptom | Fix |
|---|---|
| `arduino-cli board list` shows nothing | Try another USB-C cable (many are charge-only) and another port. Run `dmesg -w`, then plug in: you should see `ttyACM0`. |
| `Permission denied: /dev/ttyACM0` | `id` must list `dialout`. Log out and back in after `setup-root.sh`. |
| Port appears then vanishes (CH340/CP210x boards) | `brltty` is stealing it: `sudo apt remove brltty` (the setup script does this). |
| Upload: "Failed to connect" / "No serial data received" | Hold **BOOT**, tap **RESET**, release **BOOT**, `make upload`, then press RESET. Usually caused by a firmware crash loop. |
| `make boot-check` reports `reset=panic` | The firmware crashes at boot. `make monitor SECS=20` and look for `Backtrace:`. Ask the agent to decode it. |
| No serial output at all | FQBN must contain `CDCOnBoot=cdc` (the Makefile does). In Arduino IDE: *USB CDC On Boot = Enabled*. |
| Garbled serial | Baud mismatch: the template uses 115200. |
| T-PSRAM fails | PSRAM must be **OPI**, not QSPI. Check FQBN `PSRAM=opi`. |
| Display stays black | Backlight on? `bl 200` in the console. Colours inverted? The `IPS` flag must be `true`. |
| Touch coordinates are wrong (R board) | Use `touch` command at four corners → update `XPT_*` in `firmware/src/config.h`. |
| Touch shows `xpt2046` on the C board | GT911 not found on I2C. Address may depend on INT level at reset; the firmware already retries with the GT911 reset sequence on IO38; ask the agent to dig further. Record the fix in the board file. |
| Two boards plugged in | `make boards` shows which is R and which is C. Add `BOARD=R` or `BOARD=C` to any make command (`make loop BOARD=C`); every step then uses that board. `PORT=/dev/ttyACM1` works too. |
| `make boards` shows `board=-` | That board isn't registered yet. Plug it in alone and run `python3 tools/esp_serial.py register R` (or `C`). Once per board per dev box. |
| `T-TOUCH` fails with `expected=unknown(register-the-board)` | Same thing: the self test doesn't know which touch controller this board must have. Register it. |
| `T-TOUCH` fails with `type=xpt2046 expected=gt911` | The C board's GT911 wasn't found, so the firmware fell back to the resistive driver. That's a real fault on the C board (or the board is registered under the wrong letter: fix the line in `~/.config/embwf/boards`). |
| `no connected board is registered as C` | The C board is unplugged, or was never registered. |
| `make open-check` prints `OPENCHECK:RESETS` | **Board restarts when the port is opened.** The S3's built-in USB uses the DTR/RTS lines as reset signals and Linux toggles them on open. Single commands still work (the tool waits for the reboot). Multi-step bench tests lose device state between steps. Tell the agent: "esp_serial.py resets the board on open; keep one serial connection open for the whole pytest session instead of one per command", and try `stty -F /dev/ttyACM0 -hupcl` first, which stops Linux dropping the lines on close. |
| `make trace` shows `STALE` | The test passed on older code. Rerun that tier: `make host-test`, `make loop`, or `make bench-test`. `STALE` on target/bench with `build unknown` means the firmware wasn't built by `make compile` (Arduino IDE build). |

## Toolchain

| Symptom | Fix |
|---|---|
| `make deps` can't find `esp32:esp32` | Board index URL missing. Run `make deps` (it passes the URL), or `arduino-cli config set board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json`. |
| Pinned version not found | Version numbers in `template/Makefile` (`ESP32_CORE_VERSION`, `GFX_LIB_VERSION`) can be changed. Ask the agent to pick the newest 3.3.x / 1.6.x and re-run the tests. |
| `ledcSetup was not declared` | 2.x API in old code. Use `ledcAttach`/`ledcWrite` (core 3.x). |
| Sketch too big | `PartitionScheme=huge_app` is already the default. Need OTA? Then `default` partition and slimmer code. |
| CI red but local green | Open the Actions log on GitHub, or ask the agent: `gh run view --log-failed`. |

## Dev box / network

| Symptom | Fix |
|---|---|
| `bench-wifi: refusing - wlp… is this machine's internet connection` | Plug in Ethernet (or a USB Wi-Fi dongle) first. That's deliberate. |
| `bench-wifi up` asks for a password / "Not authorized" | The polkit rule from `setup-root.sh` didn't apply. Reboot once. Check that `/etc/polkit-1/rules.d/50-embwf-networkmanager.rules` exists. |
| ESP32 can't reach `bench-mqtt` at 10.42.0.1 | `bench-mqtt status`. If ufw is active: `sudo ufw allow from 10.42.0.0/24 to any port 1883`. |
| `bench-ble-scan` fails | `bluetoothctl show` → `Powered: yes`? Run `rfkill unblock bluetooth`. |
| SSH from Windows times out | Is the T480s asleep? Set the lid action to "Do nothing" and disable suspend on AC. Check the IP in the router. |
| Agent stopped when I closed my laptop | Run it inside `tmux` (see GUIDE §B5). |

## pi (the agent)

| Symptom | Fix |
|---|---|
| `pi: command not found` | Open a new terminal (PATH). Otherwise re-run `bash ~/Embed_WF/devbox/setup-user.sh`. |
| Commands like `/start` don't appear | `ls ~/.pi/agent/prompts` should list `start.md`, `wrap.md`, `define.md` and the others. If not, run `bash ~/Embed_WF/tools/install-workflow.sh`. In a running pi, `/reload` picks them up. |
| I edited a command file in the kit and nothing changed | The commands are links, so the file is already current: `/reload` in a running pi, or start a new session. If you installed with `--copy`, run `bash ~/Embed_WF/tools/install-workflow.sh --copy` again. |
| Linked commands are not offered | Install copies instead: `bash ~/Embed_WF/tools/install-workflow.sh --copy`. |
| A session starts with more context than expected | A parent folder has its own `AGENTS.md` or `CLAUDE.md`: agents load those too. Projects belong in `~/projects/`, not inside `~/Embed_WF`. In Claude Code, `/context all` lists the files it loaded. |
| The agent stopped at the Run limit | Ten flash-and-test runs without a pass means the item is too big or the cause is physical. `/wrap`, split the item in `docs/PLAN.md`, start fresh. |
| "Waiting on me" keeps growing | Items there are not done until you look at the device and say so at the next `/start`. Check before starting more. |
| The agent starts coding before I said OK | `/start` forbids that. Say "stop, show me the plan first". If it keeps happening, the task was given as plain text instead of through `/start`. |
| A session got long and vague | That is context rot. `/wrap` (it records exactly where things stand), `/new`, `/start`. |
| `PROGRESS.md` keeps growing or contradicts itself | It is a snapshot, not a log. Ask for "rewrite Now and Next from scratch, move finished work to docs/history.md", or do it by hand. |
| "No model" / asks to log in | `/login`, choose your provider, then `/model`. |
| Out of quota or credit | Wait for the quota window, or top up. See GUIDE §7 for ways to use less. |
| The agent ran something I didn't expect | That is how pi works: it never asks first. `Esc` stops it. This is why it runs as `embdev` on the spare machine (GUIDE §6). |
| The agent goes in circles on a bug | Stop it (`Esc`). Ask it to summarise what it tried and its hypothesis. Often the FSD is ambiguous, or the problem is physical (cable, wrong board). |
| `new-embedded-project` says git doesn't know who you are | Run the two `git config --global user.…` commands it prints, then try again. |
| `gh repo create` is refused | The dev box's GitHub token is deliberately narrow. Create the empty repo on github.com, add it to the token's repository list, then push (GUIDE §B3). |
