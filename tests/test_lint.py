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


def test_negative_control_needs_content_not_a_label(tmp_path):
    for proof in (
        "**Negative control:**",
        "**Negative control:** —",
        "**Negative control:** <remove the guard and observe failure>",
        "**Negative control:** to be written",
        "**Negative control:** N.A.",
        "**Negative control:** ...",
    ):
        guide = f"""
### P0-G1 — Gate: login rejects bad tokens

{proof}
**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 1, proof


def test_stated_negative_control_on_the_next_line_counts(tmp_path):
    guide = """
### P0-G1 — Gate: login rejects bad tokens

**Negative control:**
remove the token check in auth.py, run test_login_rejects_bad_token, watch it fail.

**Report:** `P0-G1`
"""
    _write(tmp_path, guide, "### P0-G1 — PENDING\n")
    assert lint.run(str(tmp_path)) == 0


def test_done_with_punctuation_or_none_yet_as_output_is_flagged(tmp_path, capsys):
    ids = ("P0-T1", "P0-T2", "P0-T3")
    guide = "".join(f"\n### {i} — Do a thing\n**Report:** `{i}`\n" for i in ids)
    log = "".join(
        f"\n### {i} — DONE\n**Verify output:**\n{value}\n**Observations:** none\n"
        for i, value in zip(ids, ("-", "…", "None yet"))
    )
    _write(tmp_path, guide, log)
    assert lint.run(str(tmp_path)) == 1
    assert "[done without evidence] 3 report(s)" in capsys.readouterr().out


def test_plural_negative_controls_deferral_does_not_count(tmp_path):
    for proof in (
        "**Negative controls:** none",
        "Negative controls: n/a",
        "Negative controls: TBD",
    ):
        guide = f"""
### P0-G1 — Gate: login rejects bad tokens

{proof}

**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 1, proof


def test_scaffolded_gate_needs_a_control_once_reported_done(tmp_path, capsys):
    from auditkit import scaffold

    scaffold.run(str(tmp_path))
    assert lint.run(str(tmp_path)) == 0, "a fresh scaffold is clean"
    log = tmp_path / "compliance-log.md"
    text = log.read_text(encoding="utf-8")
    assert "### P0-G1 — PENDING" in text
    log.write_text(
        text.replace(
            "### P0-G1 — PENDING",
            "### P0-G1 — DONE\n**Verify output:**\n```text\n$ pytest -q\n3 passed\n```",
        ),
        encoding="utf-8",
    )
    assert lint.run(str(tmp_path)) == 1
    out = capsys.readouterr().out
    assert "[gate w/o negative control]" in out and "  - P0-G1" in out


def test_wrapped_deferrals_and_cross_references_do_not_count(tmp_path):
    for proof in (
        "**Negative control:** will add later",
        "**Negative control:** TBA",
        "**Negative control:** see above",
        "**Negative control:** we will write it later on",
    ):
        guide = f"""
### P0-G1 — Gate: login rejects bad tokens

{proof}

**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 1, proof


def test_passive_and_scheduled_deferrals_do_not_count(tmp_path):
    for proof in (
        "**Negative control:** will be added in P1.",
        "**Negative control:** will be written once the harness lands.",
        "**Negative control:** TBC once the test harness exists.",
        "**Negative control:** to follow in the next sprint.",
        "**Negative control:** coming soon, after the harness lands.",
        "**Negative control:** planned for the next release.",
    ):
        guide = f"""
### P0-G1 — Gate: login rejects bad tokens

{proof}

**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 1, proof


def test_a_real_short_control_is_accepted(tmp_path):
    guide = """
### P0-G1 — Gate: login rejects bad tokens

**Negative control:** revert the guard and watch test_auth fail.

**Report:** `P0-G1`
"""
    _write(tmp_path, guide, "### P0-G1 — PENDING\n")
    assert lint.run(str(tmp_path)) == 0


def test_refusals_written_as_the_control_do_not_count(tmp_path):
    for proof in (
        "**Negative control:** No control; the change is documentation only.",
        "**Negative control:** deliberately omitted since coverage is high already",
        "**Negative control:** we could not break it so there is nothing to show here",
    ):
        guide = f"""
### P0-G1 — Gate: login rejects bad tokens

{proof}

**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 1, proof


def test_waivers_and_refusals_in_other_words_do_not_count(tmp_path):
    for proof in (
        "**Negative control:** We decided it is not worth doing for this gate at all.",
        "**Negative control:** Does not apply here since this gate is documentation only.",
        "**Negative control:** Unable to break the protection without rewriting the module.",
        "**Negative control:** Not relevant for this gate, it only renames files.",
        "**Negative control:** We do not have one for this gate yet.",
        "**Negative control:** Waived by the tech lead for this release.",
        "**Negative control:** Out of scope for this gate and this phase.",
        "**Negative control:** Remove the guard; nothing fails, so it is fine.",
    ):
        guide = f"""
### P0-G1 — Gate: login rejects bad passwords

{proof}

**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 1, proof


def test_real_controls_in_different_words_are_accepted(tmp_path):
    for proof in (
        "**Negative control:** send an expired token and watch the request get a 401.",
        "**Negative control:** comment out the rate limiter, run the load test, it errors out.",
        "**Negative control:** set MAX_RETRIES to 0 and the retry test raises TimeoutError.",
    ):
        guide = f"""
### P0-G1 — Gate: login rejects bad passwords

{proof}

**Report:** `P0-G1`
"""
        _write(tmp_path, guide, "### P0-G1 — PENDING\n")
        assert lint.run(str(tmp_path)) == 0, proof
