"""Negative control: break the smallest-id tie-break in owner selection."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = "        for user_id in sorted(self._users):\n"
NEW = "        for user_id in sorted(self._users, reverse=True):\n"

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
