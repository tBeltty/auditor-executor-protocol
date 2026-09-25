"""Tally the compliance log and print what is still open.

Two sources are combined per task/gate ID:

- the Auditor's verdict: the "Verdict" column of the status board table, or a report
  header whose status is a verdict (APPROVED, CONDITIONAL, REJECTED);
- the Executor's latest report header (DONE, BLOCKED, FAILED, PENDING).

Only APPROVED closes an item. A DONE report without a verdict is self-reported, not
audited, so it is listed as awaiting audit.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

LOG_HEADER_RE = re.compile(
    r"^###\s+([A-Za-z0-9_.\-]+)\s+[\u2014\u2013\-]\s+([A-Za-z_]+)\s*$", re.MULTILINE
)

VERDICTS = {"APPROVED", "CONDITIONAL", "REJECTED"}
CLOSED = "APPROVED"
AWAITING_AUDIT = "AWAITING AUDIT"


def _cells(line: str) -> list[str]:
    return [c.strip().strip("`*").strip() for c in line.strip().strip("|").split("|")]


def _board_verdicts(text: str) -> dict[str, str]:
    """ID -> verdict from the first table whose header has "ID" and "Verdict" columns."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        header = [c.lower() for c in _cells(line)]
        if "id" not in header or "verdict" not in header:
            continue
        id_col, verdict_col = header.index("id"), header.index("verdict")
        verdicts: dict[str, str] = {}
        for row in lines[i + 1 :]:
            if not row.lstrip().startswith("|"):
                break
            cells = _cells(row)
            if len(cells) <= max(id_col, verdict_col) or set(cells[id_col]) <= set("-: "):
                continue
            verdicts[cells[id_col]] = cells[verdict_col].upper()
        return verdicts
    return {}


def run(target_dir: str) -> int:
    target = Path(target_dir)
    log_path = target / "compliance-log.md"
    if not log_path.exists():
        print(f"error: {log_path} not found.")
        return 2

    text = log_path.read_text(encoding="utf-8")

    # IDs in first-seen order; for headers, the last occurrence wins (resubmissions).
    order: dict[str, None] = {}
    reports: dict[str, str] = {}
    header_verdicts: dict[str, str] = {}
    last_header_id = ""
    board = _board_verdicts(text)
    for task_id in board:
        order.setdefault(task_id, None)
    for m in LOG_HEADER_RE.finditer(text):
        task_id, value = m.group(1), m.group(2).upper()
        order.setdefault(task_id, None)
        last_header_id = task_id
        if value in VERDICTS:
            header_verdicts[task_id] = value
        else:
            reports[task_id] = value

    if not order:
        print("no task entries found in compliance-log.md.")
        return 0

    states: dict[str, str] = {}
    for task_id in order:
        verdict = board.get(task_id, "")
        if verdict not in VERDICTS:
            verdict = header_verdicts.get(task_id, "")
        report = reports.get(task_id, "PENDING")
        if verdict:
            states[task_id] = verdict
        elif report == "DONE":
            states[task_id] = AWAITING_AUDIT
        else:
            states[task_id] = report

    counts = Counter(states.values())
    print("Status board:")
    for state, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {state:<15} {n}")

    open_items = [(tid, st) for tid, st in states.items() if st != CLOSED]
    print(f"\n{len(open_items)} open (not APPROVED):")
    for tid, st in open_items:
        report_of_item = reports.get(tid)
        detail = f" (report: {report_of_item})" if report_of_item and st in VERDICTS else ""
        print(f"  - {tid}: {st}{detail}")

    last_id = last_header_id or next(reversed(order))
    print(f"\nMost recent entry: {last_id} ({states[last_id]})")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit status")
    parser.add_argument("target_dir")
    args = parser.parse_args(argv)
    return run(args.target_dir)


if __name__ == "__main__":
    sys.exit(main())
