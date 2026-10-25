"""Negative control: accept actors that are not known users."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))
'''
NEW = '''        return None
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
