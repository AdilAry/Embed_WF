// Line-based serial console: the "firmware hooks" that let an AI agent (or you)
// drive and inspect the device from tools/esp_serial.py. Type `help` to list.
#pragma once

namespace console {

void poll();  // call from loop(); never blocks

}  // namespace console
