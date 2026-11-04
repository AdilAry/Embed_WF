#!/usr/bin/env python3
"""Requirement traceability: does every FSD requirement have a test, and did it pass?

Reads the requirements table in docs/FSD.md:

    | ID | Requirement | Tier | Test |
    | REQ-010 | Text wraps at word boundaries. | host | wrap_* |

finds each named test in the code for its tier, and looks up the result of the
last run of that tier:

    tier     test is found in                       last result read from
    host     TEST(name) in test/host/*.cpp          build/host-test.log   (make host-test)
    target   report("T-XXX", ...) in firmware/      build/target-test.log (make target-test)
    bench    def test_xxx in test/bench/test_*.py   build/bench-test.xml  (make bench-test)
    field / manual   nothing to find: a human checks it (FSD section 8)

The Test column may hold several names separated by commas, and shell-style
wildcards (wrap_*). Usage:

    trace.py                       print the matrix (always exits 0)
    trace.py --strict              exit 1 if a requirement has no test or a test FAILED
    trace.py --require-run         like --strict, and NOT RUN / SKIPPED also fail
    trace.py REQ-010 REQ-020 ...   only these requirements (e.g. the current phase)
    trace.py --out docs/STATUS.md  also write the matrix as a Markdown file

This is the "did we build what we specified?" check. A green matrix is evidence
that the firmware does what the FSD says, as far as the tests go.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

AUTO_TIERS = ("host", "target", "bench")
HUMAN_TIERS = ("field", "manual")

PASS, FAIL, SKIP, NOT_RUN, NO_TEST, HUMAN, BAD_TIER = (
    "PASS", "FAIL", "SKIPPED", "NOT RUN", "NO TEST", "MANUAL", "BAD TIER")
BLOCKING_STRICT = {FAIL, NO_TEST, BAD_TIER}
BLOCKING_RUN = BLOCKING_STRICT | {NOT_RUN, SKIP}


@dataclass
class Requirement:
    rid: str
    text: str
    tier: str
    tests: list[str]
    matched: list[str] = field(default_factory=list)
    status: str = NOT_RUN
    detail: str = ""


# ---------------------------------------------------------------- FSD parsing
_REQ_ROW = re.compile(r"^\s*\|\s*(REQ-[0-9A-Za-z_.-]+)\s*\|(.*)\|\s*$")


def parse_fsd(text: str) -> list[Requirement]:
    """Requirement rows from the FSD's Markdown table(s). Placeholder rows such as
    '| REQ-… | | | |' (no requirement text) are ignored."""
    reqs = []
    for line in text.splitlines():
        m = _REQ_ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(2).split("|")]
        if len(cells) < 3 or not cells[0]:
            continue
        req_text, tier, test = cells[0], cells[1].lower(), cells[2]
        tests = [t.strip().strip("`") for t in re.split(r"[,;]|\s+", test) if t.strip().strip("`")]
        reqs.append(Requirement(m.group(1), req_text, tier, tests))
    return reqs


# ------------------------------------------------------------ test discovery
def _read_all(paths) -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in paths if p.is_file())


def discover(root: Path) -> dict[str, set[str]]:
    host_src = _read_all(sorted((root / "test" / "host").glob("*.cpp")))
    fw = root / "firmware"
    target_src = _read_all(sorted(list(fw.rglob("*.cpp")) + list(fw.rglob("*.ino")))) if fw.is_dir() else ""
    bench_src = _read_all(sorted((root / "test" / "bench").glob("test_*.py")))
    return {
        "host": set(re.findall(r"\bTEST\(\s*(\w+)\s*\)", host_src)),
        "target": set(re.findall(r"\breport\(\s*\"(T-[\w-]+)\"", target_src)),
        "bench": set(re.findall(r"^\s*(?:async\s+)?def\s+(test_\w+)\s*\(", bench_src, re.M)),
    }


# --------------------------------------------------------------- last results
def load_results(root: Path) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    """{tier: {test: PASS|FAIL|SKIPPED}}, {tier: 'file, time' of the evidence}."""
    build = root / "build"
    results: dict[str, dict[str, str]] = {t: {} for t in AUTO_TIERS}
    when: dict[str, str] = {}

    def stamp(p: Path) -> str:
        return f"{p.relative_to(root)} @ {time.strftime('%Y-%m-%d %H:%M', time.localtime(p.stat().st_mtime))}"

    host = build / "host-test.log"
    if host.is_file():
        for m in re.finditer(r"^HOSTTEST:(\w+):(PASS|FAIL)$", host.read_text(errors="replace"), re.M):
            results["host"][m.group(1)] = m.group(2)
        when["host"] = stamp(host)

    target = build / "target-test.log"
    if target.is_file():
        txt = target.read_text(errors="replace")
        for m in re.finditer(r"^TEST:([\w-]+):(PASS|FAIL):", txt, re.M):
            results["target"][m.group(1)] = m.group(2)
        when["target"] = stamp(target) + (" (CRASHED)" if "SELFTEST:CRASH" in txt else "")

    bench = build / "bench-test.xml"
    if bench.is_file():
        try:
            for case in ET.parse(bench).getroot().iter("testcase"):
                name = case.get("name", "").split("[", 1)[0]  # drop pytest parameter ids
                tags = {child.tag for child in case}
                status = FAIL if tags & {"failure", "error"} else SKIP if "skipped" in tags else PASS
                if results["bench"].get(name) != FAIL:  # a failing parameter wins
                    results["bench"][name] = status
            when["bench"] = stamp(bench)
        except ET.ParseError:
            when["bench"] = f"{bench.relative_to(root)} (unreadable)"
    return results, when


# ---------------------------------------------------------------- evaluation
def evaluate(reqs: list[Requirement], found: dict[str, set[str]],
             results: dict[str, dict[str, str]]) -> None:
    for r in reqs:
        if r.tier in HUMAN_TIERS:
            r.status, r.detail = HUMAN, "checked by a person (FSD section 8)"
            continue
        if r.tier not in AUTO_TIERS:
            r.status, r.detail = BAD_TIER, f"tier '{r.tier}' is not host/target/bench/field/manual"
            continue
        names = found[r.tier]
        missing = []
        for pattern in r.tests:
            hits = sorted(fnmatch.filter(names, pattern))
            if hits:
                r.matched.extend(h for h in hits if h not in r.matched)
            else:
                missing.append(pattern)
        if not r.tests or missing:
            elsewhere = [t for t in missing for tier, n in found.items()
                         if tier != r.tier and fnmatch.filter(n, t)]
            hint = f" (exists in another tier: {', '.join(elsewhere)})" if elsewhere else ""
            r.status = NO_TEST
            r.detail = (f"no {r.tier} test named {', '.join(missing)}{hint}" if missing
                        else "Test column is empty")
            continue
        got = [results[r.tier].get(t, NOT_RUN) for t in r.matched]
        failed = [t for t, s in zip(r.matched, got) if s == FAIL]
        if failed:
            r.status, r.detail = FAIL, "failed: " + ", ".join(failed)
        elif NOT_RUN in got:
            r.status = NOT_RUN
            r.detail = "no result yet: " + ", ".join(t for t, s in zip(r.matched, got) if s == NOT_RUN)
        elif SKIP in got:
            r.status, r.detail = SKIP, "skipped: " + ", ".join(t for t, s in zip(r.matched, got) if s == SKIP)
        else:
            r.status, r.detail = PASS, ", ".join(r.matched)


def orphans(reqs: list[Requirement], found: dict[str, set[str]]) -> dict[str, list[str]]:
    """Tests that no requirement points at. Not an error, but worth a look: either
    the FSD is missing a requirement, or the test is noise."""
    used = {t for r in reqs for t in r.matched}
    return {tier: sorted(n - used) for tier, n in found.items() if n - used}


# ------------------------------------------------------------------- output
def render(reqs: list[Requirement], when: dict[str, str], orphan: dict[str, list[str]]) -> str:
    counts: dict[str, int] = {}
    for r in reqs:
        counts[r.status] = counts.get(r.status, 0) + 1
    out = ["# Requirement status", "",
           f"Generated by `tools/trace.py` on {time.strftime('%Y-%m-%d %H:%M')}. "
           "Results are from the last run of each tier:", ""]
    for tier in AUTO_TIERS:
        out.append(f"- {tier}: {when.get(tier, 'never run on this machine')}")
    out += ["", "| ID | Tier | Status | Detail | Requirement |", "|---|---|---|---|---|"]
    for r in reqs:
        text = r.text if len(r.text) <= 70 else r.text[:67] + "..."
        out.append(f"| {r.rid} | {r.tier} | {r.status} | {r.detail} | {text} |")
    out += ["", "**Summary:** " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) if counts
            else "**Summary:** no requirements found in docs/FSD.md"]
    if orphan:
        out += ["", "Tests not referenced by any requirement: " +
                "; ".join(f"{tier}: {', '.join(n)}" for tier, n in orphan.items())]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("only", nargs="*", metavar="REQ-ID", help="limit to these requirement IDs")
    ap.add_argument("--root", default=".", help="project folder (default: current)")
    ap.add_argument("--fsd", default="docs/FSD.md")
    ap.add_argument("--strict", action="store_true", help="fail on NO TEST / FAIL / BAD TIER")
    ap.add_argument("--require-run", action="store_true", help="--strict, and NOT RUN / SKIPPED fail too")
    ap.add_argument("--out", help="also write the matrix to this Markdown file")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    fsd = root / args.fsd
    if not fsd.is_file():
        print(f"trace: {fsd} not found", file=sys.stderr)
        return 4
    reqs = parse_fsd(fsd.read_text(encoding="utf-8"))
    dupes = sorted({r.rid for r in reqs if sum(x.rid == r.rid for x in reqs) > 1})
    found = discover(root)
    results, when = load_results(root)
    evaluate(reqs, found, results)
    orphan = orphans(reqs, found)

    if args.only:
        unknown = [i for i in args.only if i not in {r.rid for r in reqs}]
        if unknown:
            print(f"trace: not in the FSD: {', '.join(unknown)}", file=sys.stderr)
            return 4
        reqs = [r for r in reqs if r.rid in args.only]
        orphan = {}

    text = render(reqs, when, orphan)
    if dupes:
        text += f"\nWARNING: duplicate requirement IDs: {', '.join(dupes)}\n"
    print(text, end="")
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")

    blocking = BLOCKING_RUN if args.require_run else BLOCKING_STRICT if args.strict else set()
    bad = [r for r in reqs if r.status in blocking]
    if dupes and blocking:
        return 1
    if bad:
        print(f"TRACE:FAIL {len(bad)} requirement(s) not proven: {', '.join(r.rid for r in bad)}")
        return 1
    if blocking:
        print("TRACE:OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
