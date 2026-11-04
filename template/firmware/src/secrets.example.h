// Copy to secrets.h (same folder) and fill in. secrets.h is in .gitignore.
// Never commit real credentials. For bench tests use the throw-away test
// access point created by `bench-wifi up`, not your home network.
#pragma once

#define WIFI_SSID "embtest"
#define WIFI_PASS "change-me-123"
#define MQTT_HOST "10.42.0.1"  // the dev box when it runs the test hotspot
#define MQTT_PORT 1883
