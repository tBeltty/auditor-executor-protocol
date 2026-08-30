from pathlib import Path

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
