// Project-wide constants. Change FW_NAME when you create a new project.
#pragma once

#define FW_NAME "template"
#define FW_VERSION "0.1.0"

// 0 = landscape 480x272 (native), 1 = portrait 272x480, 2/3 = flipped.
#define DISPLAY_ROTATION 0
#define BACKLIGHT_DEFAULT 200  // 0..255

// Rough XPT2046 (resistive, "R" board) calibration. Raw 12-bit ADC values seen
// at the screen edges in DISPLAY_ROTATION. Measure your own with the `touch`
// console command and replace these. GT911 ("C" board) needs none.
#define XPT_RAW_X_MIN 200
#define XPT_RAW_X_MAX 3900
#define XPT_RAW_Y_MIN 200
#define XPT_RAW_Y_MAX 3900
#define XPT_SWAP_XY false
#define XPT_INVERT_X false
#define XPT_INVERT_Y false

// Fingerprint of the source this firmware was built from. `make compile` writes
// build_id.h (git-ignored); the firmware prints it in `info` and `selftest`, and
// `make trace` uses it to tell whether a test result belongs to the current code.
// A build made without the Makefile (Arduino IDE) reports "unknown".
#if __has_include("build_id.h")
#include "build_id.h"
#else
#define FW_BUILD_ID "unknown"
#endif

// Optional secrets (Wi-Fi etc.). Copy secrets.example.h to secrets.h; the real
// file is git-ignored. Code checks HAVE_SECRETS before using them.
#if __has_include("secrets.h")
#include "secrets.h"
#define HAVE_SECRETS 1
#else
#define HAVE_SECRETS 0
#endif
