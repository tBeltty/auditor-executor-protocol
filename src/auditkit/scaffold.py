"""Scaffold the four-document set into a target directory."""
from __future__ import annotations

import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

FILES = {
    "plan-of-record.md": "plan-of-record.md",
    "execution-guide.md": "execution-guide.md",
    "compliance-log.md": "compliance-log.md",
}


def run(target_dir: str, project_name: str | None = None, force: bool = False) -> int:
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "annexes").mkdir(exist_ok=True)

    name = project_name or target.resolve().name

    wrote = []
    skipped = []
    for template_name, out_name in FILES.items():
        src = TEMPLATES_DIR / template_name
        dst = target / out_name
        if dst.exists() and not force:
            skipped.append(dst)
            continue
        content = src.read_text(encoding="utf-8").replace("{{PROJECT_NAME}}", name)
        dst.write_text(content, encoding="utf-8")
        wrote.append(dst)

    for path in wrote:
        print(f"wrote  {path}")
    for path in skipped:
        print(f"skip   {path}  (exists, use --force to overwrite)")

    if not (target / "annexes" / ".gitkeep").exists():
        (target / "annexes" / ".gitkeep").write_text("", encoding="utf-8")

    print(f"\n{target}/ scaffolded. Read execution-guide.md's Rules of engagement first.")
    return 0


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit init")
    parser.add_argument("target_dir")
    parser.add_argument("--name", dest="project_name", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    return run(args.target_dir, args.project_name, args.force)


if __name__ == "__main__":
    sys.exit(main())
