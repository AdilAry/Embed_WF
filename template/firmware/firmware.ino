// =============================================================================
// Project template firmware - Guition JC4827W543 (ESP32-S3-WROOM-1-N4R8)
//
// Board:      ESP32S3 Dev Module (arduino-esp32 core 3.3.x)
// Libraries:  GFX Library for Arduino (Arduino_GFX) 1.6.x
// Tools menu: USB CDC On Boot = Enabled, USB Mode = Hardware CDC and JTAG,
//             PSRAM = OPI PSRAM, Flash Size = 4MB, Partition = Huge APP
//             (all of this is in FQBN in the Makefile - use `make compile`)
//
// What it does: starts the display, detects which touch variant (R or C) this
// board is, draws touches, and runs a serial console (`help`) with a
// `selftest` command used by the automated test loop.
//
// Layout:  src/logic/  pure C++, host-tested (no Arduino.h allowed)
//          src/hal/    hardware drivers (display, touch)
//          src/app/    console + on-target self tests
// =============================================================================

#include "src/app/console.h"
#include "src/app/selftest.h"
#include "src/config.h"
#include "src/hal/display.h"
#include "src/hal/touch.h"

namespace {

constexpr uint32_t kTouchPollMs = 40;   // ~25 Hz
constexpr uint32_t kTouchDebounceMs = 150;

uint32_t g_lastTouchPoll = 0;
uint32_t g_lastTouchEdge = 0;
bool g_wasPressed = false;

void pollTouch() {
  const uint32_t now = millis();
  if (now - g_lastTouchPoll < kTouchPollMs) return;
  g_lastTouchPoll = now;

  int16_t x, y;
  const bool pressed = touch::read(x, y);
  if (pressed && !g_wasPressed && now - g_lastTouchEdge > kTouchDebounceMs) {
    g_lastTouchEdge = now;
    Serial.printf("[touch] press x=%d y=%d\n", x, y);
    if (display::ok()) {
      display::gfx()->fillCircle(x, y, 6, display::gfx()->color565(255, 200, 0));
      char buf[48];
      snprintf(buf, sizeof(buf), "touch %s  x=%d y=%d", touch::typeName(), x, y);
      display::showStatus(buf);
    }
  }
  g_wasPressed = pressed;
}

}  // namespace

void setup() {
  Serial.begin(115200);
  const uint32_t t0 = millis();
  while (!Serial && millis() - t0 < 2000) {
  }
  Serial.printf("\n[boot] %s v%s\n", FW_NAME, FW_VERSION);

  display::begin(DISPLAY_ROTATION);
  touch::begin();

  if (display::ok()) {
    display::showText(FW_NAME,
                      "Hello from the AI workflow template. Touch the screen, or type "
                      "help in the serial console.");
    char buf[48];
    snprintf(buf, sizeof(buf), "v%s  touch=%s", FW_VERSION, touch::typeName());
    display::showStatus(buf);
    display::setBacklight(BACKLIGHT_DEFAULT);
  }

  const uint32_t bootMs = millis();
  selftest::setBootMs(bootMs);
  Serial.printf("BOOT:OK fw=%s ver=%s display=%d touch=%s boot_ms=%lu\n", FW_NAME, FW_VERSION,
                display::ok() ? 1 : 0, touch::typeName(), (unsigned long)bootMs);
}

void loop() {
  console::poll();
  pollTouch();
}
