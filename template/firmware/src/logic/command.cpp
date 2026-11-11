#include "command.h"

#include <cctype>
#include <cerrno>
#include <cstdlib>

namespace logic {

namespace {

bool isSpace(char c) { return c == ' ' || c == '\t' || c == '\r' || c == '\n'; }

std::string trim(const std::string& s) {
  std::size_t b = 0;
  std::size_t e = s.size();
  while (b < e && isSpace(s[b])) ++b;
  while (e > b && isSpace(s[e - 1])) --e;
  return s.substr(b, e - b);
}

}  // namespace

Command parseCommand(const std::string& line) {
  Command cmd;
  const std::string t = trim(line);
  std::size_t i = 0;
  bool first = true;
  while (i < t.size()) {
    while (i < t.size() && isSpace(t[i])) ++i;
    const std::size_t start = i;
    while (i < t.size() && !isSpace(t[i])) ++i;
    if (start == i) break;
    std::string word = t.substr(start, i - start);
    if (first) {
      for (char& c : word) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
      cmd.name = word;
      cmd.rest = trim(t.substr(i));
      first = false;
    } else {
      cmd.args.push_back(word);
    }
  }
  return cmd;
}

bool parseLong(const std::string& s, long minValue, long maxValue, long& out) {
  if (s.empty()) return false;
  errno = 0;
  char* end = nullptr;
  const long v = std::strtol(s.c_str(), &end, 10);
  if (errno != 0 || end == s.c_str() || *end != '\0') return false;
  if (v < minValue || v > maxValue) return false;
  out = v;
  return true;
}

}  // namespace logic
