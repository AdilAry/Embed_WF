#include "display.h"

#include "../logic/text_wrap.h"

namespace display {

namespace {

constexpr int kBacklightPin = 1;
constexpr int kTitleSize = 3;
constexpr int kBodySize = 2;
constexpr int kStatusSize = 1;
constexpr int kMargin = 8;

// Proven init from the board file. No reset pin, IPS = true.
Arduino_DataBus* g_bus = new Arduino_ESP32QSPI(45 /*cs*/, 47 /*sck*/, 21 /*d0*/,
                                               48 /*d1*/, 40 /*d2*/, 39 /*d3*/);
Arduino_GFX* g_gfx = new Arduino_NV3041A(g_bus, GFX_NOT_DEFINED /*rst*/, 0 /*rotation*/,
                                         true /*IPS*/);
bool g_ok = false;
uint8_t g_backlight = 0;

uint16_t rgb(uint8_t r, uint8_t g, uint8_t b) { return g_gfx->color565(r, g, b); }

}  // namespace

bool begin(uint8_t rotation) {
  ledcAttach(kBacklightPin, 5000 /*Hz*/, 8 /*bits*/);  // core 3.x LEDC API
  setBacklight(0);
  g_ok = g_gfx->begin();
  if (!g_ok) {
    Serial.println("[display] gfx->begin() failed");
    return false;
  }
  g_gfx->setRotation(rotation);
  g_gfx->setTextWrap(false);  // we wrap ourselves, by word
  g_gfx->fillScreen(rgb(0, 0, 0));
  Serial.printf("[display] ok %dx%d rot=%u\n", g_gfx->width(), g_gfx->height(), rotation);
  return true;
}

bool ok() { return g_ok; }
Arduino_GFX* gfx() { return g_gfx; }

void setBacklight(uint8_t duty) {
  g_backlight = duty;
  ledcWrite(kBacklightPin, duty);
}

uint8_t backlight() { return g_backlight; }

void showText(const char* title, const char* text) {
  if (!g_ok) return;
  const int w = g_gfx->width();
  const int h = g_gfx->height();
  const int statusTop = h - 8 * kStatusSize - kMargin;

  g_gfx->fillRect(0, 0, w, statusTop, rgb(0, 0, 0));

  int y = kMargin;
  g_gfx->setTextSize(kTitleSize);
  g_gfx->setTextColor(rgb(0, 200, 255));
  g_gfx->setCursor(kMargin, y);
  g_gfx->print(title);
  y += 8 * kTitleSize + kMargin;

  g_gfx->setTextSize(kBodySize);
  g_gfx->setTextColor(rgb(255, 255, 255));
  const std::size_t maxChars = logic::maxCharsForWidth(w - 2 * kMargin, kBodySize);
  for (const std::string& line : logic::wrapText(text, maxChars)) {
    if (y + 8 * kBodySize > statusTop) break;  // out of room: drop the rest
    g_gfx->setCursor(kMargin, y);
    g_gfx->print(line.c_str());
    y += 8 * kBodySize + 4;
  }
}

void showStatus(const char* text) {
  if (!g_ok) return;
  const int w = g_gfx->width();
  const int h = g_gfx->height();
  const int top = h - 8 * kStatusSize - kMargin;
  g_gfx->fillRect(0, top, w, h - top, rgb(0, 0, 0));
  g_gfx->setTextSize(kStatusSize);
  g_gfx->setTextColor(rgb(160, 160, 160));
  g_gfx->setCursor(kMargin, top);
  g_gfx->print(text);
}

}  // namespace display
