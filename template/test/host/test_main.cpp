// Host-tier tests: compile firmware/src/logic/*.cpp with the PC compiler and
// check behaviour in milliseconds. Run with `make host-test`.
// Rule of thumb: every pure-logic requirement in docs/FSD.md gets a test here.
#include <string>
#include <vector>

#include "logic/command.h"
#include "logic/text_wrap.h"
#include "mini_test.h"

using logic::Command;
using logic::parseCommand;
using logic::parseLong;
using logic::wrapText;
using Lines = std::vector<std::string>;

// ---------- text wrapping ----------
TEST(wrap_basic) {
  const Lines l = wrapText("hello embedded world", 14);
  CHECK_EQ(l.size(), 2u);
  CHECK_EQ(l[0], std::string("hello embedded"));
  CHECK_EQ(l[1], std::string("world"));
}

TEST(wrap_fits_on_one_line) {
  const Lines l = wrapText("short", 20);
  CHECK_EQ(l.size(), 1u);
  CHECK_EQ(l[0], std::string("short"));
}

TEST(wrap_collapses_spaces) {
  const Lines l = wrapText("  a    b  ", 10);
  CHECK_EQ(l.size(), 1u);
  CHECK_EQ(l[0], std::string("a b"));
}

TEST(wrap_hard_splits_long_word) {
  const Lines l = wrapText("abcdefghij", 4);
  CHECK_EQ(l.size(), 3u);
  CHECK_EQ(l[0], std::string("abcd"));
  CHECK_EQ(l[1], std::string("efgh"));
  CHECK_EQ(l[2], std::string("ij"));
}

TEST(wrap_long_word_after_text) {
  const Lines l = wrapText("hi abcdefgh", 4);
  CHECK_EQ(l.size(), 3u);
  CHECK_EQ(l[0], std::string("hi"));
  CHECK_EQ(l[1], std::string("abcd"));
  CHECK_EQ(l[2], std::string("efgh"));
}

TEST(wrap_newline_forces_break) {
  const Lines l = wrapText("a\n\nb", 10);
  CHECK_EQ(l.size(), 3u);
  CHECK_EQ(l[0], std::string("a"));
  CHECK_EQ(l[1], std::string(""));
  CHECK_EQ(l[2], std::string("b"));
}

TEST(wrap_exact_width) {
  const Lines l = wrapText("abcd efgh", 9);
  CHECK_EQ(l.size(), 1u);
  CHECK_EQ(l[0], std::string("abcd efgh"));
}

TEST(wrap_zero_width_and_empty) {
  CHECK(wrapText("anything", 0).empty());
  CHECK(wrapText("", 10).empty());
}

TEST(max_chars_for_width) {
  CHECK_EQ(logic::maxCharsForWidth(480, 1), 80u);
  CHECK_EQ(logic::maxCharsForWidth(464, 2), 38u);  // 480 - 2*8 margin, size 2
  CHECK_EQ(logic::maxCharsForWidth(0, 2), 0u);
  CHECK_EQ(logic::maxCharsForWidth(480, 0), 0u);
}

// ---------- command parsing ----------
TEST(cmd_basic) {
  const Command c = parseCommand("  BL 128 ");
  CHECK_EQ(c.name, std::string("bl"));
  CHECK_EQ(c.args.size(), 1u);
  CHECK_EQ(c.args[0], std::string("128"));
  CHECK_EQ(c.rest, std::string("128"));
}

TEST(cmd_rest_keeps_text) {
  const Command c = parseCommand("text Hello  World\r");
  CHECK_EQ(c.name, std::string("text"));
  CHECK_EQ(c.rest, std::string("Hello  World"));
  CHECK_EQ(c.args.size(), 2u);
}

TEST(cmd_blank) {
  CHECK(parseCommand("").name.empty());
  CHECK(parseCommand("   \t ").name.empty());
}

TEST(parse_long_accepts_valid) {
  long v = -1;
  CHECK(parseLong("0", 0, 255, v));
  CHECK_EQ(v, 0L);
  CHECK(parseLong("255", 0, 255, v));
  CHECK_EQ(v, 255L);
}

TEST(parse_long_rejects_garbage) {
  long v = 7;
  CHECK(!parseLong("", 0, 255, v));
  CHECK(!parseLong("12x", 0, 255, v));
  CHECK(!parseLong("256", 0, 255, v));
  CHECK(!parseLong("-1", 0, 255, v));
  CHECK_EQ(v, 7L);  // untouched on failure
}

int main() { return mini_test::runAll(); }
