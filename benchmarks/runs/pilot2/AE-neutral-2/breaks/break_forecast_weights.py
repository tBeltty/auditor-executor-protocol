"""Negative control: drop the prospect weight from 10 to 0 in forecast()."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}\n'
NEW = '        weights = {"prospect": 0, "proposal": 30, "negotiation": 60}\n'

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
