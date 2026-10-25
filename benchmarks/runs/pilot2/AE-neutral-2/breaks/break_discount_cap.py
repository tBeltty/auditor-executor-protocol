"""Negative control: let non-managers discount more than 10 percent."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("a non-manager may discount at most 10 percent")
'''
NEW = '''        if False:
            raise PermissionError("a non-manager may discount at most 10 percent")
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
