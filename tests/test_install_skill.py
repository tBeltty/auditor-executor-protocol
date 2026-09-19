from pathlib import Path

from auditkit import install_skill


def test_install_skill_explicit_dest(tmp_path):
    dest = tmp_path / "custom" / "SKILL.md"
    code = install_skill.run(dest_path=str(dest))
    assert code == 0
    assert dest.exists()
    assert "Auditor / Executor Protocol" in dest.read_text(encoding="utf-8")


def test_install_skill_does_not_overwrite_without_force(tmp_path):
    dest = tmp_path / "custom" / "SKILL.md"
    dest.parent.mkdir(parents=True)
    dest.write_text("existing content", encoding="utf-8")

    code = install_skill.run(dest_path=str(dest))
    assert code == 0
    assert dest.read_text(encoding="utf-8") == "existing content"

    code_force = install_skill.run(dest_path=str(dest), force=True)
    assert code_force == 0
    assert "Auditor / Executor Protocol" in dest.read_text(encoding="utf-8")


def test_install_skill_antigravity_target(tmp_path):
    code = install_skill.run(target_dir=str(tmp_path), agent="antigravity")
    assert code == 0
    expected = tmp_path / ".agents" / "skills" / "auditor-executor-protocol" / "SKILL.md"
    assert expected.exists()


def test_install_skill_claude_target(tmp_path):
    code = install_skill.run(target_dir=str(tmp_path), agent="claude")
    assert code == 0
    expected = tmp_path / ".claude" / "skills" / "auditor-executor-protocol" / "SKILL.md"
    assert expected.exists()


def test_install_skill_cursor_target(tmp_path):
    code = install_skill.run(target_dir=str(tmp_path), agent="cursor")
    assert code == 0
    expected = tmp_path / ".cursor" / "rules" / "auditor-executor-protocol.mdc"
    assert expected.exists()


def test_install_skill_auto_detects_claude(tmp_path):
    (tmp_path / ".claude").mkdir()
    code = install_skill.run(target_dir=str(tmp_path), agent="auto")
    assert code == 0
    expected = tmp_path / ".claude" / "skills" / "auditor-executor-protocol" / "SKILL.md"
    assert expected.exists()
