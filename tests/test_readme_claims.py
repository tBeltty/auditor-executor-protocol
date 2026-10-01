"""Checks that what README.md says each command does is what it does."""

import re
import sys
from pathlib import Path

from auditkit import cli

README = Path(__file__).resolve().parent.parent / "README.md"
PY = f'"{sys.executable}"'


def _help(capsys, command):
    try:
        cli.main([command, "--help"])
    except SystemExit:
        pass
    return capsys.readouterr().out


def test_cli_reference_options_exist(capsys):
    rows = re.findall(
        r"^\| `auditkit ([a-z-]+)[^`]*` \|([^|]*)\|", README.read_text(encoding="utf-8"), re.M
    )
    assert len(rows) == 5
    for command, options in rows:
        out = _help(capsys, command)
        for option in re.findall(r"--[a-z-]+", options):
            assert option in out, f"{command} {option}"


def test_init_creates_documents_and_keeps_existing(tmp_path):
    target = tmp_path / "my-task"
    assert cli.main(["init", str(target)]) == 0
    for name in ("plan-of-record.md", "execution-guide.md", "compliance-log.md"):
        assert (target / name).is_file()
    assert (target / "annexes").is_dir()
    assert "my-task" in (target / "plan-of-record.md").read_text(encoding="utf-8")

    (target / "plan-of-record.md").write_text("mine", encoding="utf-8")
    cli.main(["init", str(target)])
    assert (target / "plan-of-record.md").read_text(encoding="utf-8") == "mine"


def test_lint_exit_codes(tmp_path):
    target = tmp_path / "t"
    assert cli.main(["lint", str(target)]) == 2
    cli.main(["init", str(target)])
    assert cli.main(["lint", str(target)]) == 0
    log = target / "compliance-log.md"
    text = log.read_text(encoding="utf-8").replace("P0-T1 — PENDING", "P0-T1 — DONE")
    log.write_text(text, encoding="utf-8")
    assert cli.main(["lint", str(target)]) == 1


def test_status_exit_codes(tmp_path):
    assert cli.main(["status", str(tmp_path)]) == 2
    cli.main(["init", str(tmp_path)])
    assert cli.main(["status", str(tmp_path)]) == 0


def test_install_skill_destinations(tmp_path):
    expected = {
        "antigravity": ".agents/skills/auditor-executor-protocol/SKILL.md",
        "claude": ".claude/skills/auditor-executor-protocol/SKILL.md",
        "cursor": ".cursor/rules/auditor-executor-protocol.mdc",
    }
    for agent, path in expected.items():
        assert cli.main(["install-skill", str(tmp_path), "--agent", agent]) == 0
        assert (tmp_path / path).is_file()
    assert (tmp_path / ".claude/skills/auditor-executor-protocol/references").is_dir()


def test_negcontrol_verifies_a_real_protection(tmp_path):
    guarded = tmp_path / "guard.txt"
    guarded.write_text("protected\n", encoding="utf-8")
    test_cmd = f"{PY} -c \"import sys; sys.exit(open(r'{guarded}').read() != 'protected\\n')\""
    break_cmd = f"{PY} -c \"open(r'{guarded}', 'w').write('broken')\""
    args = ["negcontrol", "--file", str(guarded), "--test-cmd", test_cmd]

    assert cli.main([*args, "--break-cmd", break_cmd]) == 0
    assert guarded.read_text(encoding="utf-8") == "protected\n"
    # A break that removes nothing: the test never fails, so the control is rejected.
    assert cli.main([*args, "--break-cmd", f'{PY} -c "pass"']) == 1
    assert cli.main(["negcontrol", "--test-cmd", test_cmd]) == 2


# The README's promises: drift and unverified claims are caught, not just reported.

GUIDE = """### P0-T1 — Add auth middleware
**Report:** `P0-T1`

### P0-G1 — Gate: anonymous requests are rejected
**Negative control:** {control}
**Report:** `P0-G1`
"""
LOG = """### P0-T1 — DONE
**Verify output:**
{output}
**Observations:** none

### P0-G1 — PENDING
**Verify output:**
"""
REAL_CONTROL = "remove requireAuth from the router; auth.test.js fails with 200 instead of 401"
REAL_OUTPUT = "```\nPASS auth.test.js (3 tests)\n```"


def _lint(tmp_path, control=REAL_CONTROL, output=REAL_OUTPUT, extra_log=""):
    (tmp_path / "execution-guide.md").write_text(GUIDE.format(control=control), encoding="utf-8")
    log = LOG.format(output=output) + extra_log
    (tmp_path / "compliance-log.md").write_text(log, encoding="utf-8")
    return cli.main(["lint", str(tmp_path)])


def test_promise_honest_document_set_is_clean(tmp_path):
    assert _lint(tmp_path) == 0


def test_promise_done_without_pasted_output_is_caught(tmp_path, capsys):
    assert _lint(tmp_path, output="n/a") == 1
    assert "[done without evidence]" in capsys.readouterr().out


def test_promise_waived_negative_control_is_caught(tmp_path, capsys):
    for waiver in ("n/a", "not needed, the framework handles auth"):
        assert _lint(tmp_path, control=waiver) == 1
    assert "[gate w/o negative control]" in capsys.readouterr().out


def test_promise_report_for_unplanned_work_is_caught(tmp_path, capsys):
    assert _lint(tmp_path, extra_log="\n### P0-T9 — DONE\n**Verify output:**\nok\n") == 1
    assert "[orphan report]" in capsys.readouterr().out


def test_promise_self_reported_done_stays_open(tmp_path, capsys):
    _lint(tmp_path)
    cli.main(["status", str(tmp_path)])
    assert "P0-T1: AWAITING AUDIT" in capsys.readouterr().out


def test_promise_negcontrol_rejects_a_test_that_cannot_fail(tmp_path):
    """A suite that stays green because it never checks the protection is not verification."""
    guarded = tmp_path / "guard.txt"
    guarded.write_text("protected\n", encoding="utf-8")
    break_cmd = f"{PY} -c \"import os; os.remove(r'{guarded}')\""
    code = cli.main(
        [
            "negcontrol",
            "--file",
            str(guarded),
            "--break-cmd",
            break_cmd,
            "--test-cmd",
            f'{PY} -c "pass"',
        ]
    )
    assert code == 1
    assert guarded.read_text(encoding="utf-8") == "protected\n"
