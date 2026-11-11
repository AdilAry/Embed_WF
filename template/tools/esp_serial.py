#!/usr/bin/env python3
"""Non-interactive serial tool for ESP32 boards - the AI agent's "eyes".

An interactive serial monitor never exits, which is useless for an agent. Every
command here has a timeout and returns an exit code, so it fits in a loop:

    esp_serial.py detect                       print the first ESP32 port
    esp_serial.py list                         list all serial ports
    esp_serial.py monitor -s 10                print output for 10 s
    esp_serial.py monitor --reset --expect "BOOT:OK" --fail "panic|Guru"
    esp_serial.py cmd info                     send a console command, print reply
    esp_serial.py selftest                     run on-target tests, exit 0 if all pass
    esp_serial.py register R                   remember the plugged-in board as R (or C)
    esp_serial.py opencheck                    does opening the port reset the board?

Which board: -p PORT (or $ESP_PORT), else --board R|C (or $ESP_BOARD, needs
`register` once per board), else the first ESP32 found. The Makefile sets the
environment variables from PORT= / BOARD=, so every step uses the same board.

Exit codes: 0 ok | 1 test/fail-pattern hit | 2 timeout | 3 port problem | 4 usage
Everything received is also appended to build/serial.log (override with --log).

Needs pyserial (installed by Embed_WF/devbox/setup-root.sh as python3-serial).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover - lets the pure helpers be imported by tests
    serial = None  # type: ignore[assignment]
    list_ports = None  # type: ignore[assignment]

ESPRESSIF_VID = 0x303A  # native USB (ESP32-S3/C3 USB-Serial-JTAG)
USB_UART_VIDS = {0x10C4, 0x1A86, 0x0403}  # CP210x, CH340, FTDI on other dev boards
# Lines that mean "the firmware crashed". Covers the ESP-IDF panic handler, asserts,
# stack overflows, the task watchdog and the ROM's reset-reason line after a
# watchdog or brownout reset (e.g. "rst:0x8 (TG1WDT_SYS_RST)" on the S3).
CRASH_PATTERNS = [
    r"Guru Meditation Error",
    r"abort\(\) was called",
    r"Backtrace:",
    r"Brownout detector",
    r"Stack canary watchpoint triggered",
    r"\*\*\*ERROR\*\*\* A stack overflow",
    r"Task watchdog got triggered",
    r"assert failed:",
    r"rst:0x[0-9a-f]+ \((?:TG\d?WDT|RTCWDT|RTC_WDT|SUPER_WDT|MWDT\d?|LP_WDT|BROWN_OUT)",
]
DEFAULT_FAIL = "|".join(CRASH_PATTERNS)
BAD_RESET_REASONS = {"panic", "int_wdt", "task_wdt", "wdt", "brownout"}

EXIT_OK, EXIT_FAIL, EXIT_TIMEOUT, EXIT_PORT, EXIT_USAGE = 0, 1, 2, 3, 4

_CRASH_RE = re.compile(DEFAULT_FAIL)
_DONE_RE = re.compile(r"SELFTEST:DONE pass=(\d+) fail=(\d+)")


def is_crash(line: str) -> bool:
    """True if a serial line is a crash / watchdog / brownout signature."""
    return bool(_CRASH_RE.search(line))


def parse_kv(line: str) -> dict[str, str]:
    """'INFO fw=x reset=poweron heap=1' -> {'fw': 'x', 'reset': 'poweron', 'heap': '1'}."""
    return dict(kv.split("=", 1) for kv in line.split()[1:] if "=" in kv)


def parse_selftest(lines) -> tuple[int, int, list[str]] | None:
    """Summarise selftest output. Returns (passed, failed, FAIL lines), or None if
    SELFTEST:DONE never appeared. A FAIL line wins over a DONE line claiming fail=0."""
    failures = [ln for ln in lines if ln.startswith("TEST:") and ":FAIL:" in ln]
    for ln in lines:
        m = _DONE_RE.search(ln)
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
            return passed, max(failed, len(failures)), failures
    return None


def _need_pyserial() -> None:
    if serial is None:
        print("pyserial missing: sudo apt install python3-serial  (or pip install pyserial)",
              file=sys.stderr)
        sys.exit(EXIT_PORT)


# ---- board registry -------------------------------------------------------
# The owner has two boards that look the same to USB. Each has a unique USB
# serial number, so one line per board in ~/.config/embwf/boards
#
#     <usb-serial-number> <variant>          e.g.  34:85:18:AB:CD:EF R
#
# (written by `esp_serial.py register R`) lets the tools pick a board by name
# when both are plugged in, and tells the selftest which touch controller it
# MUST find. Without that, a C board whose GT911 is not detected would quietly
# be treated as an R board and still pass.
BOARD_TOUCH = {"R": "xpt2046", "C": "gt911"}


def boards_file() -> Path:
    override = os.environ.get("EMBWF_BOARDS")
    if override:
        return Path(override)
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "embwf" / "boards"


def parse_boards(text: str) -> dict[str, str]:
    """'<serial> <variant>' lines -> {serial: VARIANT}. '#' starts a comment."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split("#", 1)[0].split()
        if len(parts) >= 2:
            out[parts[0]] = parts[1].upper()
    return out


def load_boards() -> dict[str, str]:
    try:
        return parse_boards(boards_file().read_text(encoding="utf-8"))
    except OSError:
        return {}


def pick_port(ports, boards: dict[str, str], board: str | None = None) -> str | None:
    """Choose a device from ports = [(device, usb_vid, usb_serial_number), ...].

    With `board` ("R"/"C"): only the port whose serial number is registered as
    that variant. Without: the first Espressif device, then common USB-UART
    bridges, then any ttyACM/ttyUSB.
    """
    if board:
        for device, _vid, serial_number in ports:
            if serial_number and boards.get(serial_number) == board.upper():
                return device
        return None
    for vids in ({ESPRESSIF_VID}, USB_UART_VIDS):
        for device, vid, _serial_number in ports:
            if vid in vids:
                return device
    for device, _vid, _serial_number in ports:  # last resort on Linux
        if device.startswith(("/dev/ttyACM", "/dev/ttyUSB")):
            return device
    return None


def _ports():
    _need_pyserial()
    return [(p.device, p.vid, p.serial_number) for p in list_ports.comports()]


def find_port(board: str | None = None) -> str | None:
    return pick_port(_ports(), load_boards(), board)


def serial_of(device: str) -> str | None:
    """USB serial number of a port (also works for /dev/serial/by-id/... links)."""
    real = os.path.realpath(device)
    for dev, _vid, serial_number in _ports():
        if os.path.realpath(dev) == real:
            return serial_number
    return None


def variant_of(device: str) -> str | None:
    """'R' / 'C' if this port's board has been registered, else None."""
    serial_number = serial_of(device)
    return load_boards().get(serial_number) if serial_number else None


class Link:
    """Serial connection that survives the USB re-enumeration an ESP32-S3 does on reset."""

    def __init__(self, port: str | None, baud: int, log_path: Path, board: str | None = None):
        self.port = port
        self.board = board
        self.baud = baud
        self.ser: serial.Serial | None = None
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log = log_path.open("a", encoding="utf-8", errors="replace")
        self.log.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")

    def open(self, wait_s: float) -> bool:
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            port = self.port or find_port(self.board)
            if port:
                try:
                    s = serial.Serial()
                    s.port = port
                    s.baudrate = self.baud
                    s.timeout = 0.1
                    s.dtr = False  # don't hold the chip in reset / bootloader
                    s.rts = False
                    s.open()
                    self.ser = s
                    return True
                except (serial.SerialException, OSError):
                    pass
            time.sleep(0.2)
        return False

    def close(self) -> None:
        if self.ser:
            try:
                self.ser.close()
            except Exception:
                pass
        self.ser = None

    def reset(self) -> None:
        """Hardware reset via RTS (same sequence esptool uses for USB-Serial-JTAG)."""
        assert self.ser
        try:
            self.ser.dtr = False
            self.ser.rts = True
            time.sleep(0.2)
            self.ser.rts = False
            time.sleep(0.2)
        except (serial.SerialException, OSError) as e:
            print(f"[esp_serial] reset via RTS not possible ({e}); continuing without reset",
                  file=sys.stderr)
            return
        self.close()  # the USB device drops and comes back

    def write_line(self, text: str) -> None:
        assert self.ser
        self.ser.write((text + "\n").encode())
        self.ser.flush()

    def lines(self, until: float):
        """Yield decoded lines until the monotonic deadline. Reconnects on USB drop."""
        buf = b""
        while time.monotonic() < until:
            if self.ser is None and not self.open(max(0.0, until - time.monotonic())):
                return
            try:
                chunk = self.ser.read(256)
            except (serial.SerialException, OSError):
                self.close()
                continue
            if not chunk:
                continue
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.decode("utf-8", errors="replace").rstrip("\r")
                self.log.write(line + "\n")
                self.log.flush()
                yield line


def _no_port_message(args) -> str:
    if args.port:
        return f"could not open serial port {args.port}"
    if args.board:
        return (f"no connected board is registered as {args.board} "
                f"(plug it in alone and run: esp_serial.py register {args.board})")
    return "no ESP32 serial port found"


def cmd_detect(args) -> int:
    port = args.port or find_port(args.board)
    if not port:
        print(_no_port_message(args), file=sys.stderr)
        return EXIT_PORT
    print(port)
    return EXIT_OK


def cmd_list(_args) -> int:
    _need_pyserial()
    boards = load_boards()
    for p in list_ports.comports():
        vid = f"{p.vid:04X}" if p.vid is not None else "----"
        pid = f"{p.pid:04X}" if p.pid is not None else "----"
        variant = boards.get(p.serial_number or "", "-")
        print(f"{p.device}\t{vid}:{pid}\tboard={variant}\tserial={p.serial_number or '-'}\t{p.description}")
    return EXIT_OK


def cmd_register(args) -> int:
    """Remember which physical board is the R and which is the C."""
    variant = args.variant.upper()
    if args.port:
        port = args.port
    else:
        candidates = [dev for dev, vid, _sn in _ports() if vid == ESPRESSIF_VID]
        if len(candidates) != 1:
            print(f"register: need exactly one board plugged in (found {len(candidates)}), "
                  "or name it with -p PORT", file=sys.stderr)
            return EXIT_PORT
        port = candidates[0]
    serial_number = serial_of(port)
    if not serial_number:
        print(f"register: {port} has no USB serial number, cannot tell boards apart", file=sys.stderr)
        return EXIT_PORT
    boards = load_boards()
    boards[serial_number] = variant
    path = boards_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# usb-serial-number variant   (written by esp_serial.py register)\n" +
                    "".join(f"{sn} {v}\n" for sn, v in sorted(boards.items())), encoding="utf-8")
    print(f"registered {port} (serial {serial_number}) as board {variant} in {path}")
    return EXIT_OK


def _connect(args) -> Link | None:
    _need_pyserial()
    link = Link(args.port, args.baud, Path(args.log), args.board)
    if not link.open(args.wait_port):
        print(_no_port_message(args), file=sys.stderr)
        return None
    return link


def cmd_monitor(args) -> int:
    link = _connect(args)
    if not link:
        return EXIT_PORT
    if args.reset:
        link.reset()
    expect = re.compile(args.expect) if args.expect else None
    fail = re.compile(args.fail) if args.fail else None
    deadline = time.monotonic() + args.seconds
    for line in link.lines(deadline):
        print(line, flush=True)
        if fail and fail.search(line):
            print(f"[esp_serial] FAIL pattern matched: {line}", file=sys.stderr)
            return EXIT_FAIL
        if expect and expect.search(line):
            return EXIT_OK
    if expect:
        print(f"[esp_serial] TIMEOUT: '{args.expect}' not seen in {args.seconds}s", file=sys.stderr)
        return EXIT_TIMEOUT
    return EXIT_OK


def _wait_alive(link: Link, timeout: float) -> bool:
    """Send `ping` every 0.5 s until PONG - handles a board that is still booting."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if link.ser is None and not link.open(deadline - time.monotonic()):
            return False
        try:
            link.write_line("ping")
        except (serial.SerialException, OSError):
            link.close()
            continue
        for line in link.lines(min(deadline, time.monotonic() + 0.5)):
            if line.strip() == "PONG":
                return True
    return False


def cmd_cmd(args) -> int:
    link = _connect(args)
    if not link:
        return EXIT_PORT
    if not _wait_alive(link, args.alive_timeout):
        print("[esp_serial] device did not answer ping", file=sys.stderr)
        return EXIT_TIMEOUT
    link.write_line(" ".join(args.command))
    until = re.compile(args.until) if args.until else None
    deadline = time.monotonic() + args.seconds
    for line in link.lines(deadline):
        print(line, flush=True)
        if is_crash(line):
            print(f"[esp_serial] CRASH signature: {line}", file=sys.stderr)
            return EXIT_FAIL
        if until and until.search(line):
            return EXIT_OK
    return EXIT_TIMEOUT if until else EXIT_OK


def cmd_selftest(args) -> int:
    link = _connect(args)
    if not link:
        return EXIT_PORT
    if not _wait_alive(link, args.alive_timeout):
        print("[esp_serial] device did not answer ping - is the firmware running?", file=sys.stderr)
        return EXIT_TIMEOUT
    # Tell the firmware which touch controller this board must have, so T-TOUCH
    # fails if a C board is mis-detected as R (or the other way round).
    variant = args.board or (variant_of(link.ser.port) if link.ser else None)
    expected = BOARD_TOUCH.get(variant or "")
    if expected:
        print(f"[esp_serial] board {variant}: expecting touch={expected}")
    else:
        print("[esp_serial] board not registered: T-TOUCH passes only on a positively detected "
              "GT911. Register it once: esp_serial.py register R   (or C)", file=sys.stderr)
    link.write_line(selftest_command(expected))
    seen: list[str] = []
    report = Path(args.report) if args.report else None
    deadline = time.monotonic() + args.seconds
    result = None
    for line in link.lines(deadline):
        print(line, flush=True)
        if is_crash(line):
            seen.append("SELFTEST:CRASH " + line)
            _write_report(report, seen, variant)
            print("[esp_serial] device crashed during selftest", file=sys.stderr)
            return EXIT_FAIL
        if line.startswith(("TEST:", "SELFTEST:")):
            seen.append(line)
        result = parse_selftest(seen)
        if result:
            break
    _write_report(report, seen, variant)
    if not result:
        print("[esp_serial] TIMEOUT waiting for SELFTEST:DONE", file=sys.stderr)
        return EXIT_TIMEOUT
    passed, failed, failures = result
    print(f"[esp_serial] target tests: {passed} passed, {failed} failed")
    for f in failures:
        print(f"  {f}")
    return EXIT_OK if failed == 0 else EXIT_FAIL


def selftest_command(expected_touch: str | None) -> str:
    return f"selftest touch={expected_touch}" if expected_touch else "selftest"


def board_report_path(path: Path, variant: str) -> Path:
    """build/target-test.log -> build/target-test.R.log"""
    return path.with_name(f"{path.stem}.{variant}{path.suffix}")


def _write_report(path: Path | None, lines: list[str], variant: str | None = None) -> None:
    """Keep the last selftest result for tools/trace.py (overwritten each run).

    A registered board also gets its own copy (target-test.R.log / .C.log), so a
    requirement can demand a pass on each board: `T-TOUCH@R, T-TOUCH@C` in the FSD.
    """
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(ln + "\n" for ln in lines)
    path.write_text(text, encoding="utf-8")
    if variant:
        board_report_path(path, variant).write_text(text, encoding="utf-8")


def _read_info(args) -> dict[str, str] | None:
    """Open the port, ask for `info`, close again. None if the board did not answer."""
    link = _connect(args)
    if not link:
        return None
    try:
        if not _wait_alive(link, args.alive_timeout):
            return None
        link.write_line("info")
        for line in link.lines(time.monotonic() + 3):
            if line.startswith("INFO "):
                return parse_kv(line)
        return None
    finally:
        link.close()


def cmd_buildid(args) -> int:
    """Print the source fingerprint the running firmware was built from."""
    info = _read_info(args)
    if not info or "build" not in info:
        return EXIT_TIMEOUT
    print(info["build"])
    return EXIT_OK


def cmd_opencheck(args) -> int:
    """Does opening (or closing) the serial port reset the board?

    On the ESP32-S3's built-in USB the DTR/RTS lines double as reset signals, and
    Linux toggles them when a port is opened. Every tool call opens the port, so
    if that resets the chip, state such as a Wi-Fi connection is lost between two
    bench-test commands. We open the port twice and compare the uptime.
    """
    first = _read_info(args)
    time.sleep(args.gap)
    second = _read_info(args)
    try:
        up1, up2 = int(first["uptime_ms"]), int(second["uptime_ms"])  # type: ignore[index]
    except (TypeError, KeyError, ValueError):
        print("[esp_serial] opencheck: the board did not answer `info` twice", file=sys.stderr)
        return EXIT_TIMEOUT
    if up2 > up1:
        print(f"OPENCHECK:OK uptime {up1} -> {up2} ms: opening the port does not reset the board")
        return EXIT_OK
    print(f"OPENCHECK:RESETS uptime {up1} -> {up2} ms: the board restarts when the port is opened. "
          "Multi-step bench tests will lose device state between commands; see docs/troubleshooting.md")
    return EXIT_FAIL


def cmd_bootcheck(args) -> int:
    """Reset, then prove the firmware booted cleanly.

    The ESP32-S3 USB port disappears during reset, so the BOOT:OK banner can be
    printed before we reconnect. If we miss it, fall back to `info` and check the
    reset reason and uptime instead.
    """
    link = _connect(args)
    if not link:
        return EXIT_PORT
    link.reset()
    deadline = time.monotonic() + args.seconds
    for line in link.lines(deadline):
        print(line, flush=True)
        if is_crash(line):
            print("[esp_serial] BOOT FAILED: crash signature seen", file=sys.stderr)
            return EXIT_FAIL
        if "BOOT:OK" in line:
            return _settle(link, args.settle)
    # Banner missed - ask the device directly.
    if not _wait_alive(link, args.alive_timeout):
        print("[esp_serial] BOOT FAILED: no BOOT:OK and no answer to ping", file=sys.stderr)
        return EXIT_TIMEOUT
    link.write_line("info")
    for line in link.lines(time.monotonic() + 3):
        print(line, flush=True)
        if line.startswith("INFO "):
            fields = parse_kv(line)
            reason = fields.get("reset", "?")
            if reason in BAD_RESET_REASONS:
                print(f"[esp_serial] BOOT FAILED: last reset reason = {reason}", file=sys.stderr)
                return EXIT_FAIL
            print(f"[esp_serial] booted (alive, reset={reason}, uptime_ms={fields.get('uptime_ms')})")
            return _settle(link, args.settle)
    return EXIT_TIMEOUT


def _settle(link: Link, seconds: float) -> int:
    """After a good boot, keep listening a little: a firmware that crashes 2 s after
    BOOT:OK (Wi-Fi start, first sensor read, ...) must not count as a clean boot."""
    deadline = time.monotonic() + seconds
    for line in link.lines(deadline):
        print(line, flush=True)
        if is_crash(line):
            print(f"[esp_serial] BOOT FAILED: crashed within {seconds:.0f}s of boot", file=sys.stderr)
            return EXIT_FAIL
        if "BOOT:OK" in line or line.startswith("[boot]"):
            print("[esp_serial] BOOT FAILED: the board rebooted by itself (boot loop?)", file=sys.stderr)
            return EXIT_FAIL
    print(f"[esp_serial] boot ok (stable for {seconds:.0f}s)")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-p", "--port", default=os.environ.get("ESP_PORT") or None,
                    help="serial port (default: $ESP_PORT, else auto-detect)")
    ap.add_argument("--board", default=os.environ.get("ESP_BOARD") or None,
                    help="use the board registered as this variant, e.g. R or C (default: $ESP_BOARD)")
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("--log", default="build/serial.log", help="append everything received here")
    ap.add_argument("--wait-port", type=float, default=10.0, help="seconds to wait for the port to appear")
    sub = ap.add_subparsers(dest="sub", required=True)

    sub.add_parser("detect").set_defaults(fn=cmd_detect)
    sub.add_parser("list", help="ports with their USB serial number and registered variant"
                   ).set_defaults(fn=cmd_list)

    r = sub.add_parser("register", help="remember the connected board as variant R or C")
    r.add_argument("variant", choices=sorted(BOARD_TOUCH) + [v.lower() for v in sorted(BOARD_TOUCH)])
    r.set_defaults(fn=cmd_register)

    i = sub.add_parser("buildid", help="print the source fingerprint of the running firmware")
    i.add_argument("--alive-timeout", type=float, default=10.0)
    i.set_defaults(fn=cmd_buildid)

    o = sub.add_parser("opencheck", help="check that opening the port does not reset the board")
    o.add_argument("--alive-timeout", type=float, default=15.0)
    o.add_argument("--gap", type=float, default=1.0, help="seconds between the two opens")
    o.set_defaults(fn=cmd_opencheck)

    m = sub.add_parser("monitor", help="print serial output with a timeout")
    m.add_argument("-s", "--seconds", type=float, default=10.0)
    m.add_argument("--reset", action="store_true", help="hardware-reset the board first")
    m.add_argument("--expect", help="regex: exit 0 as soon as it appears")
    m.add_argument("--fail", default=DEFAULT_FAIL, help="regex: exit 1 if it appears (default: crash signatures)")
    m.set_defaults(fn=cmd_monitor)

    c = sub.add_parser("cmd", help="send one console command and print the reply")
    c.add_argument("command", nargs="+")
    c.add_argument("-s", "--seconds", type=float, default=3.0)
    c.add_argument("--until", help="regex: stop reading when it appears")
    c.add_argument("--alive-timeout", type=float, default=15.0)
    c.set_defaults(fn=cmd_cmd)

    b = sub.add_parser("bootcheck", help="reset board and verify a clean boot")
    b.add_argument("-s", "--seconds", type=float, default=8.0, help="how long to wait for BOOT:OK")
    b.add_argument("--alive-timeout", type=float, default=10.0)
    b.add_argument("--settle", type=float, default=4.0,
                   help="seconds to keep watching for a crash/reboot after a good boot")
    b.set_defaults(fn=cmd_bootcheck)

    t = sub.add_parser("selftest", help="run on-target tests")
    t.add_argument("-s", "--seconds", type=float, default=30.0)
    t.add_argument("--alive-timeout", type=float, default=15.0)
    t.add_argument("--report", default="build/target-test.log",
                   help="write this run's TEST:/SELFTEST: lines here (read by tools/trace.py)")
    t.set_defaults(fn=cmd_selftest)

    args = ap.parse_args(argv)
    if args.board:
        args.board = args.board.upper()
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
