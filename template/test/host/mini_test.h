// Tiny dependency-free test framework for host tests (runs on the PC, not the ESP32).
// Usage:
//   TEST(name) { CHECK(cond); CHECK_EQ(a, b); }
// Output is one line per failure plus a summary; exit code = number of failed tests.
#pragma once

#include <cstdio>
#include <functional>
#include <sstream>
#include <string>
#include <vector>

namespace mini_test {

struct Case {
  const char* name;
  std::function<void()> fn;
};

inline std::vector<Case>& registry() {
  static std::vector<Case> r;
  return r;
}

inline int& currentFailures() {
  static int f = 0;
  return f;
}

struct Registrar {
  Registrar(const char* name, std::function<void()> fn) { registry().push_back({name, fn}); }
};

template <typename T>
std::string show(const T& v) {
  std::ostringstream os;
  os << v;
  return os.str();
}

inline int runAll() {
  int failedTests = 0;
  for (const Case& c : registry()) {
    currentFailures() = 0;
    c.fn();
    if (currentFailures() == 0) {
      std::printf("HOSTTEST:%s:PASS\n", c.name);
    } else {
      std::printf("HOSTTEST:%s:FAIL\n", c.name);
      ++failedTests;
    }
  }
  std::printf("HOSTTEST:DONE pass=%d fail=%d\n",
              static_cast<int>(registry().size()) - failedTests, failedTests);
  return failedTests;
}

}  // namespace mini_test

#define MT_CAT2(a, b) a##b
#define MT_CAT(a, b) MT_CAT2(a, b)

#define TEST(name)                                                              \
  static void MT_CAT(test_, name)();                                            \
  static mini_test::Registrar MT_CAT(reg_, name)(#name, MT_CAT(test_, name));   \
  static void MT_CAT(test_, name)()

#define CHECK(cond)                                                             \
  do {                                                                          \
    if (!(cond)) {                                                              \
      std::printf("  %s:%d: CHECK(%s) failed\n", __FILE__, __LINE__, #cond);    \
      ++mini_test::currentFailures();                                           \
    }                                                                           \
  } while (0)

#define CHECK_EQ(a, b)                                                          \
  do {                                                                          \
    const auto _va = (a);                                                       \
    const auto _vb = (b);                                                       \
    if (!(_va == _vb)) {                                                        \
      std::printf("  %s:%d: CHECK_EQ(%s, %s) failed: '%s' != '%s'\n", __FILE__, \
                  __LINE__, #a, #b, mini_test::show(_va).c_str(),               \
                  mini_test::show(_vb).c_str());                                \
      ++mini_test::currentFailures();                                           \
    }                                                                           \
  } while (0)
