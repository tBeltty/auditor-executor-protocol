"""Negative control: allow a rep to transfer an opportunity."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer an opportunity")
'''
NEW = '''        if False:
            raise PermissionError("only a manager may transfer an opportunity")
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
