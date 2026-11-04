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

Note: Windows 10 is out of support. The free EU Extended Security Updates year
for consumers ended in October 2026, so this machine no longer gets security
patches. That's another good reason to keep the autonomous agent and its
downloads off it. The i5-9300H (9th gen Intel) is on Microsoft's Windows 11 CPU
list, so a free Windows 11 upgrade should be possible. Confirm with the *PC
Health Check* app (it also checks TPM 2.0 / Intel PTT and Secure Boot in the BIOS).
Repasted, with 16 GB, it has plenty of life left as the cockpit.

Claude Desktop runs here. Its Code tab can also drive Claude Code **on the
T480s** over SSH (GUIDE §3, step 6). The agent still runs on the T480s.
Arduino IDE still works here for quick manual experiments.

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
- Single-channel RAM costs some speed, which hardly matters here. As far as I
  know the T480s has memory soldered to the board plus **one** SODIMM slot.
  `sudo dmidecode -t memory` shows what's fitted where. If the slot is empty, an
  8 GB DDR4-2666 SODIMM gives 16 GB and dual channel. That's a cheap upgrade if
  you ever run ESP-IDF builds locally.
- Keep it on AC with lid-close set to "Do nothing".

## Boards

See [`boards/guition-jc4827w543.md`](boards/guition-jc4827w543.md). You own one
**R** (resistive XPT2046) and one **C** (capacitive GT911) JC4827W543.
