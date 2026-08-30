"""Cross-check the document set for the failure modes this protocol names by hand:
task IDs that exist in one document but not the other, gates with no stated negative
control, near-duplicate paragraphs from append-only logging, and an annex count that
signals an under-verified plan rather than a healthy one.
"""
from __future__ import annotations

import hashlib
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPORT_ID_RE = re.compile(r"\*\*Report:\*\*\s*`?([A-Za-z0-9_.\-]+)`?")
GUIDE_HEADER_RE = re.compile(r"^###\s+([A-Za-z0-9_.\-]+)\s+—\s*(.*)$", re.MULTILINE)
LOG_HEADER_RE = re.compile(r"^###\s+([A-Za-z0-9_.\-]+)\s+—\s+([A-Za-z]+)\s*$", re.MULTILINE)
GATE_ID_RE = re.compile(r"-G\d+$|^G\d+$", re.IGNORECASE)

MIN_DUP_LEN = 120
DEFAULT_ANNEX_THRESHOLD = 6


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _guide_sections(text: str) -> list[tuple[str, str, str]]:
    """Return (id, title, body) for every '### ID — title' section."""
    matches = list(GUIDE_HEADER_RE.finditer(text))
    sections = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((m.group(1), m.group(2).strip(), text[start:end]))
    return sections


def _is_gate(task_id: str, title: str) -> bool:
    return bool(GATE_ID_RE.search(task_id)) or "gate" in title.lower()


HEADER_LINE_RE = re.compile(r"^###\s+.*$", re.MULTILINE)


def _duplicate_paragraphs(text: str) -> list[tuple[str, int]]:
    paragraphs = re.split(r"\n\s*\n", text)
    stripped = [HEADER_LINE_RE.sub("", p) for p in paragraphs]
    normalized = [re.sub(r"\s+", " ", p).strip() for p in stripped]
    normalized = [p for p in normalized if len(p) >= MIN_DUP_LEN]
    counts = Counter(normalized)
    return [(p, n) for p, n in counts.items() if n > 1]


def run(target_dir: str, annex_threshold: int = DEFAULT_ANNEX_THRESHOLD) -> int:
    target = Path(target_dir)
    guide_text = _read(target / "execution-guide.md")
    log_text = _read(target / "compliance-log.md")

    problems = 0

    # 1. Every **Report:** ID in the guide should have an entry in the log.
    guide_ids = REPORT_ID_RE.findall(guide_text)
    log_ids = {m.group(1) for m in LOG_HEADER_RE.finditer(log_text)}

    missing = [i for i in guide_ids if i not in log_ids]
    if missing:
        problems += len(missing)
        print(f"[missing report] {len(missing)} task(s) in execution-guide.md have no entry in compliance-log.md:")
        for i in missing:
            print(f"  - {i}")

    # 2. Gates with no stated negative control.
    gate_gaps = []
    for task_id, title, body in _guide_sections(guide_text):
        if _is_gate(task_id, title) and "negative control" not in body.lower():
            gate_gaps.append(task_id)
    if gate_gaps:
        problems += len(gate_gaps)
        print(f"[gate w/o negative control] {len(gate_gaps)} gate(s) don't mention a negative control:")
        for i in gate_gaps:
            print(f"  - {i}")

    # 3. Near-duplicate paragraphs in the log (append-only rot).
    dups = _duplicate_paragraphs(log_text)
    if dups:
        problems += len(dups)
        print(f"[duplicate content] {len(dups)} paragraph(s) repeated verbatim in compliance-log.md:")
        for p, n in dups:
            preview = p[:100] + ("…" if len(p) > 100 else "")
            print(f"  - x{n}: {preview}")

    # 4. Annex count as a plan-health signal.
    annex_dir = target / "annexes"
    if annex_dir.exists():
        annex_files = [f for f in annex_dir.iterdir() if f.is_file() and f.name != ".gitkeep"]
        if len(annex_files) > annex_threshold:
            problems += 1
            print(
                f"[annex count] {len(annex_files)} annexes exceeds the threshold of "
                f"{annex_threshold}. This usually means a phase's plan was under-verified "
                f"before work started, not that it hit unusual surprises. Worth naming as a "
                f"planning finding, not only fixing task by task."
            )

    if problems == 0:
        print("clean — no cross-document gaps found.")
        return 0

    print(f"\n{problems} issue(s) found.")
    return 1


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit lint")
    parser.add_argument("target_dir")
    parser.add_argument("--annex-threshold", type=int, default=DEFAULT_ANNEX_THRESHOLD)
    args = parser.parse_args(argv)
    return run(args.target_dir, args.annex_threshold)


if __name__ == "__main__":
    sys.exit(main())
