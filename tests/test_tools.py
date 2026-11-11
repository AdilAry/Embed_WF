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
    results, _, stale = trace.load_results(root)
    trace.evaluate(reqs, trace.discover(root), results, stale)
    return {r.rid: r.status for r in reqs}


def _write_results(root: Path, board: str = "") -> None:
    """Results as the make targets leave them, stamped for the CURRENT source."""
    build = root / "build"
    build.mkdir(exist_ok=True)
    fw = trace.src_hash(root, "firmware")
    (build / "host-test.log").write_text(
        f"SRC:{trace.src_hash(root, 'host')}\n"
        "HOSTTEST:wrap_basic:PASS\nHOSTTEST:wrap_long:PASS\nHOSTTEST:DONE pass=2 fail=0\n")
    name = f"target-test.{board}.log" if board else "target-test.log"
    (build / name).write_text(
        f"SELFTEST:BEGIN build={fw}\nTEST:T-PSRAM:PASS:psram=8388608\nTEST:T-HEAP:PASS:x\n"
        "SELFTEST:DONE pass=2 fail=0\n")
    (build / "bench-test.xml").write_text(
        '<testsuites><testsuite><testcase name="test_req_030_reconnect"/></testsuite></testsuites>')
    (build / "bench-test.stamp").write_text(f"fw={fw} tests={trace.src_hash(root, 'bench')}\n")


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
    _write_results(root)
    build = root / "build"
    host = build / "host-test.log"
    host.write_text(host.read_text().replace("wrap_long:PASS", "wrap_long:FAIL"))
    (build / "bench-test.xml").write_text(
        '<testsuites><testsuite><testcase name="test_req_030_reconnect"><skipped/></testcase>'
        "</testsuite></testsuites>")
    s = _status(root)
    assert s["REQ-010"] == "FAIL"      # one of the wrap_* tests failed
    assert s["REQ-020"] == "PASS"
    assert s["REQ-030"] == "SKIPPED"
    assert s["REQ-060"] == "PASS"


def test_trace_all_green_when_results_match_the_source(tmp_path):
    root = _project(tmp_path)
    _write_results(root)
    s = _status(root)
    assert (s["REQ-010"], s["REQ-020"], s["REQ-030"]) == ("PASS", "PASS", "PASS")
    assert trace.main(["--root", str(root), "--require-run", "REQ-010", "REQ-020", "REQ-030"]) == 0


def test_trace_marks_results_stale_after_the_source_changes(tmp_path):
    """The gate must not accept a PASS that was produced by older code."""
    root = _project(tmp_path)
    _write_results(root)
    (root / "firmware" / "src" / "logic").mkdir()
    (root / "firmware" / "src" / "logic" / "wrap.cpp").write_text("// changed after the test run\n")
    s = _status(root)
    assert s["REQ-010"] == "STALE"     # host: logic changed
    assert s["REQ-020"] == "STALE"     # target: firmware on the board is an older build
    assert s["REQ-030"] == "STALE"     # bench: same
    assert trace.main(["--root", str(root), "--require-run", "REQ-010"]) == 1
    assert trace.main(["--root", str(root), "--strict", "REQ-010"]) == 0   # like NOT RUN


def test_trace_result_without_a_stamp_is_stale(tmp_path):
    root = _project(tmp_path)
    (root / "build").mkdir()
    (root / "build" / "host-test.log").write_text("HOSTTEST:wrap_basic:PASS\nHOSTTEST:wrap_long:PASS\n")
    (root / "build" / "target-test.log").write_text("SELFTEST:BEGIN\nTEST:T-PSRAM:PASS:x\n")
    s = _status(root)
    assert s["REQ-010"] == "STALE" and s["REQ-020"] == "STALE"


def test_src_hash_ignores_generated_and_secret_files(tmp_path):
    root = _project(tmp_path)
    before = trace.src_hash(root, "firmware")
    src = root / "firmware" / "src"
    trace.write_build_id(root, src / "build_id.h")
    (src / "secrets.h").write_text('#define WIFI_PASS "x"\n')
    (root / "test" / "bench" / "__pycache__").mkdir()
    (root / "test" / "bench" / "__pycache__" / "x.pyc").write_text("junk")
    assert trace.src_hash(root, "firmware") == before
    assert before in (src / "build_id.h").read_text()
    (src / "selftest.cpp").write_text("// edited\n")
    assert trace.src_hash(root, "firmware") != before


def test_trace_per_board_requirement_needs_both_boards(tmp_path):
    """`T-PSRAM@R, T-PSRAM@C` is only proven by a run on each registered board."""
    root = _project(tmp_path)
    fsd = root / "docs" / "FSD.md"
    fsd.write_text(fsd.read_text().replace("| target | T-PSRAM |", "| target | T-PSRAM@R, T-PSRAM@C |"))
    _write_results(root)                       # last run only, board unknown
    assert _status(root)["REQ-020"] == "NOT RUN"
    _write_results(root, board="R")
    assert _status(root)["REQ-020"] == "NOT RUN"   # C still missing
    _write_results(root, board="C")
    assert _status(root)["REQ-020"] == "PASS"
    c_log = root / "build" / "target-test.C.log"
    c_log.write_text(c_log.read_text().replace("T-PSRAM:PASS", "T-PSRAM:FAIL"))
    assert _status(root)["REQ-020"] == "FAIL"


def test_trace_board_suffix_is_only_valid_for_target_tests(tmp_path):
    root = _project(tmp_path)
    fsd = root / "docs" / "FSD.md"
    fsd.write_text(fsd.read_text().replace("| host | wrap_* |", "| host | wrap_basic@R |"))
    assert _status(root)["REQ-010"] == "NO TEST"


# ------------------------------------------------- esp_serial.py board registry
PORTS = [("/dev/ttyACM0", 0x303A, "AA:AA"), ("/dev/ttyACM1", 0x303A, "BB:BB"),
         ("/dev/ttyUSB0", 0x10C4, None)]


def test_parse_boards():
    text = "# comment\nAA:AA R\nBB:BB c   # my capacitive one\n\nbroken-line\n"
    assert esp_serial.parse_boards(text) == {"AA:AA": "R", "BB:BB": "C"}


def test_pick_port_by_registered_board():
    boards = {"AA:AA": "R", "BB:BB": "C"}
    assert esp_serial.pick_port(PORTS, boards, "C") == "/dev/ttyACM1"
    assert esp_serial.pick_port(PORTS, boards, "r") == "/dev/ttyACM0"
    assert esp_serial.pick_port(PORTS, {"AA:AA": "R"}, "C") is None   # never guess another board


def test_pick_port_without_board_prefers_espressif():
    assert esp_serial.pick_port(list(reversed(PORTS)), {}) == "/dev/ttyACM1"
    assert esp_serial.pick_port([PORTS[2]], {}) == "/dev/ttyUSB0"
    assert esp_serial.pick_port([], {}) is None


def test_selftest_tells_the_firmware_which_touch_to_expect():
    assert esp_serial.selftest_command(esp_serial.BOARD_TOUCH["C"]) == "selftest touch=gt911"
    assert esp_serial.selftest_command(esp_serial.BOARD_TOUCH["R"]) == "selftest touch=xpt2046"
    assert esp_serial.selftest_command(None) == "selftest"


def test_board_report_path():
    assert esp_serial.board_report_path(Path("build/target-test.log"), "C") == Path("build/target-test.C.log")


def test_port_and_board_come_from_the_environment(monkeypatch):
    """`make loop PORT=...` exports ESP_PORT so every step uses the same board."""
    seen = {}
    monkeypatch.setenv("ESP_PORT", "/dev/ttyACM9")
    monkeypatch.setenv("ESP_BOARD", "c")
    monkeypatch.setattr(esp_serial, "cmd_detect", lambda args: seen.update(vars(args)) or 0)
    assert esp_serial.main(["detect"]) == 0
    assert seen["port"] == "/dev/ttyACM9" and seen["board"] == "C"


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
