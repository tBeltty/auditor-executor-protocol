"""Stateful differential scenarios: drive valid workflows (which the random
fuzzer rarely reached) plus periodic invalid variants, comparing delivery vs
the independent reference after every call.
"""
import copy
import random
import sys

sys.path.insert(0, "/tmp/aep-lab/pilot3/deepseek-rerun/AE-neutral-2")
sys.path.insert(0, "/tmp/aep-lab/pilot3/deepseek-rerun/audprobe")

from crm import CRM
from ref import RefCRM
from fuzz import call, snap

EMAIL_POOL = [
    "a@corp.com", "b@corp.com", "c@corp.com", "d@gmail.com", "e@yahoo.com",
    "f@outlook.com", "g@sub.example.co", "h@x.io",
]
AMOUNTS = [1, 7, 100, 101, 999, 5000, 49999, 50000, 50001, 60000, 123457]


def reps(rng):
    out = []
    for i in range(rng.randint(1, 3)):
        out.append({"id": "r%d" % (i + 1), "role": "rep", "capacity": rng.randint(0, 2)})
    out.append({"id": "m1", "role": "manager", "capacity": rng.choice([0, 1, 3])})
    return out


def pick(rng, seq):
    seq = list(seq)
    return rng.choice(seq) if seq else None


def run(seed):
    rng = random.Random(10_000 + seed)
    cfg = reps(rng)
    a, b = CRM(copy.deepcopy(cfg)), RefCRM(copy.deepcopy(cfg))
    users = cfg
    rep_ids = [u["id"] for u in users if u["role"] == "rep"]
    mgr_ids = [u["id"] for u in users if u["role"] == "manager"]
    email_n = 0

    for step in range(70):
        leads = b.leads
        opps = b.opps
        choice = rng.choices(
            ["add", "qualify", "convert", "advance", "discount", "transfer", "forecast"],
            weights=[3, 3, 3, 4, 2, 2, 1])[0]
        fn, args = None, ()

        if choice == "add" or (choice != "add" and rng.random() < 0.1):
            if rng.random() < 0.75 or email_n >= len(EMAIL_POOL):
                email = "u%d@%s" % (email_n, rng.choice(["corp.com", "gmail.com", "sub.example.co"]))
                email_n += 1
            else:
                email = rng.choice(EMAIL_POOL)
            if rng.random() < 0.25:
                email = "  %s  " % email.upper()
            name = rng.choice(["Alice", "Bob", "  Carol  ", "", "   "])
            source = rng.choice(["web", "referral", "event", "bogus"])
            actor = rng.choice(rep_ids + mgr_ids)
            fn, args = "add_lead", (email, name, source, actor)

        elif choice == "qualify":
            cand = [l for l in leads.values() if l["status"] == "new"]
            lead = pick(rng, [l["id"] for l in cand])
            if lead is None:
                continue
            owner = leads[lead]["owner"]
            actor = owner if owner else rng.choice(mgr_ids)
            fn, args = "qualify", (lead, actor)

        elif choice == "convert":
            cand = [l for l in leads.values() if l["status"] == "qualified" and l["owner"]]
            lead = pick(rng, [l["id"] for l in cand])
            if lead is None:
                continue
            fn, args = "convert", (lead, rng.choice(AMOUNTS), leads[lead]["owner"])

        elif choice == "advance":
            cand = [o for o in opps.values() if o["stage"] not in ("won", "lost")]
            oid = pick(rng, [o["id"] for o in cand])
            if oid is None:
                continue
            cur = opps[oid]["stage"]
            order = ["prospect", "proposal", "negotiation", "won"]
            nxt = order[order.index(cur) + 1]
            stage = rng.choice([nxt, nxt, "lost"])
            actor = opps[oid]["owner"]
            # Over 50k, moving to negotiation needs a manager.
            if stage == "negotiation" and opps[oid]["amount"] > 50000:
                actor = rng.choice(mgr_ids)
            if rng.random() < 0.1:
                actor = rng.choice(rep_ids + mgr_ids + ["ghost"])
            fn, args = "advance", (oid, stage, actor)

        elif choice == "discount":
            cand = [o for o in opps.values() if o["stage"] not in ("won", "lost")]
            oid = pick(rng, [o["id"] for o in cand])
            if oid is None:
                continue
            pct = rng.choice([1, 5, 10, 10, 11, 20, 30])
            actor = opps[oid]["owner"]
            if pct > 10:
                actor = rng.choice(mgr_ids)
            fn, args = "discount", (oid, pct, actor)

        elif choice == "transfer":
            cand = [o for o in opps.values() if o["stage"] not in ("won", "lost")]
            oid = pick(rng, [o["id"] for o in cand])
            if oid is None:
                continue
            new_owner = rng.choice(rep_ids)
            fn, args = "transfer", (oid, new_owner, rng.choice(mgr_ids))

        else:
            fn, args = "forecast", ()

        ra = call(lambda: getattr(a, fn)(*args))
        rb = call(lambda: getattr(b, fn)(*args))
        ka = ra[0] if ra[0] == "ok" else ra[1]
        kb = rb[0] if rb[0] == "ok" else rb[1]
        if ka != kb:
            return "seed=%s step=%s %s%r\n  delivery=%r\n  reference=%r\n  exception class differs" % (seed, step, fn, args, ra, rb)
        if ra[0] == "ok" and ra[1] != rb[1]:
            return "seed=%s step=%s %s%r\n  delivery=%r\n  reference=%r\n  return differs" % (seed, step, fn, args, ra, rb)
        sa, sb = snap(a), snap(b)
        if sa != sb:
            parts = ["seed=%s step=%s %s%r" % (seed, step, fn, args)]
            for key in ("leads", "opps", "log", "queue"):
                if sa[key] != sb[key]:
                    parts.append("  %s:\n    delivery=%r\n    reference=%r" % (key, sa[key], sb[key]))
            return "\n".join(parts)
    return None


findings = []
stats = {"won": 0, "lost": 0, "transfer": 0, "assign": 0, "discount_ok": 0}
for seed in range(300):
    out = run(seed)
    if out:
        findings.append(out)
print("divergences:", len(findings))
for f in findings[:10]:
    print("=" * 70)
    print(f)
