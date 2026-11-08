from aepkit import status


def test_status_counts_verdicts(tmp_path, capsys):
    log = """
### P0-T1 — DONE
### P0-T2 — BLOCKED
### P0-G1 — APPROVED
"""
    (tmp_path / "compliance-log.md").write_text(log, encoding="utf-8")
    code = status.run(str(tmp_path))
    out = capsys.readouterr().out
    assert code == 0
    assert "AWAITING AUDIT" in out
    assert "BLOCKED" in out
    assert "APPROVED" in out
    # DONE is a self-report awaiting audit; only APPROVED closes an item.
    assert "2 open" in out
    assert "P0-T1: AWAITING AUDIT" in out
    assert "P0-T2: BLOCKED" in out


def test_status_last_entry_wins_on_resubmission(tmp_path, capsys):
    log = """
### P0-T1 — FAILED
### P0-T1 — DONE
"""
    (tmp_path / "compliance-log.md").write_text(log, encoding="utf-8")
    status.run(str(tmp_path))
    out = capsys.readouterr().out
    assert "1 open" in out
    assert "P0-T1: AWAITING AUDIT" in out


def test_status_counts_rejected_and_handles_hyphens(tmp_path, capsys):
    log = """
### P0-T1 - DONE
### P0-T2 - REJECTED
"""
    (tmp_path / "compliance-log.md").write_text(log, encoding="utf-8")
    code = status.run(str(tmp_path))
    out = capsys.readouterr().out
    assert code == 0
    assert "REJECTED" in out
    assert "2 open" in out
    assert "P0-T2: REJECTED" in out


def test_status_missing_log_returns_error(tmp_path, capsys):
    code = status.run(str(tmp_path))
    out = capsys.readouterr().err
    assert code == 2
    assert "not found" in out


def test_status_empty_log(tmp_path, capsys):
    (tmp_path / "compliance-log.md").write_text("# Empty log\n", encoding="utf-8")
    code = status.run(str(tmp_path))
    out = capsys.readouterr().out
    assert code == 0
    assert "no task entries found" in out


def test_status_reads_verdicts_from_the_status_board(tmp_path, capsys):
    log = """
## Status board

| ID | Delivery | Verdict | Notes |
|---|---|---|---|
| P0-T1 | abc123 | `APPROVED` | |
| P0-T2 | def456 | `REJECTED` | fixture broken |
| P0-G1 | | `PENDING` | |

## Reports

### P0-T1 — DONE
### P0-T2 — DONE
### P0-G1 — PENDING
"""
    (tmp_path / "compliance-log.md").write_text(log, encoding="utf-8")
    assert status.run(str(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "2 open" in out
    assert "P0-T2: REJECTED (report: DONE)" in out
    assert "P0-G1: PENDING" in out
    assert "P0-T1" not in out.split("open (not APPROVED):")[1].split("Most recent")[0]


def test_status_on_a_fresh_scaffold_lists_every_item_open(tmp_path, capsys):
    from aepkit import scaffold

    scaffold.run(str(tmp_path), "demo")
    capsys.readouterr()
    assert status.run(str(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "2 open" in out


def test_conflicting_verdicts_stay_open(tmp_path, capsys):
    log = """
| ID | Delivery | Verdict | Notes |
|---|---|---|---|
| P0-T1 | abc | `APPROVED` | |

### P0-T1 — DONE
### P0-T1 — REJECTED
"""
    (tmp_path / "compliance-log.md").write_text(log, encoding="utf-8")
    assert status.run(str(tmp_path)) == 0
    out = capsys.readouterr().out
    assert "1 open" in out
    assert "P0-T1: CONFLICT (status board: APPROVED, report header: REJECTED)" in out


def _json(tmp_path, capsys, log, guide=None, plan=None):
    import json

    (tmp_path / "compliance-log.md").write_text(log, encoding="utf-8")
    if guide is not None:
        (tmp_path / "execution-guide.md").write_text(guide, encoding="utf-8")
    if plan is not None:
        (tmp_path / "plan-of-record.md").write_text(plan, encoding="utf-8")
    assert status.run(str(tmp_path), as_json=True) == 0
    return json.loads(capsys.readouterr().out)


def test_json_on_an_empty_log(tmp_path, capsys):
    data = _json(tmp_path, capsys, "# Empty log\n")
    assert data["schema"] == 1
    assert data["items"] == []
    assert data["phases"] == []
    assert data["open"] == []
    assert data["mostRecent"] is None


def test_json_on_an_empty_board_counts_the_guide(tmp_path, capsys):
    log = """
## Status board

| ID | Delivery | Verdict | Notes |
|---|---|---|---|
"""
    guide = """
# Phase 0 — Setup

### P0-T1 — Do the thing
**Report:** `P0-T1`

### P0-G1 — Gate: it holds
**Report:** `P0-G1`
"""
    data = _json(tmp_path, capsys, log, guide=guide)
    assert [(i["id"], i["state"], i["inLog"]) for i in data["items"]] == [
        ("P0-T1", "PENDING", False),
        ("P0-G1", "PENDING", False),
    ]
    assert [i["kind"] for i in data["items"]] == ["task", "gate"]
    # Only what the log holds is counted as open, as in the text output.
    assert data["open"] == []
    assert data["phases"] == [
        {
            "number": 0,
            "id": "P0",
            "title": "Setup",
            "weight": 1.0,
            "brokenDown": True,
            "items": ["P0-T1", "P0-G1"],
        }
    ]


def test_json_reports_a_conflict_between_board_and_header(tmp_path, capsys):
    log = """
| ID | Delivery | Verdict | Notes |
|---|---|---|---|
| P0-T1 | abc | `APPROVED` | |

### P0-T1 — DONE
### P0-T1 — REJECTED
"""
    data = _json(tmp_path, capsys, log)
    (item,) = data["items"]
    assert item["state"] == "CONFLICT"
    assert item["conflict"] == {"board": "APPROVED", "header": "REJECTED"}
    assert item["verdict"] == "APPROVED"
    assert item["report"] == "DONE"
    assert data["open"] == ["P0-T1"]
    assert data["counts"] == {"CONFLICT": 1}


def test_json_lists_phases_the_guide_has_not_broken_down(tmp_path, capsys):
    log = """
| ID | Executor | Verdict | Notes |
|---|---|---|---|
| P0-T1 | Ana | `APPROVED` | |
| P1-T1 | Bo | `PENDING` | |

### P1-T1 — DONE
"""
    guide = """
# Phase 0 — Groundwork
### P0-T1 — a
# Phase 1 — <name>
### P1-T1 — b
"""
    plan = """
## 5. Phases

| Phase | Delivers | Risk | Weight |
|---|---|---|---|
| P0 | Groundwork | low | 1 |
| P1 | The core | high | 3 |
| P2 | Polish | low | |
"""
    data = _json(tmp_path, capsys, log, guide=guide, plan=plan)
    phases = {p["id"]: p for p in data["phases"]}
    assert phases["P0"]["title"] == "Groundwork"
    # A placeholder heading falls back to the plan's "Delivers" column.
    assert phases["P1"]["title"] == "The core"
    assert phases["P1"]["weight"] == 3.0
    assert phases["P2"] == {
        "number": 2,
        "id": "P2",
        "title": "Polish",
        "weight": 1.0,
        "brokenDown": False,
        "items": [],
    }
    items = {i["id"]: i for i in data["items"]}
    assert items["P0-T1"]["executor"] == "Ana"
    assert items["P1-T1"]["state"] == "AWAITING AUDIT"
    assert data["mostRecent"] == {"id": "P1-T1", "state": "AWAITING AUDIT"}


def test_json_missing_log_is_an_error(tmp_path, capsys):
    assert status.run(str(tmp_path), as_json=True) == 2
    assert "not found" in capsys.readouterr().err


SAMPLE_PLAN = """\
# Sample — Plan of Record

## 5. Phases

| Phase | Delivers | Risk | Weight |
|---|---|---|---|
| P0 | Groundwork | low | 1 |
| P1 | The core feature | high | 2 |
| P2 | Hardening | medium | 1 |
"""

SAMPLE_GUIDE = """\
# Sample — Execution Guide

# Phase 0 — Groundwork

### P0-T1 — Set up the project
**Report:** `P0-T1`

### P0-G1 — Gate: the build runs clean
**Report:** `P0-G1`

# Phase 1 — The core feature

### P1-T1 — Add the parser
**Report:** `P1-T1`

### P1-T2 — Add the writer
**Report:** `P1-T2`

### P1-T3 — Wire the command
**Report:** `P1-T3`

### P1-G1 — Gate: round trip holds
**Report:** `P1-G1`
"""

SAMPLE_LOG = """\
# Sample — Compliance Log

## Status board

| ID | Executor | Verdict | Notes |
|---|---|---|---|
| P0-T1 | Ana | `APPROVED` | |
| P0-G1 | Ana | `APPROVED` | |
| P1-T1 | Bo | `APPROVED` | |
| P1-T2 | Bo | `CONDITIONAL` | missing error path test |
| P1-T3 | Cy | `PENDING` | |
| P1-G1 | | `PENDING` | |

## Reports

### P1-T3 — DONE
"""


def test_json_matches_what_the_progress_pane_is_tested_against(tmp_path, capsys):
    """The pane's tests stand in for aepkit with this JSON; it must stay aepkit's own."""
    import json
    from pathlib import Path

    import pytest

    fixture = (
        Path(__file__).resolve().parent.parent
        / "integrations"
        / "claude-code"
        / "aeprogress"
        / "tests"
        / "fixtures"
        / "status.ts"
    )
    if not fixture.exists():
        pytest.skip("the progress pane is not shipped in the sdist")
    expected = json.loads(fixture.read_text(encoding="utf-8").split("export const STATUS = ", 1)[1])
    (tmp_path / "plan-of-record.md").write_text(SAMPLE_PLAN, encoding="utf-8")
    (tmp_path / "execution-guide.md").write_text(SAMPLE_GUIDE, encoding="utf-8")
    (tmp_path / "compliance-log.md").write_text(SAMPLE_LOG, encoding="utf-8")
    assert status.run(str(tmp_path), as_json=True) == 0
    assert json.loads(capsys.readouterr().out) == expected
    phases = {p["id"]: p for p in expected["phases"]}
    assert phases["P2"]["brokenDown"] is False
    assert phases["P1"]["weight"] == 2.0
