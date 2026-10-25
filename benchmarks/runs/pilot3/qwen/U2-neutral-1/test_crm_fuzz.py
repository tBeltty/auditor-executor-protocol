"""Seeded randomized invariant testing for crm.CRM.

Exercises only the public API with a fixed seed (deterministic, stdlib only)
and checks the spec's general rules after every call:

- a failed call changes nothing and appends nothing to the log;
- only reps own anything, and no rep's load ever exceeds capacity;
- leads without an owner are exactly the waiting queue, in FIFO order;
- every opp references an existing converted lead and is owned by a rep;
- forecast() never logs.
"""

import copy
import random
import unittest

from crm import CRM

STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
KNOWN_OPS = ("add_lead", "qualify", "convert", "advance", "discount",
             "transfer", "assign")


class TestFuzzInvariants(unittest.TestCase):
    def build_crm(self, rng):
        specs = [("r%d" % i, "rep", rng.randint(0, 2)) for i in range(1, rng.randint(1, 4))]
        specs.append(("m1", "manager", rng.choice([0, 5])))
        rng.shuffle(specs)
        return CRM([{"id": i, "role": r, "capacity": c} for (i, r, c) in specs])

    def snapshot(self, c):
        return (copy.deepcopy(dict(c.leads)), copy.deepcopy(dict(c.opps)),
                list(c.log), list(c._queue))

    def check_invariants(self, c):
        leads, opps, log = c.leads, c.opps, c.log
        for lid, lead in leads.items():
            self.assertEqual(lid, lead["id"])
            self.assertIn(lead["status"], ("new", "qualified", "converted"))
            self.assertEqual(lead["email"], lead["email"].strip().lower())
            self.assertTrue(lead["owner"] is None
                            or c._users[lead["owner"]]["role"] == "rep")
        for oid, opp in opps.items():
            self.assertEqual(oid, opp["id"])
            self.assertIn(opp["stage"], STAGES)
            self.assertGreater(opp["amount"], 0)
            self.assertLessEqual(opp["amount"], opp["original_amount"])
            self.assertEqual(leads[opp["lead_id"]]["status"], "converted")
            self.assertEqual(c._users[opp["owner"]]["role"], "rep")
        # queue == leads with owner None, in FIFO creation order
        unowned = [lid for lid, lead in leads.items() if lead["owner"] is None]
        self.assertEqual(list(c._queue), unowned)
        # capacity is never exceeded
        for uid, user in c._users.items():
            if user["role"] == "rep":
                self.assertLessEqual(c._load(uid), user["capacity"])
        # log shape
        for entry in log:
            self.assertIsInstance(entry, tuple)
            self.assertEqual(len(entry), 3)
            self.assertIn(entry[0], KNOWN_OPS)
            self.assertTrue(entry[2] in c._users or entry[2] == "system")

    def test_random_sequences(self):
        rng = random.Random(20261025)
        for _trial in range(12):
            c = self.build_crm(rng)
            actors = list(c._users) + ["ghost"]
            emails = iter("l%d@corp.com" % i for i in range(2000))
            lead_ids, opp_ids = [], []
            for _step in range(80):
                before = self.snapshot(c)
                op = rng.choice(["add", "add", "qualify", "convert",
                                 "advance", "discount", "transfer"])
                actor = rng.choice(actors)
                try:
                    if op == "add":
                        email = "dup@corp.com" if rng.random() < 0.12 else next(emails)
                        lead_ids.append(c.add_lead(
                            email, "N", rng.choice(["web", "referral", "event", "phone"]),
                            actor))
                    elif op == "qualify" and lead_ids:
                        c.qualify(rng.choice(lead_ids), actor)
                    elif op == "convert" and lead_ids:
                        amount = rng.choice([1, 50001, rng.randint(1, 99999), 0, "x"])
                        opp_ids.append(c.convert(rng.choice(lead_ids), amount, actor))
                    elif op == "advance" and opp_ids:
                        c.advance(rng.choice(opp_ids), rng.choice(STAGES + ("gone",)), actor)
                    elif op == "discount" and opp_ids:
                        c.discount(rng.choice(opp_ids), rng.randint(-1, 35), actor)
                    elif op == "transfer" and opp_ids:
                        c.transfer(rng.choice(opp_ids), rng.choice(actors), actor)
                    else:
                        continue  # nothing applicable attempted this step
                except Exception:
                    self.assertEqual(self.snapshot(c), before,
                                     "failed %s mutated state" % op)
                self.check_invariants(c)
            # forecast must never log or mutate
            before = self.snapshot(c)
            f = c.forecast()
            self.assertEqual(self.snapshot(c), before)
            self.assertEqual(set(f), {"open", "weighted", "won"})


if __name__ == "__main__":
    unittest.main()
