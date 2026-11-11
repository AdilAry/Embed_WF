"""Bench smoke tests: the board is alive and the console works end to end.

Project-specific bench tests (Wi-Fi provisioning, MQTT outage, BLE ...) go in
new files next to this one. Name each test after the FSD requirement it proves,
e.g. test_req_020_reconnects_after_wifi_loss.
"""


def test_console_ping(device):
    assert "PONG" in device.command("ping", until="PONG")


def test_info_reports_healthy_boot(device):
    info = device.info()
    assert info["reset"] not in {"panic", "int_wdt", "task_wdt", "wdt", "brownout"}
    assert int(info["psram"].split("/")[1]) >= 4 * 1024 * 1024, "PSRAM not enabled - check FQBN PSRAM=opi"


def test_text_command_accepted(device):
    assert "OK" in device.command("text bench test says hello", until="^OK")


def test_unknown_command_is_rejected(device):
    assert "ERR unknown command" in device.command("frobnicate", until="^ERR")


# Example of a fault-injection test - enable once your firmware has Wi-Fi.
#
# def test_req_020_reconnects_after_wifi_loss(device, wifi_ap):
#     device.wait_for("wifi status", "^WIFI connected", timeout=30)
#     subprocess.run(["bench-wifi", "down"], check=True)
#     device.wait_for("wifi status", "^WIFI disconnected", timeout=15)
#     subprocess.run(["bench-wifi", "up"], check=True)
#     device.wait_for("wifi status", "^WIFI connected", timeout=30)
