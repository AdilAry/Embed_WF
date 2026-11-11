// On-target tests ("target tier"). Triggered by the `selftest` console command
// and parsed by tools/esp_serial.py. Output contract, one line per test:
//
//   TEST:<id>:PASS:<detail>
//   TEST:<id>:FAIL:<detail>
//   SELFTEST:DONE pass=<n> fail=<m>
//
// Keep IDs stable: docs/FSD.md refers to them in its verification column.
#pragma once

#include <stdint.h>

namespace selftest {

// Runs every test, prints the lines above, returns the number of failures.
// expectTouch: "xpt2046" / "gt911" if the tester knows which board this is
// (tools/esp_serial.py passes it for a registered board), or "" if unknown.
int runAll(const char* expectTouch = "");

// Called once at the end of setup() with millis() at that moment (for T-BOOT).
void setBootMs(uint32_t ms);

}  // namespace selftest
