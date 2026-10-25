"""Negative control: consume a lead id before add_lead has validated anything."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        self._check_actor(actor)
        normalized = _normalize_email(email)
'''
NEW = '''        self._check_actor(actor)
        self._lead_count += 1
        normalized = _normalize_email(email)
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
