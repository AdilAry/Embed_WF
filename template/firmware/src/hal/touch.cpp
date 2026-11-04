#include "touch.h"

#include <Wire.h>

#include "../config.h"
#include "display.h"

namespace touch {

namespace {

// Shared pins
constexpr int kIrq = 3;  // active-low on both variants
constexpr int kPin38 = 38;  // XPT2046 CS on R, GT911 RESET on C - don't touch until detected

// R: XPT2046 bit-banged SPI (shares 11/12/13 with the SD card, see board file)
constexpr int kSck = 12;
constexpr int kMiso = 13;
constexpr int kMosi = 11;

// C: GT911 I2C
constexpr int kSda = 8;
constexpr int kScl = 4;

Type g_type = Type::None;
uint8_t g_gtAddr = 0;

// ---------- XPT2046 (proven code from the board file) ----------
uint16_t xptXfer(uint8_t cmd) {
  for (int i = 7; i >= 0; i--) {
    digitalWrite(kMosi, (cmd >> i) & 1);
    digitalWrite(kSck, HIGH);
    delayMicroseconds(1);
    digitalWrite(kSck, LOW);
    delayMicroseconds(1);
  }
  uint16_t raw = 0;
  for (int i = 0; i < 16; i++) {
    digitalWrite(kSck, HIGH);
    delayMicroseconds(1);
    raw = (raw << 1) | (digitalRead(kMiso) & 1);
    digitalWrite(kSck, LOW);
    delayMicroseconds(1);
  }
  return (raw >> 3) & 0x0FFF;
}

bool xptReadRaw(int& rx, int& ry) {
  if (digitalRead(kIrq) == HIGH) return false;
  long sx = 0, sy = 0;
  digitalWrite(kPin38, LOW);
  for (int s = 0; s < 4; s++) {
    sy += xptXfer(0x90);
    sx += xptXfer(0xD0);
  }
  digitalWrite(kPin38, HIGH);
  rx = sx / 4;
  ry = sy / 4;
  return !(rx < 100 || rx > 4000 || ry < 100 || ry > 4000);
}

void xptInit() {
  pinMode(kPin38, OUTPUT);
  digitalWrite(kPin38, HIGH);
  pinMode(kSck, OUTPUT);
  digitalWrite(kSck, LOW);
  pinMode(kMosi, OUTPUT);
  pinMode(kMiso, INPUT);
  pinMode(kIrq, INPUT_PULLUP);
  int a, b;
  xptReadRaw(a, b);  // one read to arm PENIRQ
}

// ---------- GT911 (minimal register access, UNVERIFIED on owner's board) ----------
constexpr uint16_t kGtStatus = 0x814E;
constexpr uint16_t kGtPoint1 = 0x8150;

bool gtRead(uint16_t reg, uint8_t* buf, size_t n) {
  Wire.beginTransmission(g_gtAddr);
  Wire.write(static_cast<uint8_t>(reg >> 8));
  Wire.write(static_cast<uint8_t>(reg & 0xFF));
  if (Wire.endTransmission() != 0) return false;
  if (Wire.requestFrom(static_cast<uint16_t>(g_gtAddr), static_cast<size_t>(n), true) != n)
    return false;
  for (size_t i = 0; i < n; i++) buf[i] = Wire.read();
  return true;
}

bool gtWrite8(uint16_t reg, uint8_t v) {
  Wire.beginTransmission(g_gtAddr);
  Wire.write(static_cast<uint8_t>(reg >> 8));
  Wire.write(static_cast<uint8_t>(reg & 0xFF));
  Wire.write(v);
  return Wire.endTransmission() == 0;
}

bool gtReadRaw(int& rx, int& ry) {
  uint8_t status = 0;
  if (!gtRead(kGtStatus, &status, 1)) return false;
  if (!(status & 0x80)) return false;  // buffer not ready
  const uint8_t points = status & 0x0F;
  bool got = false;
  if (points > 0 && points <= 5) {
    uint8_t p[4];
    if (gtRead(kGtPoint1, p, sizeof(p))) {
      rx = p[0] | (p[1] << 8);
      ry = p[2] | (p[3] << 8);
      got = true;
    }
  }
  gtWrite8(kGtStatus, 0);  // tell the controller we consumed the data
  return got;
}

bool probeGt911() {
  Wire.begin(kSda, kScl, 400000);
  for (uint8_t a : {static_cast<uint8_t>(0x5D), static_cast<uint8_t>(0x14)}) {
    Wire.beginTransmission(a);
    if (Wire.endTransmission() == 0) {
      g_gtAddr = a;
      return true;
    }
  }
  Wire.end();  // release 8/4 on the R board
  return false;
}

int16_t clampTo(long v, int16_t hi) {
  if (v < 0) return 0;
  if (v > hi) return hi;
  return static_cast<int16_t>(v);
}

}  // namespace

Type begin() {
  if (probeGt911()) {
    g_type = Type::GT911;
    pinMode(kIrq, INPUT);
    Serial.printf("[touch] GT911 at 0x%02X (capacitive, C board)\n", g_gtAddr);
  } else {
    g_type = Type::XPT2046;
    xptInit();
    Serial.println("[touch] no GT911 on I2C -> assuming XPT2046 (resistive, R board)");
  }
  return g_type;
}

Type type() { return g_type; }

const char* typeName() {
  switch (g_type) {
    case Type::XPT2046: return "xpt2046";
    case Type::GT911: return "gt911";
    default: return "none";
  }
}

bool readRaw(int& rx, int& ry) {
  switch (g_type) {
    case Type::XPT2046: return xptReadRaw(rx, ry);
    case Type::GT911: return gtReadRaw(rx, ry);
    default: return false;
  }
}

bool read(int16_t& x, int16_t& y) {
  int rx, ry;
  if (!readRaw(rx, ry)) return false;
  Arduino_GFX* g = display::gfx();
  const int16_t w = g->width() - 1;
  const int16_t h = g->height() - 1;

  if (g_type == Type::GT911) {
    // Panel pixels in native landscape. Rotation mapping UNVERIFIED.
    switch (g->getRotation()) {
      case 1: x = clampTo(ry, w); y = clampTo(271 - rx, h); break;
      case 2: x = clampTo(479 - rx, w); y = clampTo(271 - ry, h); break;
      case 3: x = clampTo(271 - ry, w); y = clampTo(rx, h); break;
      default: x = clampTo(rx, w); y = clampTo(ry, h); break;
    }
    return true;
  }

  // XPT2046: map raw ADC -> screen with the constants in config.h
  if (XPT_SWAP_XY) {
    const int t = rx;
    rx = ry;
    ry = t;
  }
  long mx = map(rx, XPT_RAW_X_MIN, XPT_RAW_X_MAX, 0, w);
  long my = map(ry, XPT_RAW_Y_MIN, XPT_RAW_Y_MAX, 0, h);
  if (XPT_INVERT_X) mx = w - mx;
  if (XPT_INVERT_Y) my = h - my;
  x = clampTo(mx, w);
  y = clampTo(my, h);
  return true;
}

}  // namespace touch
