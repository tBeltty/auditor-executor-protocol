from auditkit import lint


def _write(target, guide="", log="", annexes=None):
    target.mkdir(parents=True, exist_ok=True)
    (target / "execution-guide.md").write_text(guide, encoding="utf-8")
    (target / "compliance-log.md").write_text(log, encoding="utf-8")
    if annexes:
        annex_dir = target / "annexes"
        annex_dir.mkdir(exist_ok=True)
        for name in annexes:
            (annex_dir / name).write_text("x", encoding="utf-8")


def test_clean_set_passes(tmp_path):
    guide = """
### P0-T1 — Do a thing

**Report:** `P0-T1`
"""
    log = """
### P0-T1 — DONE
**Changed:** foo.py
**Verify output:**
```
3 passed in 0.12s
```
**Observations:** none
"""
    _write(tmp_path, guide, log)
    assert lint.run(str(tmp_path)) == 0


def test_missing_report_is_flagged(tmp_path):
    guide = """
### P0-T1 — Do a thing

**Report:** `P0-T1`
"""
    _write(tmp_path, guide, log="")
    assert lint.run(str(tmp_path)) == 1


def test_gate_without_negative_control_is_flagged(tmp_path):
    guide = """
### P0-G1 — Gate: everything works

**Proven by:** the suite passing.

**Report:** `P0-G1`
"""
    log = """
### P0-G1 — APPROVED
"""
    _write(tmp_path, guide, log)
    assert lint.run(str(tmp_path)) == 1


def test_gate_with_negative_control_passes(tmp_path):
    guide = """
### P0-G1 — Gate: everything works

**Proven by:** a negative control — remove the check, observe it fail, restore, observe it pass.

**Report:** `P0-G1`
"""
    log = """
### P0-G1 — APPROVED
"""
    _write(tmp_path, guide, log)
    assert lint.run(str(tmp_path)) == 0


def test_duplicate_paragraph_is_flagged(tmp_path):
    paragraph = (
        "This open condition keeps getting copied verbatim into every new log entry "
        "instead of being compacted into one current statement, which is exactly the "
        "kind of rot this check exists to catch."
    )
    log = f"""
### P0-T1 — DONE
{paragraph}

### P0-T2 — DONE
{paragraph}
"""
    _write(tmp_path, guide="", log=log)
    assert lint.run(str(tmp_path)) == 1


def test_annex_threshold_warns(tmp_path):
    annexes = [f"ANNEX_{c}.md" for c in "ABCDEFG"]
    _write(tmp_path, annexes=annexes)
    assert lint.run(str(tmp_path), annex_threshold=6) == 1
    assert lint.run(str(tmp_path), annex_threshold=10) == 0


def test_headers_with_hyphens_and_endash_pass(tmp_path):
    guide = """
### P0-T1 - Standard hyphen
**Report:** `P0-T1`

### P0-T2 – En-dash
**Report:** `P0-T2`
"""
    log = """
### P0-T1 - PENDING
### P0-T2 – PENDING
"""
    _write(tmp_path, guide, log)
    assert lint.run(str(tmp_path)) == 0


def test_annex_phase_breakdown_warns(tmp_path, capsys):
    annexes = [f"P1-ANNEX-{i}.md" for i in range(4)] + [f"P2-ANNEX-{i}.md" for i in range(4)]
    _write(tmp_path, annexes=annexes)
    assert lint.run(str(tmp_path), annex_threshold=5) == 1
    out = capsys.readouterr().out
    assert "Phase 1" in out
    assert "Phase 2" in out


def test_lint_main_cli(tmp_path):
    _write(tmp_path, guide="", log="")
    code = lint.main([str(tmp_path), "--annex-threshold", "10"])
    assert code == 0


def test_done_without_verify_output_is_flagged(tmp_path, capsys):
    guide = """
### P0-T1 — Do a thing
**Report:** `P0-T1`

### P0-T2 — Do another thing
**Report:** `P0-T2`

### P0-T3 — And a third
**Report:** `P0-T3`
"""
    log = """
### P0-T1 — DONE
**Changed:** a.py
**Verify output:**
**Observations:** none

### P0-T2 — DONE
**Changed:** b.py
**Verify output:**
<pasted, literal, unedited command output>
```text
```
**Observations:** none

### P0-T3 — DONE
**Changed:** c.py
"""
    _write(tmp_path, guide, log)
    assert lint.run(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "[done without evidence] 3 report(s)" in out
    for task_id in ("P0-T1", "P0-T2", "P0-T3"):
        assert f"  - {task_id}" in out


def test_pending_and_blocked_reports_need_no_evidence(tmp_path):
    guide = """
### P0-T1 — Do a thing
**Report:** `P0-T1`

### P0-T2 — Do another thing
**Report:** `P0-T2`
"""
    log = """
### P0-T1 — PENDING
**Verify output:**

### P0-T2 — BLOCKED
**Verify output:**
"""
    _write(tmp_path, guide, log)
    assert lint.run(str(tmp_path)) == 0
