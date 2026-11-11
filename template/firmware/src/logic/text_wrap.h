// Pure C++ logic: word wrapping for fixed-width fonts.
//
// RULE: nothing in src/logic/ may include Arduino.h or any ESP-IDF header.
// That is what lets `make host-test` compile and test it on the PC in under a
// second, before we spend minutes compiling and flashing firmware.
#pragma once

#include <cstddef>
#include <string>
#include <vector>

namespace logic {

// Split `text` into lines of at most `maxChars` characters.
//  - Breaks on spaces; runs of spaces collapse to one.
//  - '\n' forces a line break (an empty line is kept).
//  - A word longer than maxChars is hard-split.
//  - maxChars == 0 returns an empty vector.
std::vector<std::string> wrapText(const std::string& text, std::size_t maxChars);

// Characters that fit on one line: pixel width / (6 px * text size).
// The Arduino_GFX built-in font is 6x8 px per text-size unit.
std::size_t maxCharsForWidth(int pixelWidth, int textSize);

}  // namespace logic
