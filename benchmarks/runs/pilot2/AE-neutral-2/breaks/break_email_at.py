"""Negative control: drop the exactly-one-'@' email check."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''    if normalized.count("@") != 1:
        raise ValueError("email must contain exactly one '@'")
'''
NEW = '''    if False:
        raise ValueError("email must contain exactly one '@'")
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
