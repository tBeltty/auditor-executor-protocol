"""Negative control: allow a transfer to the current owner."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if new_owner == opp["owner"]:
            raise ValueError("new owner is already the owner")
'''
NEW = '''        if False:
            raise ValueError("new owner is already the owner")
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
