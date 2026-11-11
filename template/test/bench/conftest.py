"""Shared fixtures for bench-tier tests (tier 3).

Bench tests talk to the real board AND to the environment around it: the dev
box's test Wi-Fi hotspot (`bench-wifi`), its MQTT broker (`bench-mqtt`), BLE, etc.
They are slower than target tests, so only use them for behaviour that cannot
be proven by host or target tests.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

PROJECT = Path(__file__).resolve().parents[2]
ESP_SERIAL = [sys.executable, str(PROJECT / "tools" / "esp_serial.py")]


class Device:
    """Thin wrapper around tools/esp_serial.py so tests read like sentences.

    Which board: whatever `make bench-test PORT=... / BOARD=...` selected (the
    Makefile passes it on as $ESP_PORT / $ESP_BOARD), else the first one found.
    Every call opens the serial port afresh; `make open-check` proves that this
    does not reset the board.
    """

    def run(self, *args: str, timeout: float = 60) -> subprocess.CompletedProcess:
        return subprocess.run(ESP_SERIAL + list(args), capture_output=True, text=True,
                              timeout=timeout, cwd=PROJECT)

    def command(self, cmd: str, until: str | None = None, seconds: float = 3) -> str:
        args = ["cmd", *cmd.split(), "-s", str(seconds)]
        if until:
            args += ["--until", until]
        res = self.run(*args)
        assert res.returncode == 0, f"'{cmd}' failed (rc={res.returncode}):\n{res.stdout}\n{res.stderr}"
        return res.stdout

    def wait_for(self, cmd: str, pattern: str, timeout: float = 30, every: float = 1.0) -> str:
        """Ask `cmd` again and again until its reply matches `pattern` (a regex).

        Use this for state that changes over time ("wifi status" turning into
        "WIFI connected"). `command(..., until=...)` asks only ONCE and then just
        listens, so it only works if the firmware prints the change by itself.
        """
        deadline = time.monotonic() + timeout
        last = ""
        while time.monotonic() < deadline:
            res = self.run("cmd", *cmd.split(), "-s", "2")
            last = res.stdout
            if res.returncode == 0 and re.search(pattern, last, re.M):
                return last
            time.sleep(every)
        raise AssertionError(f"'{cmd}' never matched /{pattern}/ within {timeout}s. Last reply:\n{last}")

    def info(self) -> dict[str, str]:
        out = self.command("info", until="^INFO")
        line = next(ln for ln in out.splitlines() if ln.startswith("INFO "))
        return dict(kv.split("=", 1) for kv in line.split()[1:] if "=" in kv)


@pytest.fixture(scope="session")
def device() -> Device:
    res = subprocess.run(ESP_SERIAL + ["detect"], capture_output=True, text=True)
    if res.returncode != 0:
        pytest.skip("no ESP32 connected")
    return Device()


def _have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


@pytest.fixture
def wifi_ap():
    """Bring the dev box test hotspot up for one test, then down again."""
    if not _have("bench-wifi"):
        pytest.skip("bench-wifi not installed (run Embed_WF/devbox/setup-user.sh)")
    subprocess.run(["bench-wifi", "up"], check=True)
    yield
    subprocess.run(["bench-wifi", "down"], check=False)


@pytest.fixture
def mqtt_broker():
    """Local Mosquitto on the dev box; tests may stop it to inject faults."""
    if not _have("bench-mqtt"):
        pytest.skip("bench-mqtt not installed (run Embed_WF/devbox/setup-user.sh)")
    subprocess.run(["bench-mqtt", "start"], check=True)
    yield
    subprocess.run(["bench-mqtt", "stop"], check=False)
