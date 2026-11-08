import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PACKAGED = REPO / "src" / "aepkit" / "skill"
SYNC_HINT = (
    "packaged skill is out of sync with the repo root; run: "
    "cp SKILL.md src/aepkit/skill/ && cp references/*.md src/aepkit/skill/references/"
)


def _skill_files(root: Path) -> dict[str, str]:
    paths = [root / "SKILL.md", *sorted((root / "references").glob("*.md"))]
    return {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8") for p in paths}


def test_packaged_skill_matches_repo_root():
    assert _skill_files(PACKAGED) == _skill_files(REPO), SYNC_HINT


def test_claude_code_plugin_skill_matches_repo_root():
    """The plugin brings the protocol as a skill: its copy must be the repo root's."""
    bundled = (
        REPO
        / "integrations"
        / "claude-code"
        / "aeprogress"
        / "skills"
        / "auditor-executor-protocol"
    )
    if not bundled.exists():
        return  # the sdist ships no integrations/; the repository checkout always has it
    assert _skill_files(bundled) == _skill_files(REPO), (
        "the plugin's skill is out of sync with the repo root; run: "
        "cp SKILL.md integrations/claude-code/aeprogress/skills/auditor-executor-protocol/ && "
        "cp references/*.md integrations/claude-code/aeprogress/skills/auditor-executor-protocol/references/"
    )


def test_every_reference_is_linked_and_every_link_resolves():
    text = (REPO / "SKILL.md").read_text(encoding="utf-8")
    linked = set(re.findall(r"\]\(references/([\w.-]+\.md)\)", text))
    on_disk = {p.name for p in (REPO / "references").glob("*.md")}
    assert linked == on_disk
