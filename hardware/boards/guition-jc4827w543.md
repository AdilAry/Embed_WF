# Board reference — Guition JC4827W543 (ESP32-S3, 4.3" 480×272 NV3041A QSPI)

Hardware reference for every project on this board. Project-specific behaviour
belongs in the project's own notes; this file only covers the board, toolchain
and hard-won gotchas. Items marked **(unverified)** come from vendor docs or
convention, not from a sketch that has been run on this board.

## 0. Board identity (read first)

- Module: **ESP32-S3-WROOM-1-N4R8** — dual-core LX7 @ 240 MHz, 512 KB SRAM,
  **4 MB flash (quad)**, **8 MB PSRAM (octal / OPI)**. Wi-Fi 2.4 GHz + BLE 5.
  **No Bluetooth Classic** (no `BluetoothSerial`, no A2DP) despite vendor docs
  saying "BT 4.2".
- Display: 4.3" IPS TFT, 480×272 native (landscape), **NV3041A** over **QSPI**.
- Touch comes in three SKUs, and the suffix decides the driver:
  `N` = no touch, `R` = **resistive XPT2046 (SPI)**, `C` = **capacitive GT911 (I2C)**.
- **The owner has both an R (resistive) and a C (capacitive) board.** Unless a
  project names one, write touch code that works on either: detect at boot and
  pick the driver (§4). Everything except touch (display, SD, audio, GPIO) is
  identical on both.
- Toolchain: **Arduino IDE** (primary), board "ESP32S3 Dev Module". Owner is in
  **Finland (ETSI)**.

## 1. Pin map (complete)

| GPIO | Function | Notes |
|---|---|---|
| 0 | BOOT button / LCD_TE | Strapping pin. Can be read as a user button (INPUT_PULLUP, LOW = pressed) after boot. Never drive it. |
| 1 | LCD backlight | PWM via LEDC (§3). |
| 2 | I2S LRCK (WS) | Speaker amp. |
| 3 | Touch INT | XPT2046 /PENIRQ (R) or GT911 INT (C). Active-low. |
| 4 | Touch I2C SCL | GT911 only (C). Free on R/N? **(unverified)** |
| 8 | Touch I2C SDA | GT911 only (C). Free on R/N? **(unverified)** |
| 10 | SD card CS | microSD (TF) slot. |
| 11 | SPI MOSI | Shared: XPT2046 DIN + SD CMD. |
| 12 | SPI SCK | Shared: XPT2046 CLK + SD CLK. |
| 13 | SPI MISO | Shared: XPT2046 DOUT + SD D0. |
| 19 / 20 | USB D+ / D− | Native USB on the USB-C port. Do not use. |
| 21 | LCD D0 | QSPI. |
| 26–37 | — | **Internal flash (26–32) and octal PSRAM (33–37). Never use.** |
| 38 | Touch CS (R) / Touch RESET (C) | Depends on variant. |
| 39 | LCD D3 | QSPI. |
| 40 | LCD D2 | QSPI. |
| 41 | I2S DOUT | To speaker amp. |
| 42 | I2S BCLK | Speaker amp. |
| 43 / 44 | UART0 TX / RX | Not on the expansion headers. |
| 45 | LCD CS | QSPI. Strapping pin. |
| 47 | LCD SCK | QSPI. |
| 48 | LCD D1 | QSPI. |

The factory pin sheet labels IO11 as "TF_MISO" and IO13 as "TF_MOSI"; that is a
labelling error. Use MOSI = 11, MISO = 13 (matches SD protocol, Dev Device Pins,
and the proven XPT2046 code).

### Expansion headers (JST 1.25 mm, 4-pin) — the only free GPIO

| Header | Pins (silkscreen order) |
|---|---|
| P2 | IO46, IO9, IO14, IO5 |
| P3 | IO6, IO7, IO15, IO16 |
| P4 (UART1) | GND, 3V3, IO17, IO18 |
| P5 | GND, 3V3, IO17, IO18 (duplicate of P4, different connector) |

- **P2 and P3 carry no GND or 3V3** — take power/ground from P4 or P5.
- **ADC with Wi-Fi on:** only ADC1 works while Wi-Fi is active. ADC1 = GPIO1–10,
  so of the free pins only **IO5, IO6, IO7, IO9** can do analog reads. IO14–18
  are ADC2 (unusable with Wi-Fi).
- **IO46 is a strapping pin**: fine as an output after boot, but don't attach
  anything that pulls it high during reset.
- IO17/IO18 default to UART1 (`Serial1.begin(baud, SERIAL_8N1, 18, 17)`,
  RX = 18, TX = 17) but are ordinary GPIO if UART1 is unused.

### Other connectors

- USB-C: power + native USB (programming + serial).
- P1: 4-pin JST 1.25 "power supply base" (5 V input). Exact pinout **(unverified)**.
- P6 "BAT": 2-pin JST 1.25 LiPo input. SW1: battery power switch.
- P7 "Speak": 2-pin speaker output from the I2S amp.
- TF: microSD slot. BOOT and RESET buttons on the back.

## 2. Toolchain settings

**Arduino IDE → Tools** (board: *ESP32S3 Dev Module*):

| Setting | Value | Why |
|---|---|---|
| USB CDC On Boot | **Enabled** | Otherwise `Serial` goes nowhere over USB-C. |
| USB Mode | Hardware CDC and JTAG | |
| CPU Frequency | 240 MHz (WiFi) | |
| Flash Mode | QIO 80 MHz | DIO 80 MHz also works (used by the reference WiFi Analyzer). |
| Flash Size | **4 MB (32 Mb)** | |
| PSRAM | **OPI PSRAM** | Not "QSPI PSRAM" — that fails to find the octal chip. |
| Partition Scheme | Default 4 MB (1.2 MB app) or **Huge APP (3 MB No OTA)** | Switch to Huge APP when the binary exceeds ~1.2 MB (LVGL, Wi-Fi + BLE, big assets). |
| Upload Speed | 921600 | |

**arduino-cli FQBN** (for compile checks from Claude Code):

```
esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,CPUFreq=240,FlashMode=qio,FlashSize=4M,PSRAM=opi,PartitionScheme=huge_app,UploadSpeed=921600
```

Swap `PartitionScheme=default` when OTA is needed.

**Upload trouble:** if the port vanishes or upload won't start (e.g. the running
sketch crashes in a boot loop), hold **BOOT**, tap **RESET**, release BOOT, then
upload. Press RESET afterwards if the new sketch doesn't start by itself.

**Serial:** `Serial.begin(115200);` then optionally
`while (!Serial && millis() < 2000) {}` so early boot messages aren't lost on
native USB. Always include serial debug output in sketches.

### Library / core versions

State the versions used in a comment at the top of every sketch. Prefer the
newest releases; known-good baseline:

- **arduino-esp32 core 3.3.x** (3.3.10 proven; ESP-IDF 5.x underneath).
- **GFX Library for Arduino** (Arduino_GFX, by Moon On Our Nation) **1.6.x**
  (1.6.8 latest at time of writing).

## 3. Display — NV3041A over QSPI (Arduino_GFX only)

**Use Arduino_GFX. Do not use LovyanGFX or TFT_eSPI** — neither supports this
panel's ESP32 QSPI bus out of the box.

Proven initialisation:

```cpp
#include <Arduino_GFX_Library.h>

#define GFX_BL 1
Arduino_DataBus *bus = new Arduino_ESP32QSPI(
    45 /*cs*/, 47 /*sck*/, 21 /*d0*/, 48 /*d1*/, 40 /*d2*/, 39 /*d3*/);
Arduino_GFX *gfx = new Arduino_NV3041A(
    bus, GFX_NOT_DEFINED /*rst*/, 0 /*rotation*/, true /*IPS*/);

void setup() {
  Serial.begin(115200);
  ledcAttach(GFX_BL, 5000 /*Hz*/, 8 /*bits*/);   // core 3.x LEDC API
  ledcWrite(GFX_BL, 220);                        // 0..255 brightness
  if (!gfx->begin()) Serial.println("gfx->begin() failed");
  gfx->fillScreen(RGB565_BLACK);
}
```

- **No reset pin** (`GFX_NOT_DEFINED`). **IPS = true**, or colours come out
  inverted.
- `gfx->begin()` defaults to 40 MHz and works. If artefacts ever appear, try
  `gfx->begin(32000000)` (the value Dev Device Pins uses).
- **Rotation:** 0 = landscape 480×272 (native), **1 = portrait 272×480**,
  2/3 = the flipped versions. Pass it in the constructor or call
  `gfx->setRotation(n)`, then always lay out from `gfx->width()` /
  `gfx->height()` rather than hard-coded numbers.
- **Backlight (core 3.x):** `ledcAttach(pin, freq, bits)` + `ledcWrite(pin, duty)`.
  The 2.x calls `ledcSetup` / `ledcAttachPin` **do not compile** on 3.x. Plain
  `digitalWrite(1, HIGH)` also works for on/off.
- **Colours:** RGB565. Use the `RGB565_*` named constants or
  `gfx->color565(r, g, b)`.
- **Text:** built-in font cell is 6×8 px per `setTextSize` unit. Built-in
  wrapping splits words mid-way and ignores panel borders — call
  `setTextWrap(false)` and wrap manually by word using `maxChars = width / (6*size)`.
- **Treat the panel as write-only.** Keep your own state; don't plan on reading
  pixels back.
- **Flicker control:** either (a) redraw only the regions whose state changed
  (proven approach), or (b) draw into a full-frame canvas and push it once:
  ```cpp
  Arduino_NV3041A *panel = new Arduino_NV3041A(bus, GFX_NOT_DEFINED, 0, true);
  Arduino_GFX *gfx = new Arduino_Canvas(480, 272, panel);
  // ...draw...  then  gfx->flush();
  ```
  The frame buffer is 480×272×2 ≈ 255 KB, so it **needs PSRAM = OPI enabled**
  or `begin()` returns false. Canvas + rotation is **(unverified)** here — check
  that `width()/height()` report what you expect before building on it.
- Optional convenience header: Dev Device Pins library, `#include <PINS_JC4827W543.h>`,
  defines `bus`, `gfx`, `GFX_BL` and the other pins. It assumes the **GFX C
  (GT911) variant**. Prefer explicit definitions like the block above so
  nothing is hidden.
- LVGL works on this board (vendor examples use LVGL 8.4 with Arduino_GFX as the
  flush backend); only bring it in if a project really needs widgets.

## 4. Touch

### R vs C at a glance

| | R (resistive) | C (capacitive) |
|---|---|---|
| Controller | XPT2046, SPI | GT911, I2C |
| Pins | SCK 12, MOSI 11, MISO 13, CS 38, IRQ 3 | SDA 8, SCL 4, RESET 38, INT 3 |
| Coordinates | Raw 12-bit ADC, needs calibration | Panel pixels |
| Multi-touch | No | Yes (up to 5) |
| Surface | Soft plastic, needs a press | Glass, light touch |

- IO3 is an active-low touch interrupt on both, so "tap anywhere" logic that
  only watches IO3 works on either board, but coordinates only make sense with
  the matching driver.
- IO38 means different things: CS on R, GT911 reset on C. Don't configure it
  until the variant is known.

### Auto-detect at boot (default for all projects) **(unverified)**

Probe I2C first, before touching IO38 or the SPI pins:

```cpp
#include <Wire.h>
enum TouchType { TOUCH_NONE, TOUCH_XPT2046, TOUCH_GT911 };
static TouchType g_touch = TOUCH_NONE;
static uint8_t   g_gt911Addr = 0;

static TouchType detectTouch() {
  Wire.begin(8 /*SDA*/, 4 /*SCL*/, 400000);
  for (uint8_t a : {0x5D, 0x14}) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) { g_gt911Addr = a; return TOUCH_GT911; }
  }
  Wire.end();                        // release 8/4 on the R board
  return TOUCH_XPT2046;              // no GT911 answered: assume resistive
}
// setup(): g_touch = detectTouch(); Serial.printf("touch: %d\n", g_touch);
//          then init only the matching driver.
```

Wrap both drivers behind one function, for example
`bool touchRead(int16_t &x, int16_t &y)`, returning **screen** coordinates in
the current rotation, so the rest of the sketch never cares which board it's on.
Keep the XPT2046 calibration constants in one place.

### R variant — XPT2046 (proven on the owner's R board)

SPI: SCK 12, MOSI 11, MISO 13, CS 38, /PENIRQ 3. The proven approach
**bit-bangs** it on plain GPIO — no library and no SPI peripheral, so there's
no conflict with the QSPI display.

```cpp
#define T_SCK 12
#define T_MISO 13
#define T_MOSI 11
#define T_CS 38
#define T_IRQ 3

static uint16_t xptXfer(uint8_t cmd) {
  for (int i = 7; i >= 0; i--) {
    digitalWrite(T_MOSI, (cmd >> i) & 1);
    digitalWrite(T_SCK, HIGH); delayMicroseconds(1);
    digitalWrite(T_SCK, LOW);  delayMicroseconds(1);
  }
  uint16_t raw = 0;
  for (int i = 0; i < 16; i++) {
    digitalWrite(T_SCK, HIGH); delayMicroseconds(1);
    raw = (raw << 1) | (digitalRead(T_MISO) & 1);
    digitalWrite(T_SCK, LOW);  delayMicroseconds(1);
  }
  return (raw >> 3) & 0x0FFF;                    // 12-bit result
}

// true + averaged raw ADC coords while pressed
static bool xptRead(int &rx, int &ry) {
  if (digitalRead(T_IRQ) == HIGH) return false;  // not touched: one cheap read
  long sx = 0, sy = 0;
  digitalWrite(T_CS, LOW);
  for (int s = 0; s < 4; s++) { sy += xptXfer(0x90); sx += xptXfer(0xD0); }
  digitalWrite(T_CS, HIGH);
  rx = sx / 4; ry = sy / 4;
  return !(rx < 100 || rx > 4000 || ry < 100 || ry > 4000);  // reject noise
}

// setup():
//   pinMode(T_CS, OUTPUT);  digitalWrite(T_CS, HIGH);
//   pinMode(T_SCK, OUTPUT); digitalWrite(T_SCK, LOW);
//   pinMode(T_MOSI, OUTPUT); pinMode(T_MISO, INPUT);
//   pinMode(T_IRQ, INPUT_PULLUP);
//   { int a, b; xptRead(a, b); }   // one read to arm PENIRQ
```

- Poll at ~25 Hz (every 40 ms) and debounce ~150 ms; act on the press edge.
- Raw values are **not screen coordinates**. For on-screen buttons, calibrate:
  print raw X/Y at the four corners in the rotation you're using, then `map()`
  and swap/invert axes as needed. Axis orientation relative to rotation must be
  found empirically.
- Library alternative: `XPT2046_Touchscreen` (Paul Stoffregen) with a second
  SPI instance on these pins. The bit-bang routine is preferred.
- **Pins 11/12/13 are shared with the SD card.** Using both means sharing the
  bus with separate CS lines (touch 38, SD 10): keep both CS high when idle, and
  don't bit-bang these pins while the SD driver is mid-transaction (same task,
  or guard with a mutex).

### C variant — GT911 (not yet proven on the owner's C board)

I2C SDA 8, SCL 4, 400 kHz; RESET 38, INT 3; address 0x5D (or 0x14 depending on
INT level at reset). Use a GT911 library from Library Manager (e.g.
`TAMC_GT911`, check the current version) with `Wire.begin(8, 4)`. Coordinates
come back in panel pixels; map them for rotation.

## 5. microSD (TF)

SCK 12, MOSI 11, MISO 13, CS 10 (SPI mode). **(unverified on owner's board)**

```cpp
#include <SPI.h>
#include <SD.h>
SPIClass sdSPI(FSPI);
// in setup():
sdSPI.begin(12, 13, 11, 10);        // sck, miso, mosi, ss
if (!SD.begin(10, sdSPI, 20000000)) Serial.println("SD init failed");
```

Shared with resistive touch — see §4.

## 6. Audio — I2S mono amplifier

BCLK 42, LRCK/WS 2, DOUT 41 → class-D amp (vendor docs ship NS4168 and
MAX98357-type datasheets; either way it's standard I2S, mono) → speaker on P7.
**(unverified on owner's board)**

Core 3.x uses the new `ESP_I2S.h` API. The legacy `driver/i2s.h` is deprecated:

```cpp
#include <ESP_I2S.h>
I2SClass i2s;
// in setup():
i2s.setPins(42 /*bclk*/, 2 /*ws*/, 41 /*dout*/);
i2s.begin(I2S_MODE_STD, 16000, I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO);
// i2s.write(buf, len);
```

Keep volume low in software at first; small speakers distort easily.

## 7. Power

- 5 V via USB-C or P1; ~260 mA typical with the backlight on.
- LiPo on P6 through an **IP5306** charge/boost IC; SW1 switches battery power.
- **No battery-voltage GPIO** appears in the factory pin table, so the firmware
  cannot read the charge level without adding a divider to a free ADC1 pin
  (IO5/6/7/9).
- IP5306 boost chips typically auto-shut off under very light load, so
  deep-sleep on battery may power the board off entirely. **(unverified here)**
- Dimming the backlight is the single biggest power saving.

## 8. Memory

- Internal SRAM is scarce (only a few hundred KB of heap is left once Wi-Fi is running). Put big buffers in
  PSRAM: `ps_malloc()` / `heap_caps_malloc(n, MALLOC_CAP_SPIRAM)`. With OPI PSRAM
  enabled, large `malloc`s (> ~4 KB) usually land in PSRAM automatically.
- Prefer fixed static buffers over growing heap structures in long-running loops.
- Nothing sensitive in flash unless intended: call `WiFi.persistent(false)`
  before the first `WiFi.mode()` (keeps the Wi-Fi driver config in RAM).
- Check sizes at boot when debugging:
  `ESP.getFreeHeap()`, `ESP.getFreePsram()`, `ESP.getPsramSize()`.

## 9. Radio (Wi-Fi / BLE)

- 2.4 GHz only, one radio. Wi-Fi and BLE coexist but share airtime.
- **Region:** set the country for Finland/ETSI so channels 1–13 are legal and
  scanned:
  ```cpp
  wifi_country_t c = {}; strncpy(c.cc, "FI", sizeof(c.cc));
  c.schan = 1; c.nchan = 13; c.policy = WIFI_COUNTRY_POLICY_MANUAL;
  esp_wifi_set_country(&c);     // after WiFi.mode(WIFI_STA)
  ```
  FCC hardware and regions: channels 1–11 only.
- **Async scans keep the UI responsive:**
  `WiFi.scanNetworks(true /*async*/, true /*hidden*/, true /*passive*/)`, then
  poll `WiFi.scanComplete()` (returns `WIFI_SCAN_RUNNING` while busy, a negative
  value on failure — clamp to 0). Call `WiFi.scanDelete()` when done. If you
  abandon a scan early, call `esp_wifi_scan_stop()`.
- **Promiscuous mode and scanning are mutually exclusive** — both use the same
  driver. Disable promiscuous before scanning; stop the scan before enabling
  promiscuous.
- The promiscuous RX callback runs in the **Wi-Fi task** (not an ISR — no
  `IRAM_ATTR` needed). Keep it short, and guard any data it shares with
  `loop()` using a `portMUX_TYPE` critical section or `volatile` flags.
- Channel hopping: `esp_wifi_set_channel(ch, WIFI_SECOND_CHAN_NONE)`; 500 ms
  per channel is proven.
- The PCB antenna is on the module end of the board — keep metal and hands off it.

## 10. Rules for Claude on this board

1. Graphics: **Arduino_GFX only**. Never LovyanGFX or TFT_eSPI.
2. Core **3.x APIs only**: `ledcAttach`/`ledcWrite`, `ESP_I2S.h`,
   `WiFi.scanNetworks(async, …)`. No 2.x `ledcSetup`/`ledcAttachPin`.
3. Header comment on every sketch: board, core version, library names + versions,
   and required Tools settings (at least PSRAM = OPI and USB CDC On Boot = Enabled).
4. Never touch GPIO 19/20 (USB), 26–37 (flash/PSRAM), or the display pins.
   Only use free pins from the header table in §1, and flag ADC2 or strapping-pin
   choices.
5. Lay out from `gfx->width()/height()`, redraw only on change, and wrap text
   manually.
6. Keep touch polling non-blocking. Any long operation (scans, network, file I/O)
   must be async or call the touch poll from inside its wait loop.
7. Include serial debug output (`Serial.begin(115200)`), tagged by subsystem.
8. Touch code must run on both the R and C boards: auto-detect (§4) behind a
   single `touchRead()` that returns screen coordinates. Only target one variant
   when the project says so.

## Sources

- Factory docs, IO pin distribution and spec sheet (mirrored):
  https://github.com/profi-max/JC4827W543_4.3inch_ESP32S3_board
- Dev Device Pins, `PINS_JC4827W543.h`: https://github.com/moononournation/Dev_Device_Pins
- Arduino_GFX: https://github.com/moononournation/Arduino_GFX
- Reference project (display + Wi-Fi scan, proven): https://github.com/thelastoutpostworkshop/JC4827W543_WifiAnalyzer
- Owner's proven project: VirtualPetNetSec (QSPI display, LEDC backlight,
  bit-banged XPT2046, async scan + promiscuous, FI country code).
- Product page: https://manuals.plus/ae/1005006729657546