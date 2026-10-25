"""Randomized (fixed-seed) checks of the invariants the spec states generally:
only the documented exceptions escape, failed calls are atomic, successful calls
append exactly the documented log entries, and the waiting queue stays
consistent with rep capacity.

The walk is deliberately guided: it mostly proposes legal operations, so that
deep pipeline states (negotiation, wins, transfers, auto-assignment) are reached
rather than only the first validation error."""

import copy
import random
import unittest

from crm import CRM, DuplicateLeadError

TEAMS = [
    [{"id": "r1", "role": "rep", "capacity": 2}, {"id": "m1", "role": "manager", "capacity": 3}],
    [{"id": "r1", "role": "rep", "capacity": 3}, {"id": "r2", "role": "rep", "capacity": 2}],
    [{"id": "a1", "role": "rep", "capacity": 4}, {"id": "b2", "role": "rep", "capacity": 1},
     {"id": "m1", "role": "manager", "capacity": 0}],
    [{"id": "r1", "role": "rep", "capacity": 0}, {"id": "r2", "role": "rep", "capacity": 3},
     {"id": "m1", "role": "manager", "capacity": 2}],
    # A roomy team: opportunities accumulate, so transfers and hand-backs happen.
    [{"id": "r1", "role": "rep", "capacity": 5}, {"id": "r2", "role": "rep", "capacity": 5},
     {"id": "r3", "role": "rep", "capacity": 4}, {"id": "m1", "role": "manager", "capacity": 9}],
]

STAGES = ["prospect", "proposal", "negotiation", "won", "lost"]
NEXT = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
DOMAINS = ["acme.com", "gmail.com", "big.co.uk", "outlook.com"]


def snapshot(crm):
    return copy.deepcopy((crm.leads, crm.opps, crm.log))


class FuzzTest(unittest.TestCase):
    def run_one(self, seed, team, steps=400):
        rng = random.Random(seed)
        crm = CRM(copy.deepcopy(team))
        user_ids = [u["id"] for u in team]
        rep_ids = [u["id"] for u in team if u["role"] == "rep"]
        manager_ids = [u for u in user_ids if u not in rep_ids]
        counter = [0]

        def new_email():
            counter[0] += 1
            return "lead%d@%s" % (counter[0], rng.choice(DOMAINS))

        def actor_for(entity):
            """Mostly the owner or a manager, sometimes somebody else."""
            roll = rng.random()
            if roll < 0.45 and manager_ids:
                return rng.choice(manager_ids)
            if roll < 0.85 and entity is not None:
                return entity.get("owner") or rng.choice(user_ids)
            return rng.choice(user_ids + ["ghost"])

        for _ in range(steps):
            before = snapshot(crm)
            kind = rng.choice(
                ["add_lead", "qualify", "convert", "advance", "advance", "advance",
                 "discount", "transfer", "forecast"]
            )
            lead_ids = sorted(crm.leads)
            opp_ids = sorted(crm.opps)
            lead = crm.leads[rng.choice(lead_ids)] if lead_ids and rng.random() < 0.8 else None
            opp = crm.opps[rng.choice(opp_ids)] if opp_ids and rng.random() < 0.8 else None
            actor = None

            try:
                if kind == "add_lead":
                    email = new_email() if rng.random() < 0.9 else rng.choice(
                        ["bad", "@x.com", "a@b.", "a@.com", "a@b@c.com", None, 7])
                    name = rng.choice(["Ann", "  Bob  ", "Cy"]) if rng.random() < 0.95 else ""
                    source = rng.choice(["web", "referral", "event"]) if rng.random() < 0.95 else "phone"
                    actor = actor_for(lead)
                    crm.add_lead(email, name, source, actor)
                elif kind == "qualify":
                    actor = actor_for(lead or {"owner": None})
                    crm.qualify(lead["id"] if lead else "L?", actor)
                elif kind == "convert":
                    amount = rng.choice([1, 500, 42000, 60000, 90000]) if rng.random() < 0.9 else 0
                    actor = actor_for(lead)
                    crm.convert(lead["id"] if lead else "L?", amount, actor)
                elif kind == "advance":
                    if opp and rng.random() < 0.7:
                        stage = NEXT.get(opp["stage"], "lost")
                        if rng.random() < 0.25:
                            stage = "lost"
                    else:
                        stage = rng.choice(STAGES + ["halt"])
                    actor = actor_for(opp)
                    crm.advance(opp["id"] if opp else "O?", stage, actor)
                elif kind == "discount":
                    pct = rng.choice([1, 5, 10, 11, 20, 30]) if rng.random() < 0.9 else rng.choice([0, 31, "5", True])
                    actor = actor_for(opp)
                    crm.discount(opp["id"] if opp else "O?", pct, actor)
                elif kind == "transfer":
                    if opp and rng.random() < 0.7:
                        open_reps = [u["id"] for u in team
                                     if u["role"] == "rep" and u["id"] != opp["owner"]]
                        target = rng.choice(open_reps) if open_reps else "r?"
                    else:
                        target = rng.choice(rep_ids + ["m1", "ghost"])
                    actor = actor_for(opp)
                    crm.transfer(opp["id"] if opp else "O?", target, actor)
                else:
                    forecast = crm.forecast()
                    self.assertEqual(sorted(forecast), ["open", "weighted", "won"])
            except (ValueError, PermissionError, DuplicateLeadError):
                self.assertEqual(snapshot(crm), before, "%s: a failed call changed state" % kind)
                continue

            after = snapshot(crm)
            new_entries = after[2][len(before[2]):]

            if kind == "forecast":
                self.assertEqual(new_entries, [], "forecast must not append to the log")
            else:
                self.assertTrue(new_entries, "%s succeeded but logged nothing" % kind)
                self.assertEqual(new_entries[0][0], kind)
                self.assertEqual(new_entries[0][2], actor, "wrong actor recorded")
                store = after[0] if kind in ("add_lead", "qualify") else after[1]
                self.assertIn(new_entries[0][1], store, "%s logged the wrong entity" % kind)
                for entry in new_entries[1:]:
                    self.assertEqual(entry[0], "assign", "only auto-assignment may follow")
                    self.assertEqual(len(entry), 3)
                    self.assertEqual(entry[2], "system")
                    self.assertIn(entry[1], after[0])
                    self.assertIsNotNone(after[0][entry[1]]["owner"])
                if kind not in ("advance", "transfer"):
                    self.assertEqual(len(new_entries), 1, "unexpected extra log entries")
                elif len(new_entries) > 1:
                    self.assertEqual(kind, "advance")
                    self.assertIn(after[1][new_entries[0][1]]["stage"], ("won", "lost"),
                                  "auto-assignment only happens when a deal closes")

            # Structural invariants that must hold after every successful call.
            for lead_id, entry in after[0].items():
                self.assertEqual(lead_id, entry["id"])
                self.assertIn(entry["status"], ("new", "qualified", "converted"))
                self.assertTrue(entry["owner"] is None or entry["owner"] in rep_ids,
                                "only reps may own leads")
                self.assertEqual(sorted(entry),
                                 ["email", "id", "name", "owner", "score", "source", "status"])
            for opp_id, entry in after[1].items():
                self.assertEqual(opp_id, entry["id"])
                self.assertIn(entry["stage"], STAGES)
                self.assertIn(entry["owner"], rep_ids, "only reps may own opportunities")
                self.assertLessEqual(entry["amount"], entry["original_amount"])
                self.assertGreaterEqual(entry["amount"] * 100, entry["original_amount"] * 70)
                self.assertEqual(sorted(entry),
                                 ["amount", "id", "lead_id", "original_amount", "owner", "stage"])

            # A waiting lead can only exist while every rep is saturated.
            if getattr(crm, "_waiting", []):
                for user in team:
                    if user["role"] != "rep":
                        continue
                    load = sum(1 for entry in after[0].values()
                               if entry["owner"] == user["id"] and entry["status"] != "converted")
                    load += sum(1 for entry in after[1].values()
                                if entry["owner"] == user["id"] and entry["stage"] not in ("won", "lost"))
                    self.assertGreaterEqual(load, user["capacity"],
                                            "work queued while a rep had room")

    def test_every_team(self):
        for index, team in enumerate(TEAMS):
            for seed in (1, 2, 3):
                self.run_one(1000 * (index + 1) + seed, team)

    def test_more_walks_on_the_widest_team(self):
        for seed in range(20, 32):
            self.run_one(seed, TEAMS[-1])


if __name__ == "__main__":
    unittest.main()
