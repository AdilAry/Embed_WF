// Touch for both board variants behind one API (board file §4):
//   "R" board: XPT2046 resistive, bit-banged SPI   (proven on the owner's board)
//   "C" board: GT911 capacitive, I2C               (UNVERIFIED - check on first use)
// Detection probes I2C for a GT911 first; if nothing answers we assume XPT2046.
#pragma once

#include <Arduino.h>

namespace touch {

enum class Type : uint8_t { None, XPT2046, GT911 };

Type begin();             // detect + init; call once in setup() after display::begin()
Type type();
const char* typeName();   // "none" / "xpt2046" / "gt911"

// true while pressed; x/y in screen coordinates for the current rotation.
// Non-blocking: costs one GPIO read when nothing is touched (R board).
bool read(int16_t& x, int16_t& y);

// Raw controller values (XPT2046 12-bit ADC, GT911 panel pixels). For calibration.
bool readRaw(int& rx, int& ry);

}  // namespace touch
