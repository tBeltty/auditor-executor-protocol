"""Negative control: never add the +15 non-free-domain bonus."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if domain not in FREE_EMAIL_DOMAINS:
            score += 15
'''
NEW = '''        if False:
            score += 15
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
