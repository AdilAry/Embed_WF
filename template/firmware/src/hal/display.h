// NV3041A 480x272 QSPI panel via Arduino_GFX (see docs/hardware board file §3).
#pragma once

#include <Arduino_GFX_Library.h>

namespace display {

bool begin(uint8_t rotation);  // false if the panel driver failed to start
bool ok();
Arduino_GFX* gfx();
void setBacklight(uint8_t duty);  // 0..255
uint8_t backlight();

// Clear the text area and print `text` word-wrapped (uses logic::wrapText).
void showText(const char* title, const char* text);

// Small status line at the bottom of the screen.
void showStatus(const char* text);

}  // namespace display
