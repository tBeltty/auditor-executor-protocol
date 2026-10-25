"""Negative control: allow transfer to a user who is not a rep."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a rep")
'''
NEW = '''        if target is None:
            raise ValueError("new owner must be a rep")
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
