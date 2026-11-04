#include "selftest.h"

#include <Arduino.h>

#include <cstdarg>

#include "../hal/display.h"
#include "../hal/touch.h"
#include "../logic/text_wrap.h"

namespace selftest {

namespace {

int g_pass = 0;
int g_fail = 0;

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

int runAll() {
  g_pass = g_fail = 0;
  Serial.println("SELFTEST:BEGIN");

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

  // T-TOUCH: some touch controller selected. NOTE: on an R board detection falls
  // back to XPT2046 without proof the chip is there, so this only fails for "none".
  report("T-TOUCH", touch::type() != touch::Type::None, "type=%s", touch::typeName());

  // T-WRAP: the same logic the host tests cover, run on the real compiler/CPU.
  const auto lines = logic::wrapText("hello embedded world", 14);
  const bool wrapOk = lines.size() == 2 && lines[0] == "hello embedded" && lines[1] == "world";
  report("T-WRAP", wrapOk, "lines=%u", (unsigned)lines.size());

  // Add project-specific target tests here. One report() per FSD requirement.

  Serial.printf("SELFTEST:DONE pass=%d fail=%d\n", g_pass, g_fail);
  return g_fail;
}

}  // namespace selftest
