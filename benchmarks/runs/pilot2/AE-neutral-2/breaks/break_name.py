"""Negative control: stop rejecting blank / non-string names."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
'''
NEW = '''        if False:
            raise ValueError("name must be a non-empty string")
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
