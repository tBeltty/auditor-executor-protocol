"""Tally verdicts in the compliance log and print what's still open."""
from __future__ import annotations

import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

LOG_HEADER_RE = re.compile(r"^###\s+([A-Za-z0-9_.\-]+)\s+—\s+([A-Za-z]+)\s*$", re.MULTILINE)

OPEN_STATUSES = {"PENDING", "BLOCKED", "FAILED", "CONDITIONAL"}


def run(target_dir: str) -> int:
    target = Path(target_dir)
    log_path = target / "compliance-log.md"
    if not log_path.exists():
        print(f"error: {log_path} not found.")
        return 2

    text = log_path.read_text(encoding="utf-8")

    # Last occurrence of each ID wins — a task can be reported more than once.
    latest: "OrderedDict[str, str]" = OrderedDict()
    for m in LOG_HEADER_RE.finditer(text):
        latest[m.group(1)] = m.group(2).upper()

    if not latest:
        print("no task entries found in compliance-log.md.")
        return 0

    counts = Counter(latest.values())
    print("Status board:")
    for status, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {status:<12} {n}")

    open_items = [(tid, st) for tid, st in latest.items() if st in OPEN_STATUSES]
    print(f"\n{len(open_items)} open (not APPROVED/DONE):")
    for tid, st in open_items:
        print(f"  - {tid}: {st}")

    if latest:
        last_id = next(reversed(latest))
        print(f"\nMost recent entry: {last_id} ({latest[last_id]})")

    return 0


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit status")
    parser.add_argument("target_dir")
    args = parser.parse_args(argv)
    return run(args.target_dir)


if __name__ == "__main__":
    sys.exit(main())
