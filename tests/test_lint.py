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
    guide = "**Report:** `P0-T1`\n**Report:** `P0-T2`\n"
    _write(tmp_path, guide=guide, log=log)
    assert lint.run(str(tmp_path)) == 1


def test_annex_threshold_warns(tmp_path):
    annexes = [f"ANNEX_{c}.md" for c in "ABCDEFG"]
    guide = "### P0-T1 — Do a thing\n**Report:** `P0-T1`\n"
    _write(tmp_path, guide=guide, log="### P0-T1 — PENDING\n", annexes=annexes)
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
    guide = "### P0-T1 — Do a thing\n**Report:** `P0-T1`\n"
    _write(tmp_path, guide=guide, log="### P0-T1 — PENDING\n")
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


def test_missing_directory_or_documents_is_an_error(tmp_path, capsys):
    assert lint.run(str(tmp_path / "does-not-exist")) == 2
    (tmp_path / "execution-guide.md").write_text("", encoding="utf-8")
    assert lint.run(str(tmp_path)) == 2
    assert "missing compliance-log.md" in capsys.readouterr().out


def test_orphan_log_entry_is_flagged(tmp_path, capsys):
    guide = """
### P0-T1 — Do a thing
**Report:** `P0-T1`
"""
    log = """
### P0-T1 — PENDING
### P9-T9 — PENDING
"""
    _write(tmp_path, guide, log)
    assert lint.run(str(tmp_path)) == 1
    assert "[orphan report] 1 entry(ies)" in capsys.readouterr().out


def test_negated_negative_control_does_not_count(tmp_path):
    for proof in (
        "Negative control: n/a",
        "No negative control needed.",
        "negative control - none",
    ):
        guide = f"""
### P0-G1 — Gate: everything works

**Proven by:** the suite passing. {proof}

**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 1, proof


def test_empty_documents_are_not_clean(tmp_path, capsys):
    _write(tmp_path, guide="", log="")
    assert lint.run(str(tmp_path)) == 1
    assert "[empty guide]" in capsys.readouterr().out


def test_task_without_report_line_is_flagged(tmp_path, capsys):
    guide = """
### P0-T1 — implement auth
Steps only, no report line.

### P0-T2 — add tests
**Report:** `P0-T2`

### Notes — context
Not a task.
"""
    _write(tmp_path, guide, "### P0-T2 — PENDING\n")
    assert lint.run(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "[missing report line] 1 task(s)" in out
    assert "  - P0-T1" in out
    assert "Notes" not in out


def test_deferred_negative_control_does_not_count(tmp_path):
    for proof in (
        "Negative control: TBD",
        "Negative control: skipped for now",
        "Negative control: TODO",
        "The negative control step was not done.",
        "Negative control is pending.",
    ):
        guide = f"""
### P0-G1 — Gate: everything works

**Proven by:** the suite passing. {proof}

**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 1, proof


def test_bold_negative_control_deferral_does_not_count(tmp_path):
    for proof in (
        "**Negative control:** n/a",
        "**Negative control**: none",
        "- **Negative control:** TBD",
        "__Negative control:__ — pending",
    ):
        guide = f"""
### P0-G1 — Gate: everything works

**Proven by:** the suite passing.
{proof}

**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 1, proof


def test_done_with_only_a_deferral_as_output_is_flagged(tmp_path, capsys):
    guide = """
### P1-T1 — Do a thing
**Report:** `P1-T1`

### P1-G1 — Gate: it works
Negative control: revert the fix and watch test_x fail.
**Report:** `P1-G1`

### P1-T2 — Real output
**Report:** `P1-T2`
"""
    log = """
### P1-T1 — DONE
**Verify output:**
n/a

### P1-G1 — DONE
**Verify output:** TBD

### P1-T2 — DONE
**Verify output:**
```text
$ pytest -q
1 passed, n/a skipped
```
"""
    _write(tmp_path, guide, log)
    assert lint.run(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "[done without evidence] 2 report(s)" in out
    assert "  - P1-T1" in out and "  - P1-G1" in out
    assert "  - P1-T2" not in out
