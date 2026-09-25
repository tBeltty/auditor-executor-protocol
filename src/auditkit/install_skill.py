"""Provision the protocol skill (SKILL.md and references/) into an agent or workspace."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

REFERENCES_DIR = "references"


def _skill_source_dir() -> Path:
    """Directory holding SKILL.md and references/: the packaged copy, else the repo root."""
    packaged = Path(__file__).parent / "skill"
    if (packaged / "SKILL.md").exists():
        return packaged
    repo_root = Path(__file__).resolve().parent.parent.parent
    if (repo_root / "SKILL.md").exists():
        return repo_root
    raise FileNotFoundError("SKILL.md could not be found.")


def _reference_files(source: Path) -> list[Path]:
    ref_dir = source / REFERENCES_DIR
    return sorted(ref_dir.glob("*.md")) if ref_dir.is_dir() else []


def _bundle(source: Path) -> str:
    """Single-file form for destinations that hold one file (Cursor rules, custom paths)."""
    parts = [(source / "SKILL.md").read_text(encoding="utf-8").rstrip("\n")]
    for ref in _reference_files(source):
        body = ref.read_text(encoding="utf-8").rstrip("\n")
        parts.append(f"<!-- {REFERENCES_DIR}/{ref.name} -->\n\n{body}")
    return "\n\n---\n\n".join(parts) + "\n"


def _install(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.name != "SKILL.md":
        dest.write_text(_bundle(source), encoding="utf-8")
        return
    shutil.copyfile(source / "SKILL.md", dest)
    refs = _reference_files(source)
    if refs:
        ref_dest = dest.parent / REFERENCES_DIR
        ref_dest.mkdir(exist_ok=True)
        for ref in refs:
            shutil.copyfile(ref, ref_dest / ref.name)


def _detect_agent(target: Path) -> str:
    # 1. Check workspace marker directories
    if (target / ".agents").exists() or (target / ".gemini").exists():
        return "antigravity"
    if (target / ".claude").exists():
        return "claude"
    if (target / ".cursor").exists():
        return "cursor"

    # 2. Check runtime environment variables
    if os.environ.get("ANTIGRAVITY_AGENT") or os.environ.get("GEMINI_CLI"):
        return "antigravity"
    if os.environ.get("CLAUDE_CODE") or os.environ.get("CLAUDE_PROJECT_DIR"):
        return "claude"
    if os.environ.get("CURSOR_PROJECT_DIR"):
        return "cursor"

    # 3. Default fallback
    return "antigravity"


def resolve_dest_path(
    target_dir: str = ".",
    agent: str = "auto",
    is_global: bool = False,
    dest_path: str | None = None,
) -> Path:
    if dest_path:
        # A directory (existing, or written with a trailing separator) receives SKILL.md.
        if Path(dest_path).is_dir() or dest_path.endswith(("/", os.sep)):
            return Path(dest_path) / "SKILL.md"
        return Path(dest_path)

    home = Path.home()
    if is_global:
        if agent == "claude":
            return home / ".claude" / "skills" / "auditor-executor-protocol" / "SKILL.md"
        if agent == "cursor":
            return home / ".cursor" / "rules" / "auditor-executor-protocol.mdc"
        return home / ".gemini" / "config" / "skills" / "auditor-executor-protocol" / "SKILL.md"

    target = Path(target_dir).resolve()
    chosen_agent = _detect_agent(target) if agent == "auto" else agent

    if chosen_agent == "claude":
        return target / ".claude" / "skills" / "auditor-executor-protocol" / "SKILL.md"
    if chosen_agent == "cursor":
        return target / ".cursor" / "rules" / "auditor-executor-protocol.mdc"
    return target / ".agents" / "skills" / "auditor-executor-protocol" / "SKILL.md"


def run(
    target_dir: str = ".",
    agent: str = "auto",
    is_global: bool = False,
    dest_path: str | None = None,
    force: bool = False,
) -> int:
    try:
        source = _skill_source_dir()
    except FileNotFoundError as e:
        print(f"error: {e}")
        return 2

    dest = resolve_dest_path(
        target_dir=target_dir, agent=agent, is_global=is_global, dest_path=dest_path
    )

    if dest.exists() and not force:
        print(f"skip: {dest} already exists (use --force to overwrite)")
        return 0

    _install(source, dest)
    print(f"installed {dest}")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit install-skill")
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=".",
        help="target project directory (defaults to current directory)",
    )
    parser.add_argument(
        "--agent",
        choices=["antigravity", "claude", "cursor", "auto"],
        default="auto",
        help="target agent framework (default: auto-detect)",
    )
    parser.add_argument(
        "--global",
        dest="is_global",
        action="store_true",
        help="install to user-level global configuration directory",
    )
    parser.add_argument(
        "--dest",
        dest="dest_path",
        default=None,
        help="explicit destination file path (SKILL.md installs references/ beside it; any other name gets a single bundled file)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing destination file",
    )
    args = parser.parse_args(argv)
    return run(
        target_dir=args.target_dir,
        agent=args.agent,
        is_global=args.is_global,
        dest_path=args.dest_path,
        force=args.force,
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
