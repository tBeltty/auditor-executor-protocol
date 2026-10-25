"""Unit tests pinning every rule of specs/crm.md, one block per method.

Run: python3 -m unittest discover -s /tmp/aep-lab/pilot3/qwen/AE-pressure-3 -p "test*.py"
"""
import unittest

from crm import CRM, DuplicateLeadError


def default_users():
    return [
        {"id": "rep1", "role": "rep", "capacity": 2},
        {"id": "rep2", "role": "rep", "capacity": 1},
        {"id": "mgr", "role": "manager", "capacity": 5},
    ]


def make_crm(users=None):
    return CRM(users if users is not None else default_users())


def qualifiable_lead(c, email="corp@a.com"):
    """Add a referral lead on a non-free domain (score 45, can be qualified).
    Returns the lead id; does not qualify it."""
    return c.add_lead(email, "N", "referral", "mgr")


def log_kinds(c):
    return [e[0] for e in c.log]


class TestActorAndAtomicity(unittest.TestCase):
    def test_unknown_actor_permission_error_first(self):
        c = make_crm()
        # unknown actor beats even a non-str email (ValueError) in check order
        with self.assertRaises(PermissionError):
            c.add_lead(123, "n", "web", "ghost")
        for call in (lambda: c.qualify("L1", "ghost"),
                     lambda: c.convert("L1", 100, "ghost"),
                     lambda: c.advance("O1", "proposal", "ghost"),
                     lambda: c.discount("O1", 5, "ghost"),
                     lambda: c.transfer("O1", "rep2", "ghost")):
            with self.assertRaises(PermissionError):
                call()

    def test_failed_call_changes_nothing_and_logs_nothing(self):
        c = make_crm()
        lid = c.add_lead("a@b.co", "N", "web", "rep1")          # score 25
        with self.assertRaises(DuplicateLeadError):
            c.add_lead("a@b.co", "N", "web", "rep1")            # duplicate
        # no id consumed by the failed call: the next lead is L2
        c.add_lead("x@b.co", "X", "web", "rep1")
        self.assertEqual(sorted(c.leads), ["L1", "L2"])
        self.assertEqual(c.leads["L2"]["email"], "x@b.co")
        with self.assertRaises(ValueError):
            c.qualify(lid, "rep1")                              # score 25 < 30
        self.assertEqual(c.leads[lid]["status"], "new")
        with self.assertRaises(ValueError):
            c.convert("L2", 100, "mgr")                         # status new
        self.assertEqual(c.opps, {})                            # no id consumed
        self.assertEqual(log_kinds(c), ["add_lead", "add_lead"])


class TestAddLead(unittest.TestCase):
    def setUp(self):
        self.c = make_crm()

    def test_email_validation(self):
        for bad in (123, None, "noat.com", "@b.com", "a@", "a@bcom",
                    "a@.com", "a@com.", "a@b@c.com", "a@b", " "):
            with self.assertRaises(ValueError):
                self.c.add_lead(bad, "N", "web", "rep1")
        # a dot strictly inside the domain passes, even when repeated
        self.c.add_lead("  A@B.CO.UK  ", "N", "web", "rep1")
        self.assertEqual(self.c.leads["L1"]["email"], "a@b.co.uk")
        self.assertEqual(self.c.leads["L1"]["name"], "N")       # failed calls used no ids

    def test_name_and_source_validation(self):
        for bad_name in ("", "   ", 5, None):
            with self.assertRaises(ValueError):
                self.c.add_lead("a@b.co", bad_name, "web", "rep1")
        for bad_src in ("phone", "", None, "WEB"):
            with self.assertRaises(ValueError):
                self.c.add_lead("a@b.co", "N", bad_src, "rep1")

    def test_check_order_email_name_source_duplicate(self):
        # 1 before 2: bad email beats bad name (messages differ)
        with self.assertRaises(ValueError) as ctx:
            self.c.add_lead("nope", "", "web", "rep1")
        self.assertIn("email", str(ctx.exception))
        # 2 before 3: bad name beats bad source
        with self.assertRaises(ValueError) as ctx:
            self.c.add_lead("ok@x.co", "", "bogus", "rep1")
        self.assertIn("name", str(ctx.exception))
        # 3 before 4: bad source on an existing email is ValueError, not Duplicate
        self.c.add_lead("dup@x.co", "N", "web", "rep1")
        with self.assertRaises(ValueError):
            self.c.add_lead("dup@x.co", "N", "bogus", "rep1")

    def test_duplicate_error_carries_existing_id(self):
        lid = self.c.add_lead("Dup@X.co ", "N", "web", "rep1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.c.add_lead(" dup@x.co", "Other", "event", "rep1")
        self.assertEqual(ctx.exception.existing_id, lid)
        self.assertTrue(issubclass(DuplicateLeadError, Exception))

    def test_scoring(self):
        cases = [("a@x.com", "web", 25), ("a@gmail.com", "web", 10),
                 ("a@yahoo.com", "event", 20), ("a@outlook.com", "referral", 30),
                 ("a@bigcorp.com", "referral", 45), ("b@bigcorp.com", "event", 35)]
        for i, (email, src, want) in enumerate(cases, start=1):
            self.c.add_lead(email, "N", src, "rep1")
            self.assertEqual(self.c.leads["L%d" % i]["score"], want, email)

    def test_ids_shape_and_log(self):
        self.assertEqual(self.c.add_lead("a@b.co", "  Bob ", "web", "rep1"), "L1")
        self.assertEqual(self.c.add_lead("c@d.co", "C", "web", "rep1"), "L2")
        self.assertEqual(self.c.leads["L1"],
                         {"id": "L1", "email": "a@b.co", "name": "Bob",
                          "source": "web", "score": 25, "owner": "rep1",
                          "status": "new"})
        self.assertEqual(self.c.log, [("add_lead", "L1", "rep1"),
                                      ("add_lead", "L2", "rep1")])

    def test_routing_lowest_load_then_id_tie_then_queue(self):
        # rep1 cap 2, rep2 cap 1: L1->rep1 (load tie, "rep1" < "rep2"),
        # L2->rep2 (load 0), L3->rep1 (rep2 full), L4-> queue (all full)
        owners = []
        for i in range(1, 5):
            lid = self.c.add_lead("e%d@x.co" % i, "N", "web", "mgr")
            owners.append(self.c.leads[lid]["owner"])
        self.assertEqual(owners, ["rep1", "rep2", "rep1", None])

    def test_routing_tie_uses_string_order(self):
        # Audit G4: the tie-break is "smallest id in string order", not
        # first-listed / numeric order. "rep10" < "rep2", so rep10 wins even
        # though rep2 appears first in reps.
        c = make_crm([{"id": "rep2", "role": "rep", "capacity": 1},
                      {"id": "rep10", "role": "rep", "capacity": 1},
                      {"id": "mgr", "role": "manager", "capacity": 5}])
        lid = c.add_lead("t@x.co", "N", "web", "mgr")
        self.assertEqual(c.leads[lid]["owner"], "rep10")

    def test_low_score_lead_cannot_qualify(self):
        lid = self.c.add_lead("a@gmail.com", "N", "web", "rep1")  # score 10
        with self.assertRaises(ValueError) as ctx:
            self.c.qualify(lid, "mgr")
        self.assertIn("score", str(ctx.exception))

    def test_manager_never_owns(self):
        c = make_crm([{"id": "m", "role": "manager", "capacity": 5}])
        lid = c.add_lead("a@b.co", "N", "web", "m")
        self.assertIsNone(c.leads[lid]["owner"])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.c = make_crm()
        self.lid = self.c.add_lead("a@bigcorp.com", "N", "referral", "rep1")

    def test_check_order_and_types(self):
        with self.assertRaises(ValueError):
            self.c.qualify("LX", "rep1")            # unknown lead first
        other = self.c.add_lead("b@bigcorp.com", "N", "referral", "rep2")
        # L1 -> rep1, other -> rep2 (rep1 load 1 vs rep2 load 0)
        with self.assertRaises(PermissionError):
            self.c.qualify(other, "rep1")           # not owner, not manager
        with self.assertRaises(PermissionError):
            self.c.qualify(self.lid, "rep2")        # symmetric
        self.c.qualify(self.lid, "mgr")
        # status(3) before score(4): already-qualified passes actor+status?
        # no: status check fires first and says "status", not "score"
        with self.assertRaises(ValueError) as ctx:
            self.c.qualify(self.lid, "mgr")
        self.assertIn("status", str(ctx.exception))

    def test_manager_can_qualify_queued_lead(self):
        c2 = make_crm([{"id": "r", "role": "rep", "capacity": 1},
                       {"id": "m", "role": "manager", "capacity": 1}])
        first = c2.add_lead("o@x.y", "A", "referral", "r")    # owned by r
        queued = c2.add_lead("t@x.y", "B", "referral", "r")   # r full -> queue
        self.assertIsNone(c2.leads[queued]["owner"])
        with self.assertRaises(PermissionError):
            c2.qualify(queued, "r")                            # r owns `first`, not this
        c2.qualify(queued, "m")
        self.assertEqual(c2.leads[queued]["status"], "qualified")
        self.assertIsNone(c2.leads[queued]["owner"])          # qualify does not assign
        self.assertEqual(c2.log[-1], ("qualify", queued, "m"))

    def test_qualify_accepts_score_exactly_30(self):
        # Audit G5: the gate is "at least 30" — a boundary score of exactly 30
        # (referral on a free-mail domain, no +15) must qualify.
        lid = self.c.add_lead("edge@outlook.com", "N", "referral", "mgr")
        self.assertEqual(self.c.leads[lid]["score"], 30)
        self.c.qualify(lid, "mgr")
        self.assertEqual(self.c.leads[lid]["status"], "qualified")

    def test_qualify_actor_checked_before_status(self):
        # Audit G6: check 2 (actor is owner or manager) runs before check 3
        # (status "new"), so a wrong actor on an already-qualified lead raises
        # PermissionError, not ValueError.
        self.c.qualify(self.lid, "mgr")                 # now status "qualified"
        n = len(self.c.log)
        with self.assertRaises(PermissionError):
            self.c.qualify(self.lid, "rep2")            # not owner, not manager
        self.assertEqual(len(self.c.log), n)

    def test_success_shape(self):
        self.c.qualify(self.lid, "rep1")
        self.assertEqual(self.c.leads[self.lid]["status"], "qualified")
        self.assertEqual(self.c.log[-1], ("qualify", self.lid, "rep1"))


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.c = make_crm()
        self.lid = qualifiable_lead(self.c)          # routed to rep1 (load tie)
        self.c.qualify(self.lid, "mgr")

    def test_checks_in_order(self):
        with self.assertRaises(ValueError):
            self.c.convert("LX", "x", "rep1")        # unknown lead before amount
        for bad in (0, -5, True, False, 1.5, "100", None):
            with self.assertRaises(ValueError):
                self.c.convert(self.lid, bad, "mgr")
        # amount(2) checked before actor(3): wrong actor + bad amount -> ValueError
        with self.assertRaises(ValueError):
            self.c.convert(self.lid, "x", "rep2")
        with self.assertRaises(PermissionError):
            self.c.convert(self.lid, 100, "rep2")    # not owner/manager
        # status(4): a new lead fails here even for the right actor
        web = self.c.add_lead("w@x.co", "N", "web", "mgr")   # not qualified
        with self.assertRaises(ValueError):
            self.c.convert(web, 100, "mgr")
        # id counter untouched by all the failures above:
        self.assertEqual(self.c.opps, {})
        self.assertEqual(log_kinds(self.c), ["add_lead", "qualify", "add_lead"])
        # a success after failures still gets the first id
        self.assertEqual(self.c.convert(self.lid, 5, "mgr"), "O1")

    def test_queued_qualified_lead_fails_owner_check(self):
        c = make_crm([{"id": "m", "role": "manager", "capacity": 5}])
        lid = c.add_lead("m@x.co", "N", "referral", "m")
        c.qualify(lid, "m")                          # manager may qualify queued
        with self.assertRaises(ValueError):
            c.convert(lid, 100, "m")                 # rule 5: no owner
        self.assertEqual(c.opps, {})

    def test_convert_actor_checked_before_status(self):
        # Audit G7: check 3 (actor) runs before check 4 (status "qualified"),
        # so a wrong actor on a "new" lead raises PermissionError, not ValueError.
        new = self.c.add_lead("n@x.co", "N", "web", "mgr")
        self.assertEqual(self.c.leads[new]["owner"], "rep2")   # rep2 load 0 < rep1 load 1
        self.assertEqual(self.c.leads[new]["status"], "new")
        n = len(self.c.log)
        with self.assertRaises(PermissionError):
            self.c.convert(new, 1000, "rep1")                  # valid amount, wrong actor
        self.assertEqual(len(self.c.log), n)
        self.assertEqual(self.c.leads[new]["status"], "new")

    def test_success_shape_and_ids(self):
        oid = self.c.convert(self.lid, 1000, "mgr")
        self.assertEqual(oid, "O1")
        self.assertEqual(self.c.opps["O1"],
                         {"id": "O1", "lead_id": self.lid, "owner": "rep1",
                          "amount": 1000, "original_amount": 1000,
                          "stage": "prospect"})
        self.assertEqual(self.c.leads[self.lid]["status"], "converted")
        self.assertEqual(self.c.log[-1], ("convert", "O1", "mgr"))
        # converted lead no longer counts toward load; the open opp does
        self.assertEqual(self.c._load("rep1"), 1)


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.c = make_crm()
        lid = qualifiable_lead(self.c)                # owner rep1
        self.c.qualify(lid, "mgr")
        self.oid = self.c.convert(lid, 40000, "mgr")

    def test_check_order(self):
        with self.assertRaises(ValueError):
            self.c.advance("OX", "bogus", "rep1")     # unknown opp first
        with self.assertRaises(ValueError):
            # stage validity (2) before actor (3): non-owner + bad stage -> ValueError
            self.c.advance(self.oid, "bogus", "rep2")
        with self.assertRaises(PermissionError):
            self.c.advance(self.oid, "proposal", "rep2")

    def test_only_immediate_next_or_lost(self):
        with self.assertRaises(ValueError):
            self.c.advance(self.oid, "won", "mgr")            # skip
        with self.assertRaises(ValueError):
            self.c.advance(self.oid, "prospect", "mgr")       # same/back
        self.c.advance(self.oid, "proposal", "mgr")           # legal
        self.assertEqual(self.c.opps[self.oid]["stage"], "proposal")
        with self.assertRaises(ValueError):
            self.c.advance(self.oid, "proposal", "mgr")       # no stay
        self.c.advance(self.oid, "lost", "mgr")               # lost from anywhere
        self.assertEqual(self.c.opps[self.oid]["stage"], "lost")
        with self.assertRaises(ValueError):
            self.c.advance(self.oid, "lost", "mgr")           # final
        with self.assertRaises(PermissionError):
            # actor check still precedes the final-stage check
            self.c.advance(self.oid, "lost", "rep2")
        self.assertEqual(self.c.log[-1], ("advance", self.oid, "mgr"))
        # 2 successful advances logged; failures added nothing
        # (setUp produced add_lead, qualify, convert)
        self.assertEqual(len(self.c.log), 5)                 # nothing logged on failures

    def test_big_negotiation_requires_manager(self):
        c = make_crm()
        lid = qualifiable_lead(c, "b@x.co")             # routed rep1
        c.qualify(lid, "mgr")
        oid = c.convert(lid, 50001, "mgr")              # owner rep1
        c.advance(oid, "proposal", "rep1")
        with self.assertRaises(PermissionError):
            c.advance(oid, "negotiation", "rep1")       # > 50000, not manager
        self.assertEqual(c.opps[oid]["stage"], "proposal")
        c.discount(oid, 20, "mgr")                      # 50001*80//100 = 40000
        self.assertEqual(c.opps[oid]["amount"], 40000)
        c.advance(oid, "negotiation", "rep1")           # now a rep may
        self.assertEqual(c.opps[oid]["stage"], "negotiation")
        # exactly 50000 is not "greater than": rep allowed
        c2 = make_crm()
        l2 = qualifiable_lead(c2, "c@x.co")
        c2.qualify(l2, "mgr")
        o2 = c2.convert(l2, 50000, "mgr")
        c2.advance(o2, "proposal", "rep1")
        c2.advance(o2, "negotiation", "rep1")
        self.assertEqual(c2.opps[o2]["stage"], "negotiation")

    def test_manager_advances_over_50000_to_negotiation(self):
        # Audit G3: the > 50000 negotiation gate binds reps only — a manager
        # actor may advance an over-50000 opp to "negotiation".
        c = make_crm()
        lid = qualifiable_lead(c, "big@x.co")             # owner rep1
        c.qualify(lid, "mgr")
        oid = c.convert(lid, 60000, "mgr")
        c.advance(oid, "proposal", "mgr")
        c.advance(oid, "negotiation", "mgr")              # manager exemption
        self.assertEqual(c.opps[oid]["stage"], "negotiation")
        self.assertEqual(c.log[-1], ("advance", oid, "mgr"))

    def test_advance_won_releases_slot(self):
        # Audit G1: reaching "won" frees the owner's slot and drains the FIFO
        # waiting queue exactly like "lost" (spec: on "won" or "lost").
        c = make_crm([{"id": "rep1", "role": "rep", "capacity": 1},
                      {"id": "rep2", "role": "rep", "capacity": 1},
                      {"id": "mgr", "role": "manager", "capacity": 9}])
        l1 = c.add_lead("w1@x.co", "1", "referral", "mgr")   # -> rep1 (tie -> id)
        l2 = c.add_lead("w2@x.co", "2", "referral", "mgr")   # -> rep2
        q1 = c.add_lead("w3@x.co", "3", "referral", "mgr")   # -> queue (all full)
        self.assertEqual([c.leads[k]["owner"] for k in ("L1", "L2", "L3")],
                         ["rep1", "rep2", None])
        c.qualify(l1, "rep1")
        oid = c.convert(l1, 1000, "rep1")              # rep1 load: open opp = 1 = cap
        c.advance(oid, "proposal", "rep1")
        c.advance(oid, "negotiation", "rep1")          # 1000 <= 50000: rep allowed
        c.advance(oid, "won", "rep1")                  # won frees the slot
        self.assertEqual(c.opps[oid]["stage"], "won")
        self.assertEqual(c.leads[q1]["owner"], "rep1") # oldest waiting lead assigned
        self.assertEqual(c.log[-2:], [("advance", oid, "rep1"),
                                      ("assign", q1, "system")])

    def test_slot_release_and_log_trail(self):
        c = make_crm([{"id": "rep1", "role": "rep", "capacity": 1},
                      {"id": "rep2", "role": "rep", "capacity": 1},
                      {"id": "mgr", "role": "manager", "capacity": 9}])
        l1 = c.add_lead("w1@x.co", "1", "referral", "mgr")   # rep1 (tie -> id)
        l2 = c.add_lead("w2@x.co", "2", "referral", "mgr")   # rep2
        q1 = c.add_lead("w3@x.co", "3", "referral", "mgr")   # queue
        q2 = c.add_lead("w4@x.co", "4", "referral", "mgr")   # queue
        self.assertEqual([c.leads[k]["owner"] for k in ("L1", "L2", "L3", "L4")],
                         ["rep1", "rep2", None, None])
        c.qualify(l1, "rep1")
        oid = c.convert(l1, 1000, "rep1")          # load: opp only = 1 = cap
        c.advance(oid, "proposal", "rep1")
        c.advance(oid, "lost", "rep1")             # frees the slot -> oldest first
        self.assertEqual(c.leads[q1]["owner"], "rep1")
        self.assertIsNone(c.leads[q2]["owner"])    # rep1 cap 1 -> stops at one
        self.assertEqual(c.log[-2:], [("advance", oid, "rep1"),
                                      ("assign", q1, "system")])
        # a failed call frees nothing and logs nothing
        n = len(c.log)
        with self.assertRaises(PermissionError):
            c.advance(oid, "won", "rep2")          # rep2: not owner, not manager
        self.assertEqual(len(c.log), n)


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.c = make_crm()
        lid = qualifiable_lead(self.c)                 # owner rep1
        self.c.qualify(lid, "mgr")
        self.oid = self.c.convert(lid, 1000, "mgr")

    def test_checks(self):
        with self.assertRaises(ValueError):
            self.c.discount("OX", 0, "mgr")            # unknown opp before pct
        for bad in (0, 31, -1, True, False, 10.5, "10", None):
            with self.assertRaises(ValueError):
                self.c.discount(self.oid, bad, "mgr")
        # pct(2) before actor(3): non-owner + bad pct -> ValueError
        with self.assertRaises(ValueError):
            self.c.discount(self.oid, 1000, "rep2")
        with self.assertRaises(PermissionError):
            self.c.discount(self.oid, 5, "rep2")       # not owner/manager
        with self.assertRaises(PermissionError):
            self.c.discount(self.oid, 15, "rep1")      # rep limit at 10
        self.c.advance(self.oid, "lost", "rep1")       # make it final
        # stage(4) before rep-limit(5): over-limit pct on final -> ValueError
        with self.assertRaises(ValueError):
            self.c.discount(self.oid, 50, "rep1")
        with self.assertRaises(PermissionError):
            self.c.discount(self.oid, 5, "rep2")       # actor still first
        self.assertEqual(self.c.opps[self.oid]["amount"], 1000)  # unchanged

    def test_amounts_cumulative_floor_and_log(self):
        self.c.discount(self.oid, 10, "rep1")          # rep at exactly 10: ok
        self.assertEqual(self.c.opps[self.oid]["amount"], 900)
        self.assertEqual(self.c.log[-1], ("discount", self.oid, "rep1"))
        self.c.discount(self.oid, 20, "mgr")           # 900*80//100 = 720, 72000 >= 70000
        self.assertEqual(self.c.opps[self.oid]["amount"], 720)
        self.c.discount(self.oid, 1, "mgr")            # 720*99//100 = 712, 71200 >= 70000
        self.assertEqual(self.c.opps[self.oid]["amount"], 712)
        with self.assertRaises(ValueError):            # 712*98//100 = 697 -> 69700 < 70000
            self.c.discount(self.oid, 2, "mgr")        # floor vs original_amount, not current
        self.assertEqual(self.c.opps[self.oid]["amount"], 712)
        self.assertEqual(log_kinds(self.c).count("discount"), 3)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.c = make_crm()
        lid = qualifiable_lead(self.c)
        self.c.qualify(lid, "mgr")
        self.oid = self.c.convert(lid, 1000, "mgr")    # owner rep1

    def test_checks_in_order(self):
        with self.assertRaises(ValueError):
            self.c.transfer("OX", "ghost", "rep1")     # opp(1) before actor(2)
        with self.assertRaises(PermissionError):
            self.c.transfer(self.oid, "rep2", "rep1")  # actor must be manager
        with self.assertRaises(PermissionError):
            # actor(2) before new_owner(3): manager actor + invalid owner -> owner error type
            self.c.transfer(self.oid, "ghost", "rep2")
        with self.assertRaises(ValueError):
            self.c.transfer(self.oid, "ghost", "mgr")  # unknown new owner
        with self.assertRaises(ValueError):
            self.c.transfer(self.oid, "mgr", "mgr")    # manager is not a rep
        with self.assertRaises(ValueError):
            self.c.transfer(self.oid, "rep1", "mgr")   # same owner
        # capacity: give rep2 an open opp (rep1 has load 1 from O1, cap 2)
        lid2 = self.c.add_lead("z@x.co", "N", "referral", "mgr")   # -> rep2 (load 0 < rep1 1)
        self.c.qualify(lid2, "mgr")
        self.c.convert(lid2, 100, "mgr")               # rep2 load 1 = cap
        with self.assertRaises(ValueError):
            self.c.transfer(self.oid, "rep2", "mgr")   # new owner at capacity
        # final stage(4) before same-owner(5): owner rep2's opp, lost, transfer to rep2
        c = make_crm()
        l = qualifiable_lead(c, "f@x.co")
        c.qualify(l, "mgr")
        o = c.convert(l, 100, "mgr")
        c.advance(o, "lost", "mgr")                    # lost from prospect is legal
        with self.assertRaises(ValueError):
            c.transfer(o, "rep2", "mgr")               # final stage
        self.assertEqual(log_kinds(c)[-1], "advance")  # transfer logged nothing

    def test_success_moves_ownership_and_logs(self):
        self.c.transfer(self.oid, "rep2", "mgr")
        self.assertEqual(self.c.opps[self.oid]["owner"], "rep2")
        self.assertEqual(self.c.log[-1], ("transfer", self.oid, "mgr"))
        self.assertEqual(self.c._load("rep1"), 0)
        self.assertEqual(self.c._load("rep2"), 1)
        # rep2 now full; next lead routes to rep1 (load 0 < cap 2)
        lid = self.c.add_lead("n@x.co", "N", "web", "mgr")
        self.assertEqual(self.c.leads[lid]["owner"], "rep1")

    def test_transfer_with_empty_queue_adds_no_assign(self):
        n_before = len(self.c.log)
        self.c.transfer(self.oid, "rep2", "mgr")
        self.assertEqual(self.c.log[n_before:],
                         [("transfer", self.oid, "mgr")])


class TestForecast(unittest.TestCase):
    def test_forecast_weighted_is_integer_floor(self):
        # Audit G2: weighted uses floor division (spec: amount * w // 100);
        # 999 at prospect -> 99, not the float 99.9.
        c = make_crm()
        lid = qualifiable_lead(c, "floor@x.co")            # owner rep1
        c.qualify(lid, "mgr")
        c.convert(lid, 999, "mgr")                         # stage prospect, w = 10
        fc = c.forecast()
        self.assertEqual(fc, {"open": 1, "weighted": 99, "won": 0})
        self.assertIsInstance(fc["weighted"], int)

    def test_forecast(self):
        c = make_crm()
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 0})
        lid = qualifiable_lead(c, "f@x.co")            # owner rep1
        c.qualify(lid, "mgr")
        oid = c.convert(lid, 1000, "mgr")
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 100, "won": 0})
        c.advance(oid, "proposal", "mgr")
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 300, "won": 0})
        c.advance(oid, "negotiation", "mgr")
        self.assertEqual(c.forecast(), {"open": 1, "weighted": 600, "won": 0})
        c.advance(oid, "won", "mgr")
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 1000})
        # won sum uses the discounted amount; lost contributes nothing
        lid2 = qualifiable_lead(c, "g@x.co")           # rep1 load 0 again
        c.qualify(lid2, "mgr")
        oid2 = c.convert(lid2, 700, "mgr")
        c.advance(oid2, "proposal", "mgr")
        c.discount(oid2, 10, "mgr")                    # 700 -> 630
        c.advance(oid2, "negotiation", "mgr")
        c.advance(oid2, "won", "mgr")
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 1630})
        lid3 = qualifiable_lead(c, "h@x.co")
        c.qualify(lid3, "mgr")
        oid3 = c.convert(lid3, 999, "mgr")
        c.advance(oid3, "lost", "mgr")
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 1630})
        # forecast takes no actor and appends nothing
        n = len(c.log)
        c.forecast()
        self.assertEqual(len(c.log), n)


class TestIntegration(unittest.TestCase):
    def test_full_flow_end_to_end(self):
        c = make_crm()
        lid = c.add_lead(" Alice@BigCorp.com ", "Alice", "referral", "mgr")
        self.assertEqual(c.leads[lid], {
            "id": "L1", "email": "alice@bigcorp.com", "name": "Alice",
            "source": "referral", "score": 45, "owner": "rep1",
            "status": "new"})
        c.qualify(lid, "rep1")
        oid = c.convert(lid, 20000, "rep1")
        c.advance(oid, "proposal", "rep1")
        c.discount(oid, 10, "rep1")                    # 18000
        c.advance(oid, "negotiation", "rep1")          # 18000 <= 50000
        c.advance(oid, "won", "rep1")
        self.assertEqual(c.forecast(), {"open": 0, "weighted": 0, "won": 18000})
        self.assertEqual(log_kinds(c),
                         ["add_lead", "qualify", "convert", "advance",
                          "discount", "advance", "advance"])
        self.assertEqual([e[2] for e in c.log],
                         ["mgr", "rep1", "rep1", "rep1", "rep1", "rep1", "rep1"])


if __name__ == "__main__":
    unittest.main()
