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

Exit codes: 0 ok | 1 test/fail-pattern hit | 2 timeout | 3 port problem | 4 usage
Everything received is also appended to build/serial.log (override with --log).

Needs pyserial (`pip install pyserial`, already done by devbox/setup.sh).
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

try:
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    print("pyserial missing: pip install pyserial", file=sys.stderr)
    sys.exit(3)

ESPRESSIF_VID = 0x303A  # native USB (ESP32-S3/C3 USB-Serial-JTAG)
USB_UART_VIDS = {0x10C4, 0x1A86, 0x0403}  # CP210x, CH340, FTDI on other dev boards
DEFAULT_FAIL = r"Guru Meditation|abort\(\) was called|Backtrace:|Brownout detector|rst:0x[0-9a-f]+ \((?:TG|RTC)WDT"

EXIT_OK, EXIT_FAIL, EXIT_TIMEOUT, EXIT_PORT, EXIT_USAGE = 0, 1, 2, 3, 4


def find_port() -> str | None:
    ports = list(list_ports.comports())
    for vids in ({ESPRESSIF_VID}, USB_UART_VIDS):
        for p in ports:
            if p.vid in vids:
                return p.device
    for p in ports:  # last resort on Linux
        if p.device.startswith(("/dev/ttyACM", "/dev/ttyUSB")):
            return p.device
    return None


class Link:
    """Serial connection that survives the USB re-enumeration an ESP32-S3 does on reset."""

    def __init__(self, port: str | None, baud: int, log_path: Path):
        self.port = port
        self.baud = baud
        self.ser: serial.Serial | None = None
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log = log_path.open("a", encoding="utf-8", errors="replace")
        self.log.write(f"\n===== {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")

    def open(self, wait_s: float) -> bool:
        deadline = time.monotonic() + wait_s
        while time.monotonic() < deadline:
            port = self.port or find_port()
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


def cmd_detect(_args) -> int:
    port = find_port()
    if not port:
        print("no ESP32 serial port found", file=sys.stderr)
        return EXIT_PORT
    print(port)
    return EXIT_OK


def cmd_list(_args) -> int:
    for p in list_ports.comports():
        vid = f"{p.vid:04X}" if p.vid is not None else "----"
        pid = f"{p.pid:04X}" if p.pid is not None else "----"
        print(f"{p.device}\t{vid}:{pid}\t{p.description}")
    return EXIT_OK


def _connect(args) -> Link | None:
    link = Link(args.port, args.baud, Path(args.log))
    if not link.open(args.wait_port):
        print(f"could not open serial port ({args.port or 'auto-detect'})", file=sys.stderr)
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
    fail = re.compile(DEFAULT_FAIL)
    deadline = time.monotonic() + args.seconds
    for line in link.lines(deadline):
        print(line, flush=True)
        if fail.search(line):
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
    link.write_line("selftest")
    crash = re.compile(DEFAULT_FAIL)
    done = re.compile(r"SELFTEST:DONE pass=(\d+) fail=(\d+)")
    failures: list[str] = []
    deadline = time.monotonic() + args.seconds
    for line in link.lines(deadline):
        print(line, flush=True)
        if crash.search(line):
            print("[esp_serial] device crashed during selftest", file=sys.stderr)
            return EXIT_FAIL
        if line.startswith("TEST:") and ":FAIL:" in line:
            failures.append(line)
        m = done.search(line)
        if m:
            passed, failed = int(m.group(1)), int(m.group(2))
            print(f"[esp_serial] target tests: {passed} passed, {failed} failed")
            for f in failures:
                print(f"  {f}")
            return EXIT_OK if failed == 0 else EXIT_FAIL
    print("[esp_serial] TIMEOUT waiting for SELFTEST:DONE", file=sys.stderr)
    return EXIT_TIMEOUT


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
    crash = re.compile(DEFAULT_FAIL)
    deadline = time.monotonic() + args.seconds
    for line in link.lines(deadline):
        print(line, flush=True)
        if crash.search(line):
            print("[esp_serial] BOOT FAILED: crash signature seen", file=sys.stderr)
            return EXIT_FAIL
        if "BOOT:OK" in line:
            print("[esp_serial] boot ok (banner seen)")
            return EXIT_OK
    # Banner missed - ask the device directly.
    if not _wait_alive(link, args.alive_timeout):
        print("[esp_serial] BOOT FAILED: no BOOT:OK and no answer to ping", file=sys.stderr)
        return EXIT_TIMEOUT
    link.write_line("info")
    for line in link.lines(time.monotonic() + 3):
        print(line, flush=True)
        if line.startswith("INFO "):
            fields = dict(kv.split("=", 1) for kv in line.split()[1:] if "=" in kv)
            reason = fields.get("reset", "?")
            if reason in ("panic", "int_wdt", "task_wdt", "wdt", "brownout"):
                print(f"[esp_serial] BOOT FAILED: last reset reason = {reason}", file=sys.stderr)
                return EXIT_FAIL
            print(f"[esp_serial] boot ok (alive, reset={reason}, uptime_ms={fields.get('uptime_ms')})")
            return EXIT_OK
    return EXIT_TIMEOUT


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-p", "--port", help="serial port (default: auto-detect ESP32)")
    ap.add_argument("-b", "--baud", type=int, default=115200)
    ap.add_argument("--log", default="build/serial.log", help="append everything received here")
    ap.add_argument("--wait-port", type=float, default=10.0, help="seconds to wait for the port to appear")
    sub = ap.add_subparsers(dest="sub", required=True)

    sub.add_parser("detect").set_defaults(fn=cmd_detect)
    sub.add_parser("list").set_defaults(fn=cmd_list)

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
    b.set_defaults(fn=cmd_bootcheck)

    t = sub.add_parser("selftest", help="run on-target tests")
    t.add_argument("-s", "--seconds", type=float, default=30.0)
    t.add_argument("--alive-timeout", type=float, default=15.0)
    t.set_defaults(fn=cmd_selftest)

    args = ap.parse_args(argv)
    try:
        return args.fn(args)
    except KeyboardInterrupt:
        return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
