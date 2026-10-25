"""Negative control: accept discount percentages outside 1..30."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
'''
NEW = '''        if not isinstance(pct, int) or isinstance(pct, bool):
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
