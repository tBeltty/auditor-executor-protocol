"""Cross-check the document set for the failure modes this protocol names by hand:
task IDs that exist in one document but not the other, gates with no stated negative
control, DONE reports with no pasted verify output, near-duplicate paragraphs from
append-only logging, and an annex count that signals an under-verified plan rather than
a healthy one.
"""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPORT_ID_RE = re.compile(r"\*\*Report:\*\*\s*`?([A-Za-z0-9_.\-]+)`?")
GUIDE_HEADER_RE = re.compile(r"^###\s+([A-Za-z0-9_.\-]+)\s+[\u2014\u2013\-]\s*(.*)$", re.MULTILINE)
LOG_HEADER_RE = re.compile(
    r"^###\s+([A-Za-z0-9_.\-]+)\s+[\u2014\u2013\-]\s+([A-Za-z_]+)\s*$", re.MULTILINE
)
GATE_ID_RE = re.compile(r"-G\d+$|^G\d+$", re.IGNORECASE)
VERIFY_FIELD_RE = re.compile(r"^\*\*Verify output:\*\*", re.MULTILINE)
NEXT_FIELD_RE = re.compile(r"^\*\*[^*\n]+:\*\*", re.MULTILINE)
SECTION_END_RE = re.compile(r"^#{1,6}\s|^---\s*$", re.MULTILINE)
PLACEHOLDER_RE = re.compile(r"<[^>\n]*>")
# A mention that negates or defers the control ("negative control: n/a", "no negative
# control needed", "negative control: TBD", "the negative control step was not done")
# does not count as stating one. This is a wording heuristic, not proof the control ran.
_DEFERRAL = (
    r"n/?a|n\.\s?a\.?|none(?:\s+yet)?|tbd|todo|later|pending|skip(?:ped)?|deferred|missing"
    r"|not\s+(?:yet|needed|required|applicable|done|run|performed|written)"
    r"|to\s+be\s+(?:written|done|added|decided|determined|defined|confirmed|run)"
)
NEGATED_CONTROL_RE = re.compile(
    r"\b(?:no|without|skip(?:ped)?|omit(?:ted)?)\s+(?:the\s+)?negative\s+control"
    rf"|negative\s+controls?[^A-Za-z0-9\n]{{0,10}}(?:{_DEFERRAL})\b"
    rf"|negative\s+controls?\b[^.\n]{{0,40}}\b(?:was|is|were|are)\s+(?:{_DEFERRAL})\b",
    re.IGNORECASE,
)
# Text that only defers ("n/a", "TBD", "none yet") or is only punctuation ("-", "...") is
# not a stated control or pasted output.
DEFERRAL_ONLY_RE = re.compile(rf"^[^A-Za-z0-9]*(?:(?:{_DEFERRAL})[^A-Za-z0-9]*)?$", re.IGNORECASE)
CONTROL_MENTION_RE = re.compile(r"negative\s+controls?", re.IGNORECASE)
# A stated control says what is broken and what fails: at least a short sentence, with no
# deferral in it ("will add later", "TBA") and not a bare cross-reference ("see above").
MIN_CONTROL_WORDS = 4
DEFERRAL_PHRASE_RE = re.compile(
    rf"\b(?:{_DEFERRAL}|tba|will\s+(?:add|write|do|define|document)\w*|see\s+(?:above|below))\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[A-Za-z0-9_]+")
# Where a stated control ends: the next bold field, heading, or blank line.
CONTROL_END_RE = re.compile(r"\n\s*(?:[-*]\s+)?(?:\*\*|__)[^*_\n]+:|\n#|\n\s*\n")
# A task or gate ID contains a digit (P0-T1, T3, G2); headings like "### Notes — x" are not tasks.
TASK_ID_RE = re.compile(r"\d")
FENCE_LINE_RE = re.compile(r"^\s*(```|~~~)[\w-]*\s*$", re.MULTILINE)

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


def _states_negative_control(body: str) -> bool:
    """True when a mention of the negative control is followed by what it is: at least a
    short sentence (not a placeholder, punctuation, cross-reference, or deferral), and nothing
    negates it. This is a wording heuristic; the Auditor still checks the control ran."""
    if NEGATED_CONTROL_RE.search(body):
        return False
    for mention in CONTROL_MENTION_RE.finditer(body):
        rest = body[mention.end() :]
        end = CONTROL_END_RE.search(rest)
        text = PLACEHOLDER_RE.sub("", rest[: end.start()] if end else rest).strip()
        if len(WORD_RE.findall(text)) >= MIN_CONTROL_WORDS and not DEFERRAL_PHRASE_RE.search(text):
            return True
    return False


def _is_gate(task_id: str, title: str) -> bool:
    return bool(GATE_ID_RE.search(task_id)) or "gate" in title.lower()


def _done_without_evidence(log_text: str) -> list[str]:
    """IDs reported DONE whose **Verify output:** field is missing, empty, or only defers.

    The protocol records such a report as FAILED: evidence is pasted command output,
    not a claim that the command passed. Template placeholders, bare code fences, and a
    lone deferral such as "n/a" or "TBD" do not count as output.
    """
    missing = []
    for m in LOG_HEADER_RE.finditer(log_text):
        if m.group(2).upper() != "DONE":
            continue
        rest = log_text[m.end() :]
        end = SECTION_END_RE.search(rest)
        body = rest[: end.start()] if end else rest
        field = VERIFY_FIELD_RE.search(body)
        if not field:
            missing.append(m.group(1))
            continue
        after = body[field.end() :]
        nxt = NEXT_FIELD_RE.search(after)
        evidence = after[: nxt.start()] if nxt else after
        evidence = FENCE_LINE_RE.sub("", PLACEHOLDER_RE.sub("", evidence)).strip()
        if not evidence or DEFERRAL_ONLY_RE.match(evidence):
            missing.append(m.group(1))
    return missing


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
    # A missing document is an error, not a clean result: linting nothing proves nothing.
    missing_docs = [
        name
        for name in ("execution-guide.md", "compliance-log.md")
        if not (target / name).is_file()
    ]
    if missing_docs:
        print(
            f"error: {target} is missing {', '.join(missing_docs)} (run `auditkit init {target}`)."
        )
        return 2
    guide_text = _read(target / "execution-guide.md")
    log_text = _read(target / "compliance-log.md")

    problems = 0

    # 1. Every **Report:** ID in the guide should have an entry in the log.
    guide_ids = REPORT_ID_RE.findall(guide_text)
    log_ids = {m.group(1) for m in LOG_HEADER_RE.finditer(log_text)}

    missing = [i for i in guide_ids if i not in log_ids]
    if missing:
        problems += len(missing)
        print(
            f"[missing report] {len(missing)} task(s) in execution-guide.md have no entry in compliance-log.md:"
        )
        for i in missing:
            print(f"  - {i}")

    # 1a. The guide must define tasks, and every task or gate must name its Report ID;
    #     otherwise the missing-report check above has nothing to compare.
    task_sections = [
        (task_id, body)
        for task_id, _, body in _guide_sections(guide_text)
        if TASK_ID_RE.search(task_id)
    ]
    if not task_sections:
        problems += 1
        print("[empty guide] execution-guide.md defines no tasks or gates (### <ID> — <title>).")
    no_report_line = [task_id for task_id, body in task_sections if not REPORT_ID_RE.search(body)]
    if no_report_line:
        problems += len(no_report_line)
        print(
            f"[missing report line] {len(no_report_line)} task(s) in execution-guide.md have no **Report:** line:"
        )
        for i in no_report_line:
            print(f"  - {i}")

    # 1b. Every log entry should belong to a task or gate in the guide.
    known_ids = set(guide_ids) | {task_id for task_id, _, _ in _guide_sections(guide_text)}
    orphans = sorted(i for i in log_ids if i not in known_ids)
    if orphans:
        problems += len(orphans)
        print(
            f"[orphan report] {len(orphans)} entry(ies) in compliance-log.md have no task or gate in execution-guide.md:"
        )
        for i in orphans:
            print(f"  - {i}")

    # 2. Gates with no stated negative control. A gate still exactly as scaffolded (its title
    #    is a template placeholder) and not yet reported DONE is an unwritten gate, not a gap.
    log_status = {m.group(1): m.group(2).upper() for m in LOG_HEADER_RE.finditer(log_text)}
    gate_gaps = []
    for task_id, title, body in _guide_sections(guide_text):
        unwritten = PLACEHOLDER_RE.fullmatch(title.split(":", 1)[-1].strip()) is not None
        if unwritten and log_status.get(task_id) != "DONE":
            continue
        if _is_gate(task_id, title) and not _states_negative_control(body):
            gate_gaps.append(task_id)
    if gate_gaps:
        problems += len(gate_gaps)
        print(
            f"[gate w/o negative control] {len(gate_gaps)} gate(s) don't mention a negative control:"
        )
        for i in gate_gaps:
            print(f"  - {i}")

    # 3. DONE reports with no pasted verify output.
    unevidenced = _done_without_evidence(log_text)
    if unevidenced:
        problems += len(unevidenced)
        print(
            f"[done without evidence] {len(unevidenced)} report(s) marked DONE in "
            "compliance-log.md have no pasted Verify output (the protocol records these as FAILED):"
        )
        for i in unevidenced:
            print(f"  - {i}")

    # 4. Near-duplicate paragraphs in the log (append-only rot).
    dups = _duplicate_paragraphs(log_text)
    if dups:
        problems += len(dups)
        print(
            f"[duplicate content] {len(dups)} paragraph(s) repeated verbatim in compliance-log.md:"
        )
        for p, n in dups:
            preview = p[:100] + ("…" if len(p) > 100 else "")
            print(f"  - x{n}: {preview}")

    # 5. Annex count as a plan-health signal.
    annex_dir = target / "annexes"
    if annex_dir.exists():
        annex_files = [f for f in annex_dir.iterdir() if f.is_file() and f.name != ".gitkeep"]
        phase_pattern = re.compile(r"^(?:P(\d+)|phase[-_]?(\d+))", re.IGNORECASE)
        phase_counts: defaultdict[str, int] = defaultdict(int)
        for f in annex_files:
            m = phase_pattern.search(f.stem)
            if m:
                phase_num = m.group(1) or m.group(2)
                phase_counts[f"Phase {phase_num}"] += 1
            else:
                phase_counts["General"] += 1

        phase_exceeded = {p: c for p, c in phase_counts.items() if c > annex_threshold}
        if len(annex_files) > annex_threshold or phase_exceeded:
            problems += 1
            print(
                f"[annex count] {len(annex_files)} annexes exceeds the threshold of "
                f"{annex_threshold}. This usually means a phase's plan was under-verified "
                f"before work started, not that it hit unusual surprises. Worth naming as a "
                f"planning finding, not only fixing task by task."
            )
            if len(phase_counts) > 1 or (len(phase_counts) == 1 and "General" not in phase_counts):
                for p_name, count in sorted(phase_counts.items()):
                    print(f"  - {p_name}: {count} annex(es)")

    if problems == 0:
        print("clean — no cross-document gaps found.")
        return 0

    print(f"\n{problems} issue(s) found.")
    return 1


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="auditkit lint")
    parser.add_argument("target_dir")
    parser.add_argument("--annex-threshold", type=int, default=DEFAULT_ANNEX_THRESHOLD)
    args = parser.parse_args(argv)
    return run(args.target_dir, args.annex_threshold)


if __name__ == "__main__":
    sys.exit(main())
