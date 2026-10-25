"""Negative control: let managers receive work from _pick_owner."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''            if user["role"] != "rep":
                continue
'''
NEW = '''            if False:
                continue
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
