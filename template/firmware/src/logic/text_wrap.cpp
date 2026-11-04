#include "text_wrap.h"

namespace logic {

namespace {

void flushWord(std::vector<std::string>& lines, std::string& line, std::string& word,
               std::size_t maxChars) {
  if (word.empty()) return;
  // Hard-split words that can never fit on a line.
  while (word.size() > maxChars) {
    if (!line.empty()) {
      lines.push_back(line);
      line.clear();
    }
    lines.push_back(word.substr(0, maxChars));
    word.erase(0, maxChars);
  }
  if (word.empty()) return;
  const std::size_t needed = line.empty() ? word.size() : line.size() + 1 + word.size();
  if (needed > maxChars) {
    lines.push_back(line);
    line = word;
  } else {
    if (!line.empty()) line += ' ';
    line += word;
  }
  word.clear();
}

}  // namespace

std::vector<std::string> wrapText(const std::string& text, std::size_t maxChars) {
  std::vector<std::string> lines;
  if (maxChars == 0) return lines;

  std::string line;
  std::string word;
  for (char c : text) {
    if (c == '\n') {
      flushWord(lines, line, word, maxChars);
      lines.push_back(line);
      line.clear();
    } else if (c == ' ' || c == '\t' || c == '\r') {
      flushWord(lines, line, word, maxChars);
    } else {
      word += c;
    }
  }
  flushWord(lines, line, word, maxChars);
  if (!line.empty()) lines.push_back(line);
  return lines;
}

std::size_t maxCharsForWidth(int pixelWidth, int textSize) {
  if (pixelWidth <= 0 || textSize <= 0) return 0;
  return static_cast<std::size_t>(pixelWidth / (6 * textSize));
}

}  // namespace logic
