"""Provision SKILL.md into an agent or workspace directory."""
from __future__ import annotations

from pathlib import Path


def _get_skill_content() -> str:
    template_skill = Path(__file__).parent / "templates" / "SKILL.md"
    if template_skill.exists():
        return template_skill.read_text(encoding="utf-8")
    repo_skill = Path(__file__).resolve().parent.parent.parent / "SKILL.md"
    if repo_skill.exists():
        return repo_skill.read_text(encoding="utf-8")
    raise FileNotFoundError("SKILL.md could not be found.")


def _detect_agent(target: Path) -> str:
    if (target / ".agents").exists() or (target / ".gemini").exists():
        return "antigravity"
    if (target / ".claude").exists():
        return "claude"
    if (target / ".cursor").exists():
        return "cursor"
    return "antigravity"


def resolve_dest_path(
    target_dir: str = ".",
    agent: str = "auto",
    is_global: bool = False,
    dest_path: str | None = None,
) -> Path:
    if dest_path:
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
        content = _get_skill_content()
    except FileNotFoundError as e:
        print(f"error: {e}")
        return 2

    dest = resolve_dest_path(target_dir=target_dir, agent=agent, is_global=is_global, dest_path=dest_path)

    if dest.exists() and not force:
        print(f"skip: {dest} already exists (use --force to overwrite)")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(content, encoding="utf-8")
    print(f"installed {dest}")
    return 0


def main(argv=None) -> int:
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
        help="explicit destination file path",
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
