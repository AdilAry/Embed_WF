#include "console.h"

#include <Arduino.h>
#include <esp_system.h>

#include <string>

#include "../config.h"
#include "../hal/display.h"
#include "../hal/touch.h"
#include "../logic/command.h"
#include "selftest.h"

namespace console {

namespace {

constexpr size_t kMaxLine = 200;
std::string g_line;

const char* resetReasonName(esp_reset_reason_t r) {
  switch (r) {
    case ESP_RST_POWERON: return "poweron";
    case ESP_RST_SW: return "software";
    case ESP_RST_PANIC: return "panic";
    case ESP_RST_INT_WDT: return "int_wdt";
    case ESP_RST_TASK_WDT: return "task_wdt";
    case ESP_RST_WDT: return "wdt";
    case ESP_RST_BROWNOUT: return "brownout";
    case ESP_RST_USB: return "usb";
    case ESP_RST_EXT: return "external";
    case ESP_RST_DEEPSLEEP: return "deepsleep";
    default: return "other";
  }
}

void cmdHelp() {
  Serial.println("commands:");
  Serial.println("  help              this list");
  Serial.println("  ping              -> PONG (liveness check)");
  Serial.println("  info              firmware, memory, reset reason, touch type");
  Serial.println("  selftest [touch=xpt2046|gt911]  run on-target tests (TEST:... lines)");
  Serial.println("  text <message>    show a word-wrapped message on the display");
  Serial.println("  bl <0..255>       set backlight");
  Serial.println("  touch             print one raw touch sample (press first)");
  Serial.println("  reboot            restart the chip");
}

void cmdInfo() {
  Serial.printf("INFO fw=%s ver=%s build=%s uptime_ms=%lu reset=%s heap=%lu psram=%lu/%lu touch=%s bl=%u\n",
                FW_NAME, FW_VERSION, FW_BUILD_ID, (unsigned long)millis(),
                resetReasonName(esp_reset_reason()), (unsigned long)ESP.getFreeHeap(),
                (unsigned long)ESP.getFreePsram(), (unsigned long)ESP.getPsramSize(),
                touch::typeName(), display::backlight());
}

void dispatch(const std::string& line) {
  const logic::Command c = logic::parseCommand(line);
  if (c.name.empty()) return;

  if (c.name == "help") {
    cmdHelp();
  } else if (c.name == "ping") {
    Serial.println("PONG");
  } else if (c.name == "info") {
    cmdInfo();
  } else if (c.name == "selftest") {
    // Optional "touch=<type>": the controller the tester knows this board has.
    std::string expectTouch;
    for (const std::string& arg : c.args) {
      if (arg.rfind("touch=", 0) == 0) expectTouch = arg.substr(6);
    }
    selftest::runAll(expectTouch.c_str());
  } else if (c.name == "text") {
    display::showText("Message", c.rest.c_str());
    Serial.println("OK");
  } else if (c.name == "bl") {
    long v;
    if (c.args.size() == 1 && logic::parseLong(c.args[0], 0, 255, v)) {
      display::setBacklight(static_cast<uint8_t>(v));
      Serial.println("OK");
    } else {
      Serial.println("ERR usage: bl <0..255>");
    }
  } else if (c.name == "touch") {
    int rx, ry;
    if (touch::readRaw(rx, ry)) {
      Serial.printf("TOUCH raw_x=%d raw_y=%d\n", rx, ry);
    } else {
      Serial.println("TOUCH none");
    }
  } else if (c.name == "reboot") {
    Serial.println("OK rebooting");
    Serial.flush();
    delay(50);
    ESP.restart();
  } else {
    Serial.printf("ERR unknown command '%s' (try help)\n", c.name.c_str());
  }
}

}  // namespace

void poll() {
  while (Serial.available() > 0) {
    const char ch = static_cast<char>(Serial.read());
    if (ch == '\n' || ch == '\r') {
      if (!g_line.empty()) {
        dispatch(g_line);
        g_line.clear();
      }
    } else if (g_line.size() < kMaxLine) {
      g_line += ch;
    }
  }
}

}  // namespace console
