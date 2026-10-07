"""Scaffold the document set: three documents and an annexes/ directory."""

from __future__ import annotations

import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

DOCUMENTS = ("plan-of-record.md", "execution-guide.md", "compliance-log.md")


def run(target_dir: str, project_name: str | None = None, force: bool = False) -> int:
    target = Path(target_dir)
    if target.exists() and not target.is_dir():
        print(f"error: {target_dir} exists and is not a directory.", file=sys.stderr)
        return 2
    target.mkdir(parents=True, exist_ok=True)
    (target / "annexes").mkdir(exist_ok=True)

    name = project_name or target.resolve().name

    wrote = []
    skipped = []
    for doc in DOCUMENTS:
        src = TEMPLATES_DIR / doc
        dst = target / doc
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
