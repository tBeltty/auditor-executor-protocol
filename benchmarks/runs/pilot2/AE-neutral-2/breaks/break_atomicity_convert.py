"""Negative control: convert mutates the lead before permission can fail."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive integer")
        if lead["owner"] != actor and not self._is_manager(actor):
'''
NEW = '''        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive integer")
        lead["status"] = "converted"
        if lead["owner"] != actor and not self._is_manager(actor):
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
