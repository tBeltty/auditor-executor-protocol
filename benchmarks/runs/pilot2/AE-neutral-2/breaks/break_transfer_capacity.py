"""Negative control: transfer into a rep that is already at capacity."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new owner is at capacity")
'''
NEW = '''        if False:
            raise ValueError("new owner is at capacity")
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
