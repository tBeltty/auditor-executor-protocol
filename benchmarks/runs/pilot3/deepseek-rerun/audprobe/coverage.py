"""Coverage counter for the fuzz run + targeted edge probes."""
import copy
import random
import sys

sys.path.insert(0, "/tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-2")
sys.path.insert(0, "/tmp/aep-lab/pilot3/deepseek-rerun/audprobe")

from crm import CRM
from fuzz import AMOUNTS, PCTS, STAGES, EMAILS, gen_reps

counts = {"ok": {}, "exc": {}}
assign_events = 0
transfers_ok = 0
wins = 0

for seed in range(400):
    rng = random.Random(seed)
    reps = gen_reps(rng)
    crm = CRM(copy.deepcopy(reps))
    actors = [r["id"] for r in reps] + ["ghost", None, 3]
    lead_ids = ["L%d" % i for i in range(1, 5)] + ["L404", None]
    opp_ids = ["O%d" % i for i in range(1, 5)] + ["O404", None]
    for step in range(80):
        op = rng.choice(["add", "add", "qualify", "convert", "advance", "discount", "transfer", "forecast"])
        actor = rng.choice(actors)
        if op == "add":
            args = (rng.choice(EMAILS), rng.choice(["Alice", " Bob ", "", "  ", None, 7]),
                    rng.choice(["web", "referral", "event", "email", "WEB", None]), actor)
            fn = "add_lead"
        elif op == "qualify":
            fn, args = "qualify", (rng.choice(lead_ids), actor)
        elif op == "convert":
            fn, args = "convert", (rng.choice(lead_ids), rng.choice(AMOUNTS), actor)
        elif op == "advance":
            fn, args = "advance", (rng.choice(opp_ids), rng.choice(STAGES), actor)
        elif op == "discount":
            fn, args = "discount", (rng.choice(opp_ids), rng.choice(PCTS), actor)
        elif op == "transfer":
            fn, args = "transfer", (rng.choice(opp_ids), rng.choice(actors), actor)
        else:
            fn, args = "forecast", ()
        before_log = len(crm.log)
        try:
            getattr(crm, fn)(*args)
            counts["ok"][fn] = counts["ok"].get(fn, 0) + 1
        except Exception as exc:  # noqa: BLE001
            key = fn + ":" + type(exc).__name__
            counts["exc"][key] = counts["exc"].get(key, 0) + 1
        new = crm.log[before_log:]
        assign_events += sum(1 for e in new if e[0] == "assign")
        if fn == "transfer" and new and new[0][0] == "transfer":
            transfers_ok += 1
        if fn == "advance" and new and new[0][0] == "advance" and crm.opps.get(args[0], {}).get("stage") == "won":
            wins += 1

print("successes by method:", counts["ok"])
print("exceptions by method/class:", counts["exc"])
print("assign log events:", assign_events, "| successful transfers:", transfers_ok, "| wins:", wins)
