// On-target tests ("target tier"). Triggered by the `selftest` console command
// and parsed by tools/esp_serial.py. Output contract, one line per test:
//
//   TEST:<id>:PASS:<detail>
//   TEST:<id>:FAIL:<detail>
//   SELFTEST:DONE pass=<n> fail=<m>
//
// Keep IDs stable: docs/FSD.md refers to them in its verification column.
#pragma once

namespace selftest {

// Runs every test, prints the lines above, returns the number of failures.
int runAll();

}  // namespace selftest
