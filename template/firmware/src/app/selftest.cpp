#include "selftest.h"

#include <Arduino.h>

#include <cstdarg>
#include <cstring>

#include "../config.h"
#include "../hal/display.h"
#include "../hal/touch.h"
#include "../logic/text_wrap.h"

namespace selftest {

namespace {

int g_pass = 0;
int g_fail = 0;
uint32_t g_bootMs = 0;

// REQ-001 in the template FSD: main screen within 3 s of power-up.
constexpr uint32_t kMaxBootMs = 3000;

void report(const char* id, bool ok, const char* fmt, ...) {
  char detail[96];
  va_list ap;
  va_start(ap, fmt);
  vsnprintf(detail, sizeof(detail), fmt, ap);
  va_end(ap);
  Serial.printf("TEST:%s:%s:%s\n", id, ok ? "PASS" : "FAIL", detail);
  (ok ? g_pass : g_fail)++;
}

}  // namespace

void setBootMs(uint32_t ms) { g_bootMs = ms; }

int runAll(const char* expectTouch) {
  g_pass = g_fail = 0;
  // The build id lets `make trace` tie this result to the source it came from.
  Serial.printf("SELFTEST:BEGIN build=%s\n", FW_BUILD_ID);

  // T-BOOT: setup() finished (screen drawn, touch detected) quickly enough.
  report("T-BOOT", g_bootMs > 0 && g_bootMs <= kMaxBootMs, "boot_ms=%lu max=%lu",
         (unsigned long)g_bootMs, (unsigned long)kMaxBootMs);

  // T-PSRAM: proves Tools > PSRAM = OPI was set (8 MB octal PSRAM on N4R8).
  const uint32_t psram = ESP.getPsramSize();
  report("T-PSRAM", psram >= 4u * 1024 * 1024, "psram=%lu", (unsigned long)psram);

  // T-FLASH: module is N4R8 -> 4 MB flash.
  const uint32_t flash = ESP.getFlashChipSize();
  report("T-FLASH", flash == 4u * 1024 * 1024, "flash=%lu", (unsigned long)flash);

  // T-HEAP: enough internal heap left after init.
  const uint32_t heap = ESP.getFreeHeap();
  report("T-HEAP", heap > 100u * 1024, "free_heap=%lu", (unsigned long)heap);

  // T-DISPLAY: panel driver started.
  report("T-DISPLAY", display::ok(), "w=%d h=%d", display::ok() ? display::gfx()->width() : 0,
         display::ok() ? display::gfx()->height() : 0);

  // T-TOUCH: the right touch controller was detected. Detection can only prove a
  // GT911 (it answers on I2C); "xpt2046" is merely assumed when nothing answers,
  // so a C board with an undetected GT911 looks exactly like an R board. The
  // tester therefore says which board this is (`selftest touch=gt911`, sent by
  // esp_serial.py for a registered board) and a mismatch fails. With no
  // expectation, only a positively detected GT911 passes.
  // What this still cannot catch: a dead XPT2046 on an R board. That is the
  // manual corner-tap check in commissioning.
  const bool haveExpect = expectTouch != nullptr && expectTouch[0] != '\0';
  const bool touchOk = haveExpect ? std::strcmp(touch::typeName(), expectTouch) == 0
                                  : touch::type() == touch::Type::GT911;
  report("T-TOUCH", touchOk, "type=%s expected=%s", touch::typeName(),
         haveExpect ? expectTouch : "unknown(register-the-board)");

  // T-WRAP: the same logic the host tests cover, run on the real compiler/CPU.
  const auto lines = logic::wrapText("hello embedded world", 14);
  const bool wrapOk = lines.size() == 2 && lines[0] == "hello embedded" && lines[1] == "world";
  report("T-WRAP", wrapOk, "lines=%u", (unsigned)lines.size());

  // Add project-specific target tests here. One report() per FSD requirement.

  Serial.printf("SELFTEST:DONE pass=%d fail=%d\n", g_pass, g_fail);
  return g_fail;
}

}  // namespace selftest
