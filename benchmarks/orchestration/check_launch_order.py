#!/usr/bin/env python3
"""Check that the shuffle in the Pilot 3 drivers reproduces the launch order recorded in the driver logs.

The drivers shuffle the 24 cells of each model block with random.Random(<block key>).shuffle(cells), where the block key is
the model name ("qwen", "glm") or "deepseek-rerun". Prints True for each block whose recorded order of Executor launches
equals the order that the shuffle produces."""
import random
import re
from pathlib import Path

LOGS = Path(__file__).resolve().parent.parent / "results"
ARMS, PRES, REPS = ["U", "U2", "N", "AE"], ["neutral", "pressure"], [1, 2, 3]


def predicted(key):
    cells = [(a, p, r) for a in ARMS for p in PRES for r in REPS]
    random.Random(key).shuffle(cells)
    return [f"{a}-{p}-{r}" for a, p, r in cells]


def recorded(log, key):
    out = []
    for line in open(LOGS / log):
        m = re.match(r"\S+ launched (\S+) exec (\S+) ", line)
        if m and m.group(1) == key:
            out.append(m.group(2))
    return out


for key, log in [("qwen", "pilot3_driver_main.log"), ("glm", "pilot3_driver_main.log"), ("deepseek-rerun", "pilot3_driver_deepseek_rerun.log")]:
    rec = recorded(log, key)
    print(key, len(rec), "launches; recorded order equals shuffled order:", rec == predicted(key))
