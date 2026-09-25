from auditkit import status


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
    out = capsys.readouterr().out
    assert code == 2
    assert "not found" in out


def test_status_empty_log(tmp_path, capsys):
    (tmp_path / "compliance-log.md").write_text("# Empty log\n", encoding="utf-8")
    code = status.run(str(tmp_path))
    out = capsys.readouterr().out
    assert code == 0
    assert "no task entries found" in out


def test_status_main_cli(tmp_path):
    log = "### P0-T1 — DONE\n"
    (tmp_path / "compliance-log.md").write_text(log, encoding="utf-8")
    code = status.main([str(tmp_path)])
    assert code == 0


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
    from auditkit import scaffold

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
