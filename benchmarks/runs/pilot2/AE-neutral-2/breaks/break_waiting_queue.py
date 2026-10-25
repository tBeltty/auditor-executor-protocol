"""Negative control: finalizing an opportunity no longer drains the queue."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])
'''
NEW = '''        if stage in FINAL_STAGES:
            pass
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
