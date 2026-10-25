"""Negative control: forecast weights the pre-discount amount."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '            weighted += opp["amount"] * weights[opp["stage"]] // 100\n'
NEW = '            weighted += opp["original_amount"] * weights[opp["stage"]] // 100\n'

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
