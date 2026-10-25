"""Negative control: allow any non-final stage transition."""

from pathlib import Path

PATH = Path("/tmp/aep-lab/pilot2/AE-neutral-2/crm.py")
OLD = '''        if stage != "lost":
            current_index = STAGE_ORDER.index(opp["stage"])
            if (
                current_index + 1 >= len(STAGE_ORDER)
                or STAGE_ORDER[current_index + 1] != stage
            ):
                raise ValueError("stage is not the immediate next stage")
'''
NEW = '''        if False:
            raise ValueError("stage is not the immediate next stage")
'''

text = PATH.read_text()
if text.count(OLD) != 1:
    raise SystemExit("anchor not found in crm.py")
PATH.write_text(text.replace(OLD, NEW))
