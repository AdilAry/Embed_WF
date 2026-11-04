// Pure C++ logic: parsing of the serial console commands.
// No Arduino.h here (see text_wrap.h for why).
#pragma once

#include <string>
#include <vector>

namespace logic {

struct Command {
  std::string name;               // lower-cased first word, "" for a blank line
  std::vector<std::string> args;  // remaining words, case preserved
  std::string rest;               // everything after the name, trimmed (for free text)
};

// "  BL 128 " -> {name:"bl", args:{"128"}, rest:"128"}
Command parseCommand(const std::string& line);

// Strict decimal integer parse with range check. Returns false on any garbage.
bool parseLong(const std::string& s, long minValue, long maxValue, long& out);

}  // namespace logic
