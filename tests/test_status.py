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
    assert "DONE" in out
    assert "BLOCKED" in out
    assert "APPROVED" in out
    assert "1 open" in out  # only P0-T2/BLOCKED is open


def test_status_last_entry_wins_on_resubmission(tmp_path, capsys):
    log = """
### P0-T1 — FAILED
### P0-T1 — DONE
"""
    (tmp_path / "compliance-log.md").write_text(log, encoding="utf-8")
    status.run(str(tmp_path))
    out = capsys.readouterr().out
    assert "0 open" in out
