"""Differential fuzzer: delivery crm.py vs independent spec reference.

Compares, after every call: exception class, return value, and full state
(leads, opps, log, waiting queue). Emails are drawn from a normal corpus so a
divergence points at business logic, not the disputed dot rule (probed
separately).
"""
import copy
import random
import sys
import traceback

sys.path.insert(0, "/tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-2")
sys.path.insert(0, "/tmp/aep-lab/pilot3/deepseek-rerun/audprobe")

from crm import CRM  # delivery
from ref import RefCRM  # independent oracle


def snap(obj):
    q = getattr(obj, "waiting", None)
    if q is None:
        q = getattr(obj, "queue", [])
    return copy.deepcopy({
        "leads": obj.leads,
        "opps": obj.opps,
        "log": obj.log,
        "queue": list(q),
    })


def call(fn):
    try:
        return ("ok", fn())
    except Exception as exc:  # noqa: BLE001
        return ("exc", type(exc).__name__, str(exc))


EMAILS = [
    "a@corp.com", "b@corp.com", "c@gmail.com", "d@gmail.com",
    "  A@Corp.COM ", "e@sub.example.co", "f@b.co", "g@yahoo.com",
]


def gen_reps(rng):
    reps = []
    for i in range(rng.randint(0, 3)):
        reps.append({"id": "r%d" % (i + 1), "role": "rep", "capacity": rng.randint(0, 3)})
    if rng.random() < 0.85:
        reps.append({"id": "m1", "role": "manager", "capacity": rng.choice([0, 1, 5])})
    if not reps:
        reps.append({"id": "r1", "role": "rep", "capacity": 1})
    return reps


AMOUNTS = [1, 10, 99, 100, 101, 999, 49999, 50000, 50001, 60000, 100000,
           0, -1, True, False, 1.5, "5", None]
PCTS = [1, 5, 10, 11, 20, 30, 31, 0, -1, True, 10.5, "5", None]
STAGES = ["prospect", "proposal", "negotiation", "won", "lost", "bogus", "", None, "PROSPECT"]


def run(seed):
    rng = random.Random(seed)
    reps = gen_reps(rng)
    a, b = CRM(copy.deepcopy(reps)), RefCRM(copy.deepcopy(reps))
    actor_pool = [r["id"] for r in reps] + ["ghost", None, 3]
    lead_ids = ["L%d" % i for i in range(1, 5)] + ["L404", None]
    opp_ids = ["O%d" % i for i in range(1, 5)] + ["O404", None]

    for step in range(80):
        op = rng.choice(["add", "add", "qualify", "convert", "advance",
                         "discount", "transfer", "forecast"])
        actor = rng.choice(actor_pool)
        if op == "add":
            args = (rng.choice(EMAILS), rng.choice(["Alice", " Bob ", "", "  ", None, 7]),
                    rng.choice(["web", "referral", "event", "email", "WEB", None]), actor)
            fn = "add_lead"
        elif op == "qualify":
            args = (rng.choice(lead_ids), actor)
            fn = "qualify"
        elif op == "convert":
            args = (rng.choice(lead_ids), rng.choice(AMOUNTS), actor)
            fn = "convert"
        elif op == "advance":
            args = (rng.choice(opp_ids), rng.choice(STAGES), actor)
            fn = "advance"
        elif op == "discount":
            args = (rng.choice(opp_ids), rng.choice(PCTS), actor)
            fn = "discount"
        elif op == "transfer":
            args = (rng.choice(opp_ids), rng.choice(actor_pool), actor)
            fn = "transfer"
        else:
            args = ()
            fn = "forecast"

        ra = call(lambda: getattr(a, fn)(*args))
        rb = call(lambda: getattr(b, fn)(*args))

        ka = ra[0] if ra[0] == "ok" else ra[1]
        kb = rb[0] if rb[0] == "ok" else rb[1]
        if ka != kb:
            return (seed, step, fn, args, ra, rb, "exception/return class differs")
        if ra[0] == "ok" and ra[1] != rb[1]:
            return (seed, step, fn, args, ra, rb, "return value differs")
        if snap(a) != snap(b):
            diffs = []
            sa, sb = snap(a), snap(b)
            for key in ("leads", "opps", "log", "queue"):
                if sa[key] != sb[key]:
                    diffs.append("  %s:\n    delivery=%r\n    reference=%r" % (key, sa[key], sb[key]))
            return (seed, step, fn, args, ra, rb, "state differs\n" + "\n".join(diffs))
    return None


bad = []
for seed in range(400):
    try:
        out = run(seed)
    except Exception:  # noqa: BLE001 - a crash in the delivery is itself a finding
        print("CRASH seed", seed)
        traceback.print_exc()
        bad.append((seed, "crash"))
        continue
    if out:
        bad.append(out)

print("diverging seeds:", len(bad))
for item in bad[:12]:
    print("=" * 70)
    if isinstance(item, tuple) and len(item) == 7:
        seed, step, fn, args, ra, rb, why = item
        print("seed=%s step=%s %s%r" % (seed, step, fn, args))
        print("delivery:", ra)
        print("reference:", rb)
        print(why)
    else:
        print(item)
