"""Negative control: mutate the amount before discount validation can fail."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
'''
NEW = '''        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp["amount"] = -1
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
