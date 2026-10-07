import os
from collections.abc import Iterator
from contextlib import contextmanager

from auditkit import install_skill

# Every variable _detect_agent reads, so the caller's own agent cannot leak into a test.
DETECTION_VARS = (
    "ANTIGRAVITY_AGENT",
    "GEMINI_CLI",
    "CLAUDECODE",
    "CLAUDE_CODE",
    "CLAUDE_PROJECT_DIR",
    "CURSOR_PROJECT_DIR",
)


@contextmanager
def _detection_env(**values: str) -> Iterator[None]:
    """Clear every detection variable, set only `values`, and restore all of them after."""
    saved = {var: os.environ.pop(var, None) for var in DETECTION_VARS}
    os.environ.update(values)
    try:
        yield
    finally:
        for var, value in saved.items():
            os.environ.pop(var, None)
            if value is not None:
                os.environ[var] = value


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
    assert "could not be found" in capsys.readouterr().err


def test_install_skill_auto_detects_claude(tmp_path):
    (tmp_path / ".claude").mkdir()
    code = install_skill.run(target_dir=str(tmp_path), agent="auto")
    assert code == 0
    expected = tmp_path / ".claude" / "skills" / "auditor-executor-protocol" / "SKILL.md"
    assert expected.exists()


def test_install_skill_auto_detects_via_env_var(tmp_path):
    for var in ("CLAUDECODE", "CLAUDE_CODE", "CLAUDE_PROJECT_DIR"):
        target = tmp_path / var
        target.mkdir()
        with _detection_env(**{var: "1"}):
            code = install_skill.run(target_dir=str(target), agent="auto")
        assert code == 0
        expected = target / ".claude" / "skills" / "auditor-executor-protocol" / "SKILL.md"
        assert expected.exists(), var


def test_install_skill_global_flag():
    dest_claude = install_skill.resolve_dest_path(agent="claude", is_global=True)
    assert ".claude" in str(dest_claude)
    dest_cursor = install_skill.resolve_dest_path(agent="cursor", is_global=True)
    assert ".cursor" in str(dest_cursor)
    dest_anti = install_skill.resolve_dest_path(agent="antigravity", is_global=True)
    assert ".gemini" in str(dest_anti)


def test_install_skill_markers_and_env(tmp_path):
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
    with _detection_env(CURSOR_PROJECT_DIR="/fake"):
        assert install_skill._detect_agent(clean_dir) == "cursor"
    with _detection_env():
        assert install_skill._detect_agent(clean_dir) == "antigravity"


def test_install_skill_dest_directory_receives_skill_md(tmp_path):
    existing = tmp_path / "skills"
    existing.mkdir()
    assert install_skill.run(dest_path=str(existing), force=True) == 0
    assert (existing / "SKILL.md").is_file()
    assert (existing / "references" / "handoffs.md").is_file()

    new_dir = tmp_path / "newdir"
    assert install_skill.run(dest_path=f"{new_dir}/") == 0
    assert (new_dir / "SKILL.md").is_file()
