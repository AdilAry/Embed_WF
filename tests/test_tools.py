"""Tests for the Python tools shipped in template/tools (run by the `template` CI job).

    python3 -m pytest -q tests
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "template" / "tools"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclasses need the module registered
    spec.loader.exec_module(mod)
    return mod


trace = _load("trace")
esp_serial = _load("esp_serial")


# ------------------------------------------------------------ esp_serial.py
@pytest.mark.parametrize("line", [
    "Guru Meditation Error: Core  1 panic'ed (LoadProhibited). Exception was unhandled.",
    "Backtrace: 0x42002a3c:0x3fcebd40 0x42005e1d:0x3fcebd60",
    "abort() was called at PC 0x42008f1b on core 0",
    "E (12345) task_wdt: Task watchdog got triggered. The following tasks did not reset the watchdog in time:",
    "Brownout detector was triggered",
    "rst:0x8 (TG1WDT_SYS_RST),boot:0x8 (SPI_FAST_FLASH_BOOT)",
    "rst:0x7 (TG0WDT_SYS_RST),boot:0x8 (SPI_FAST_FLASH_BOOT)",
    "rst:0x10 (RTCWDT_RTC_RST),boot:0x8 (SPI_FAST_FLASH_BOOT)",
    "assert failed: xQueueSemaphoreTake queue.c:1545 (pxQueue->uxItemSize == 0)",
    "Stack canary watchpoint triggered (loopTask)",
])
def test_crash_lines_are_detected(line):
    assert esp_serial.is_crash(line)


@pytest.mark.parametrize("line", [
    "BOOT:OK fw=template ver=0.1.0 display=1 touch=xpt2046 boot_ms=812",
    "rst:0x1 (POWERON),boot:0x8 (SPI_FAST_FLASH_BOOT)",
    "rst:0x15 (USB_UART_CHIP_RESET),boot:0x8 (SPI_FAST_FLASH_BOOT)",
    "[touch] press x=10 y=20",
    "TEST:T-HEAP:PASS:free_heap=250000",
])
def test_normal_lines_are_not_crashes(line):
    assert not esp_serial.is_crash(line)


def test_parse_kv():
    assert esp_serial.parse_kv("INFO fw=x reset=poweron psram=1/2 junk") == {
        "fw": "x", "reset": "poweron", "psram": "1/2"}


def test_parse_selftest_counts_and_failures():
    lines = ["SELFTEST:BEGIN", "TEST:T-A:PASS:x", "TEST:T-B:FAIL:y", "SELFTEST:DONE pass=1 fail=1"]
    assert esp_serial.parse_selftest(lines) == (1, 1, ["TEST:T-B:FAIL:y"])


def test_parse_selftest_fail_line_beats_done_line():
    # A firmware bug that miscounts must not turn a FAIL into a green run.
    assert esp_serial.parse_selftest(["TEST:T-B:FAIL:y", "SELFTEST:DONE pass=5 fail=0"])[1] == 1


def test_parse_selftest_incomplete():
    assert esp_serial.parse_selftest(["TEST:T-A:PASS:x"]) is None


# ----------------------------------------------------------------- trace.py
FSD = """# Functional Specification
| ID | Requirement | Tier | Test |
|---|---|---|---|
| REQ-010 | Wraps text. | host | wrap_* |
| REQ-020 | PSRAM present. | target | T-PSRAM |
| REQ-030 | Reconnects after Wi-Fi loss. | bench | test_req_030_reconnect |
| REQ-040 | Looks nice. | manual | |
| REQ-050 | Parses MBus frames. | host | mbus_decode |
| REQ-060 | Heap ok. | target | `T-HEAP` |
| REQ-070 | Bad tier. | hardware | x |
| REQ-… | | | |
"""


def _project(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "FSD.md").write_text(FSD)
    (tmp_path / "test" / "host").mkdir(parents=True)
    (tmp_path / "test" / "host" / "t.cpp").write_text(
        "TEST(wrap_basic) {}\nTEST(wrap_long) {}\nTEST(cmd_x) {}\n")
    (tmp_path / "test" / "bench").mkdir(parents=True)
    (tmp_path / "test" / "bench" / "test_wifi.py").write_text(
        "def test_req_030_reconnect(device):\n    pass\n")
    (tmp_path / "firmware" / "src").mkdir(parents=True)
    (tmp_path / "firmware" / "src" / "selftest.cpp").write_text(
        'report("T-PSRAM", ok, "x");\n  report( "T-HEAP", ok, "y");\n')
    return tmp_path


def _status(root: Path) -> dict[str, str]:
    reqs = trace.parse_fsd((root / "docs" / "FSD.md").read_text())
    results, _ = trace.load_results(root)
    trace.evaluate(reqs, trace.discover(root), results)
    return {r.rid: r.status for r in reqs}


def test_parse_fsd_skips_placeholder_rows():
    reqs = trace.parse_fsd(FSD)
    assert [r.rid for r in reqs] == ["REQ-010", "REQ-020", "REQ-030", "REQ-040",
                                     "REQ-050", "REQ-060", "REQ-070"]
    assert reqs[5].tests == ["T-HEAP"]  # backticks stripped


def test_trace_before_any_run(tmp_path):
    s = _status(_project(tmp_path))
    assert s == {"REQ-010": "NOT RUN", "REQ-020": "NOT RUN", "REQ-030": "NOT RUN",
                 "REQ-040": "MANUAL", "REQ-050": "NO TEST", "REQ-060": "NOT RUN",
                 "REQ-070": "BAD TIER"}


def test_trace_with_results(tmp_path):
    root = _project(tmp_path)
    build = root / "build"
    build.mkdir()
    (build / "host-test.log").write_text(
        "HOSTTEST:wrap_basic:PASS\nHOSTTEST:wrap_long:FAIL\nHOSTTEST:DONE pass=1 fail=1\n")
    (build / "target-test.log").write_text(
        "TEST:T-PSRAM:PASS:psram=8388608\nTEST:T-HEAP:PASS:x\nSELFTEST:DONE pass=2 fail=0\n")
    (build / "bench-test.xml").write_text(
        '<testsuites><testsuite><testcase name="test_req_030_reconnect"><skipped/></testcase>'
        "</testsuite></testsuites>")
    s = _status(root)
    assert s["REQ-010"] == "FAIL"      # one of the wrap_* tests failed
    assert s["REQ-020"] == "PASS"
    assert s["REQ-030"] == "SKIPPED"
    assert s["REQ-060"] == "PASS"


def test_trace_cli_exit_codes(tmp_path, capsys):
    root = str(_project(tmp_path))
    assert trace.main(["--root", root]) == 0                    # report only
    assert trace.main(["--root", root, "--strict"]) == 1        # REQ-050 has no test
    assert trace.main(["--root", root, "--strict", "REQ-020"]) == 0   # not run is ok for --strict
    assert trace.main(["--root", root, "--require-run", "REQ-020"]) == 1
    assert trace.main(["--root", root, "REQ-999"]) == 4
    assert "REQ-050 | host | NO TEST" in capsys.readouterr().out


def test_trace_hints_at_wrong_tier(tmp_path):
    root = _project(tmp_path)
    fsd = root / "docs" / "FSD.md"
    fsd.write_text(fsd.read_text().replace("| target | T-PSRAM |", "| host | T-PSRAM |"))
    reqs = trace.parse_fsd(fsd.read_text())
    trace.evaluate(reqs, trace.discover(root), {t: {} for t in trace.AUTO_TIERS})
    r = next(r for r in reqs if r.rid == "REQ-020")
    assert r.status == "NO TEST" and "another tier" in r.detail


def test_template_fsd_is_fully_traceable():
    """The template's own FSD must point only at tests that exist."""
    root = TOOLS.parent
    assert trace.main(["--root", str(root), "--strict"]) == 0


class _FakeLink:
    def __init__(self, lines):
        self._lines = lines

    def lines(self, _deadline):
        yield from self._lines


@pytest.mark.parametrize("after_boot, rc", [
    (["[touch] press x=1 y=2"], esp_serial.EXIT_OK),
    (["Guru Meditation Error: Core 0 panic'ed"], esp_serial.EXIT_FAIL),
    (["[boot] template v0.1.0", "BOOT:OK fw=template"], esp_serial.EXIT_FAIL),  # boot loop
])
def test_bootcheck_settle(after_boot, rc):
    assert esp_serial._settle(_FakeLink(after_boot), 0.1) == rc
