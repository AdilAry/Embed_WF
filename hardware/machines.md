# Machines and their roles

## Legion (main laptop) — the cockpit

| | |
|---|---|
| Model | Lenovo Legion Y540-15IRH-PG0 |
| CPU / GPU | Intel Core i5-9300H (4C/8T) / NVIDIA GTX 1650 |
| RAM / disk | 16 GB DDR4-2666 (2 sticks, mixed brands) / 476 GB SSD |
| OS | Windows 10 (EU edition) |

**Role:** your personal machine and the place you *supervise* from. Claude
Desktop (chat, planning, spec reviews), VS Code with Remote-SSH into the dev box,
the GitHub website. The AI agent does **not** run here with broad permissions.

Note: Windows 10's consumer support has ended. Another good reason to keep the
autonomous agent and its downloads off this machine. Arduino IDE still works
here for quick manual experiments.

## ThinkPad T480s (test laptop) — the dev box + test bench

| | |
|---|---|
| Model | Lenovo ThinkPad T480s 20L8S09L00 |
| CPU / GPU | Intel Core i5-8350U (4C/8T) / Intel UHD 620 |
| RAM / disk | 8 GB DDR4-2666 (single channel) / 380 GB SSD |
| OS | Linux Mint |
| Ports used | USB-A/USB-C → ESP32 boards · Ethernet → router · Intel Wi-Fi → test hotspot · Bluetooth → BLE tests |

**Role:** runs Claude Code, arduino-cli and the tests as the unprivileged user
`embdev`. Plays the part of video 3's Raspberry Pi bench: it flashes the boards,
reads their serial output, provides a disposable Wi-Fi network (`bench-wifi`),
an MQTT broker (`bench-mqtt`), and BLE scanning (`bench-ble-scan`).

**Constraints to remember**

- Internet must come over **Ethernet** while the Wi-Fi card is the test hotspot.
- 8 GB RAM is fine for one or two parallel Claude sessions with arduino-cli.
  ESP-IDF builds are heavier; close other apps or build in CI.
- Single-channel RAM costs some speed, which hardly matters here. A second
  8 GB stick (DDR4-2666 SODIMM) is a cheap upgrade if you ever want it.
- Keep it on AC with lid-close set to "Do nothing".

## Boards

See [`boards/guition-jc4827w543.md`](boards/guition-jc4827w543.md). You own one
**R** (resistive XPT2046) and one **C** (capacitive GT911) JC4827W543.
