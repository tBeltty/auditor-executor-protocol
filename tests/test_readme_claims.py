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
