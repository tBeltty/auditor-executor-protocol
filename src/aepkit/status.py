"""Tally the compliance log and print what is still open.

Two sources are combined per task/gate ID:

- the Auditor's verdict: the "Verdict" column of the status board table, or a report
  header whose status is a verdict (APPROVED, CONDITIONAL, REJECTED);
- the Executor's latest report header (DONE, BLOCKED, FAILED, PENDING).

Only APPROVED closes an item. A DONE report without a verdict is self-reported, not
audited, so it is listed as awaiting audit. When the board and a report header carry
different verdicts, the item is listed as a conflict and stays open.

With --json the same reading is printed as one JSON object, together with the phases
and their titles from execution-guide.md and the phase table of plan-of-record.md, so
tools (the optional progress pane, CI scripts) use this reading instead of their own.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LOG_HEADER_RE = re.compile(
    r"^###\s+([A-Za-z0-9_.\-]+)\s+[\u2014\u2013\-]\s+([A-Za-z_]+)\s*$", re.MULTILINE
)
GUIDE_ITEM_RE = re.compile(r"^###\s+([A-Za-z0-9_.\-]+)\s+[\u2014\u2013\-]", re.MULTILINE)
GUIDE_PHASE_RE = re.compile(r"^#\s+Phase\s+(\d+)\b[ \t]*(?:[\u2014\u2013\-:][ \t]*(.*))?$", re.M)
ITEM_PHASE_RE = re.compile(r"^P(\d+)-([A-Za-z]*)\d", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"^<[^>]*>$")
PLAN_PHASE_CELL_RE = re.compile(r"^(?:P|Phase\s*)?(\d+)\b\s*[\u2014\u2013\-:.]?\s*(.*)$", re.I)

VERDICTS = {"APPROVED", "CONDITIONAL", "REJECTED"}
CLOSED = "APPROVED"
AWAITING_AUDIT = "AWAITING AUDIT"
CONFLICT = "CONFLICT"
JSON_SCHEMA = 1
# Status board columns read as "who is executing this ID", first match wins.
EXECUTOR_COLUMNS = ("executor", "worker", "agent", "owner", "assignee")


def _cells(line: str) -> list[str]:
    return [c.strip().strip("`*").strip() for c in line.strip().strip("|").split("|")]


def _board_table(text: str) -> list[dict[str, str]]:
    """Rows (header -> cell, headers lower-cased) of the first table with ID and Verdict."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        header = [c.lower() for c in _cells(line)]
        if "id" not in header or "verdict" not in header:
            continue
        rows: list[dict[str, str]] = []
        for row in lines[i + 1 :]:
            if not row.lstrip().startswith("|"):
                break
            cells = _cells(row)
            if len(cells) <= max(header.index("id"), header.index("verdict")):
                continue
            if set(cells[header.index("id")]) <= set("-: "):
                continue
            rows.append({h: (cells[n] if n < len(cells) else "") for n, h in enumerate(header)})
        return rows
    return []


def board_verdicts(text: str) -> dict[str, str]:
    """ID -> verdict from the first table whose header has "ID" and "Verdict" columns."""
    return {row["id"]: row["verdict"].upper() for row in _board_table(text)}


def _board_executors(text: str) -> dict[str, str]:
    executors: dict[str, str] = {}
    for row in _board_table(text):
        name = next((row[c] for c in EXECUTOR_COLUMNS if row.get(c)), "")
        if name:
            executors[row["id"]] = name
    return executors


@dataclass
class Reading:
    """One reading of compliance-log.md: every ID it names and its effective state."""

    order: list[str] = field(default_factory=list)
    states: dict[str, str] = field(default_factory=dict)
    reports: dict[str, str] = field(default_factory=dict)
    verdicts: dict[str, str] = field(default_factory=dict)
    conflicts: dict[str, tuple[str, str]] = field(default_factory=dict)
    executors: dict[str, str] = field(default_factory=dict)
    last_header_id: str = ""


def read_log(text: str) -> Reading:
    """Combine the status board with the report headers, by the rules in the module doc."""
    reading = Reading()
    # IDs in first-seen order; for headers, the last occurrence wins (resubmissions).
    order: dict[str, None] = {}
    header_verdicts: dict[str, str] = {}
    board = board_verdicts(text)
    for task_id in board:
        order.setdefault(task_id, None)
    for m in LOG_HEADER_RE.finditer(text):
        task_id, value = m.group(1), m.group(2).upper()
        order.setdefault(task_id, None)
        reading.last_header_id = task_id
        if value in VERDICTS:
            header_verdicts[task_id] = value
        else:
            reading.reports[task_id] = value

    reading.order = list(order)
    reading.executors = _board_executors(text)
    for task_id in reading.order:
        board_verdict = board.get(task_id, "")
        board_verdict = board_verdict if board_verdict in VERDICTS else ""
        header_verdict = header_verdicts.get(task_id, "")
        verdict = board_verdict or header_verdict
        if verdict:
            reading.verdicts[task_id] = verdict
        report = reading.reports.get(task_id, "PENDING")
        if board_verdict and header_verdict and board_verdict != header_verdict:
            reading.states[task_id] = CONFLICT
            reading.conflicts[task_id] = (board_verdict, header_verdict)
        elif verdict:
            reading.states[task_id] = verdict
        elif report == "DONE":
            reading.states[task_id] = AWAITING_AUDIT
        else:
            reading.states[task_id] = report
    return reading


def _phase_of(task_id: str) -> int | None:
    m = ITEM_PHASE_RE.match(task_id)
    return int(m.group(1)) if m else None


def _kind_of(task_id: str) -> str:
    m = ITEM_PHASE_RE.match(task_id)
    letter = m.group(2).upper() if m else ""
    return {"T": "task", "G": "gate"}.get(letter, "other")


def _plan_phases(plan_text: str) -> dict[int, tuple[str, float]]:
    """Phase number -> (title, weight) from the plan's table with a "Phase" column.

    The weight comes from an optional "Weight" column (a positive number); every
    other phase weighs 1.
    """
    lines = plan_text.splitlines()
    for i, line in enumerate(lines):
        if not line.lstrip().startswith("|"):
            continue
        header = [c.lower() for c in _cells(line)]
        if "phase" not in header:
            continue
        phase_col = header.index("phase")
        weight_col = header.index("weight") if "weight" in header else None
        title_col = header.index("delivers") if "delivers" in header else None
        phases: dict[int, tuple[str, float]] = {}
        for row in lines[i + 1 :]:
            if not row.lstrip().startswith("|"):
                break
            cells = _cells(row)
            m = PLAN_PHASE_CELL_RE.match(cells[phase_col]) if phase_col < len(cells) else None
            if not m:
                continue
            title = m.group(2).strip()
            if not title and title_col is not None and title_col < len(cells):
                title = cells[title_col]
            weight = 1.0
            if weight_col is not None and weight_col < len(cells):
                try:
                    weight = float(cells[weight_col])
                except ValueError:
                    weight = 1.0
                weight = weight if weight > 0 else 1.0
            phases[int(m.group(1))] = (title, weight)
        return phases
    return {}


def collect(target_dir: str) -> dict[str, Any]:
    """The reading as a JSON-ready dict. Raises FileNotFoundError without a log."""
    target = Path(target_dir)
    log_path = target / "compliance-log.md"
    text = log_path.read_text(encoding="utf-8")
    reading = read_log(text)

    guide_path = target / "execution-guide.md"
    guide_text = guide_path.read_text(encoding="utf-8") if guide_path.exists() else ""
    plan_path = target / "plan-of-record.md"
    plan_text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""

    guide_titles = {
        int(m.group(1)): (m.group(2) or "").strip() for m in GUIDE_PHASE_RE.finditer(guide_text)
    }
    guide_ids = [m.group(1) for m in GUIDE_ITEM_RE.finditer(guide_text)]
    plan = _plan_phases(plan_text)

    items: list[dict[str, Any]] = []
    for task_id in reading.order:
        board_header = reading.conflicts.get(task_id)
        items.append(
            {
                "id": task_id,
                "phase": _phase_of(task_id),
                "kind": _kind_of(task_id),
                "state": reading.states[task_id],
                "verdict": reading.verdicts.get(task_id),
                "report": reading.reports.get(task_id),
                "executor": reading.executors.get(task_id),
                "conflict": (
                    {"board": board_header[0], "header": board_header[1]} if board_header else None
                ),
                "inLog": True,
            }
        )
    # A planned ID the log has no row or report for yet still counts toward its phase.
    in_log = set(reading.order)
    for task_id in guide_ids:
        if task_id in in_log or _phase_of(task_id) is None:
            continue
        in_log.add(task_id)
        items.append(
            {
                "id": task_id,
                "phase": _phase_of(task_id),
                "kind": _kind_of(task_id),
                "state": "PENDING",
                "verdict": None,
                "report": None,
                "executor": None,
                "conflict": None,
                "inLog": False,
            }
        )

    numbers = sorted(
        set(guide_titles) | set(plan) | {i["phase"] for i in items if i["phase"] is not None}
    )
    phases = []
    for n in numbers:
        members = [i["id"] for i in items if i["phase"] == n]
        titles = (guide_titles.get(n, ""), plan.get(n, ("", 1.0))[0])
        title = next((t for t in titles if t and not PLACEHOLDER_RE.match(t)), "")
        phases.append(
            {
                "number": n,
                "id": f"P{n}",
                "title": title,
                "weight": plan.get(n, ("", 1.0))[1],
                "brokenDown": bool(members),
                "items": members,
            }
        )

    counts = Counter(i["state"] for i in items if i["inLog"])
    last_id = reading.last_header_id or (reading.order[-1] if reading.order else "")
    return {
        "schema": JSON_SCHEMA,
        "items": items,
        "phases": phases,
        "counts": dict(sorted(counts.items())),
        "open": [i["id"] for i in items if i["inLog"] and i["state"] != CLOSED],
        "mostRecent": {"id": last_id, "state": reading.states[last_id]} if last_id else None,
        "documents": {
            "executionGuide": guide_path.exists(),
            "planOfRecord": plan_path.exists(),
        },
    }


def run(target_dir: str, as_json: bool = False) -> int:
    log_path = Path(target_dir) / "compliance-log.md"
    if not log_path.exists():
        print(f"error: {log_path} not found.", file=sys.stderr)
        return 2

    if as_json:
        print(json.dumps(collect(target_dir), indent=2, ensure_ascii=False))
        return 0

    reading = read_log(log_path.read_text(encoding="utf-8"))
    if not reading.order:
        print("no task entries found in compliance-log.md.")
        return 0

    states = reading.states
    counts = Counter(states.values())
    print("Status board:")
    for state, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"  {state:<15} {n}")

    open_items = [(tid, st) for tid, st in states.items() if st != CLOSED]
    print(f"\n{len(open_items)} open (not APPROVED):")
    for tid, st in open_items:
        report_of_item = reading.reports.get(tid)
        detail = f" (report: {report_of_item})" if report_of_item and st in VERDICTS else ""
        if tid in reading.conflicts:
            board_verdict, header_verdict = reading.conflicts[tid]
            detail = f" (status board: {board_verdict}, report header: {header_verdict})"
        print(f"  - {tid}: {st}{detail}")

    last_id = reading.last_header_id or reading.order[-1]
    print(f"\nMost recent entry: {last_id} ({states[last_id]})")
    return 0
