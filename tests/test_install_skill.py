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
    bundled = expected.read_text(encoding="utf-8")
    assert "Auditor / Executor Protocol" in bundled
    assert "<!-- references/autonomous-mode.md -->" in bundled
    assert "The autonomy charter" in bundled


def test_install_skill_copies_references_beside_skill(tmp_path):
    code = install_skill.run(target_dir=str(tmp_path), agent="claude")
    assert code == 0
    skill_dir = tmp_path / ".claude" / "skills" / "auditor-executor-protocol"
    refs = sorted(p.name for p in (skill_dir / "references").glob("*.md"))
    assert refs == [
        "autonomous-mode.md",
        "failure-modes-and-example.md",
        "handoffs.md",
        "tasks-and-gates.md",
    ]
    assert "## Autonomous mode (Auditor)" in (
        skill_dir / "references" / "autonomous-mode.md"
    ).read_text(encoding="utf-8")


def test_install_skill_bundles_for_non_skill_filenames(tmp_path):
    dest = tmp_path / "rules.md"
    assert install_skill.run(dest_path=str(dest)) == 0
    assert "## Writing a task (Auditor)" in dest.read_text(encoding="utf-8")
    assert not (tmp_path / "references").exists()


def test_install_skill_missing_source_returns_error(tmp_path, capsys):
    original = install_skill._skill_source_dir

    def missing() -> None:
        raise FileNotFoundError("SKILL.md could not be found.")

    install_skill._skill_source_dir = missing  # type: ignore[assignment]
    try:
        assert install_skill.run(dest_path=str(tmp_path / "SKILL.md")) == 2
    finally:
        install_skill._skill_source_dir = original  # type: ignore[assignment]
    assert "could not be found" in capsys.readouterr().out


def test_install_skill_auto_detects_claude(tmp_path):
    (tmp_path / ".claude").mkdir()
    code = install_skill.run(target_dir=str(tmp_path), agent="auto")
    assert code == 0
    expected = tmp_path / ".claude" / "skills" / "auditor-executor-protocol" / "SKILL.md"
    assert expected.exists()


def test_install_skill_auto_detects_via_env_var(tmp_path, monkeypatch=None):
    import os

    old_claude = os.environ.get("CLAUDE_CODE")
    old_antigravity = os.environ.get("ANTIGRAVITY_AGENT")
    try:
        os.environ["CLAUDE_CODE"] = "1"
        if "ANTIGRAVITY_AGENT" in os.environ:
            del os.environ["ANTIGRAVITY_AGENT"]
        code = install_skill.run(target_dir=str(tmp_path), agent="auto")
        assert code == 0
        expected = tmp_path / ".claude" / "skills" / "auditor-executor-protocol" / "SKILL.md"
        assert expected.exists()
    finally:
        if old_claude is not None:
            os.environ["CLAUDE_CODE"] = old_claude
        elif "CLAUDE_CODE" in os.environ:
            del os.environ["CLAUDE_CODE"]

        if old_antigravity is not None:
            os.environ["ANTIGRAVITY_AGENT"] = old_antigravity


def test_install_skill_global_flag():
    dest_claude = install_skill.resolve_dest_path(agent="claude", is_global=True)
    assert ".claude" in str(dest_claude)
    dest_cursor = install_skill.resolve_dest_path(agent="cursor", is_global=True)
    assert ".cursor" in str(dest_cursor)
    dest_anti = install_skill.resolve_dest_path(agent="antigravity", is_global=True)
    assert ".gemini" in str(dest_anti)


def test_install_skill_main_cli(tmp_path):
    dest = tmp_path / "installed_skill.md"
    code = install_skill.main(["--dest", str(dest), "--force"])
    assert code == 0
    assert dest.exists()


def test_install_skill_markers_and_env(tmp_path):
    import os

    # Marker .gemini
    gemini_dir = tmp_path / "gemini_proj"
    (gemini_dir / ".gemini").mkdir(parents=True)
    assert install_skill._detect_agent(gemini_dir) == "antigravity"

    # Marker .cursor
    cursor_dir = tmp_path / "cursor_proj"
    (cursor_dir / ".cursor").mkdir(parents=True)
    assert install_skill._detect_agent(cursor_dir) == "cursor"

    # Env CURSOR_PROJECT_DIR
    clean_dir = tmp_path / "clean_proj"
    clean_dir.mkdir(parents=True)
    old_cursor = os.environ.get("CURSOR_PROJECT_DIR")
    old_anti = os.environ.get("ANTIGRAVITY_AGENT")
    old_gemini = os.environ.get("GEMINI_CLI")
    try:
        os.environ["CURSOR_PROJECT_DIR"] = "/fake"
        if "ANTIGRAVITY_AGENT" in os.environ:
            del os.environ["ANTIGRAVITY_AGENT"]
        if "GEMINI_CLI" in os.environ:
            del os.environ["GEMINI_CLI"]
        assert install_skill._detect_agent(clean_dir) == "cursor"
    finally:
        if old_cursor is not None:
            os.environ["CURSOR_PROJECT_DIR"] = old_cursor
        elif "CURSOR_PROJECT_DIR" in os.environ:
            del os.environ["CURSOR_PROJECT_DIR"]
        if old_anti is not None:
            os.environ["ANTIGRAVITY_AGENT"] = old_anti
        if old_gemini is not None:
            os.environ["GEMINI_CLI"] = old_gemini
