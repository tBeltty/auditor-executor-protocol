"""Unit tests for crm.py, derived from specs/crm.md.

Note on load accounting: converting a lead moves exactly one unit of load from
the lead (status "converted", uncounted) to the opportunity (stage open,
counted) — capacity does not free up at conversion.
"""

import unittest

from crm import CRM, DuplicateLeadError


def std_reps():
    """Two reps with capacity 1 each, plus a manager."""
    return [
        {"id": "r1", "role": "rep", "capacity": 1},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 5},
    ]


def one_rep(cap=10):
    return [{"id": "r1", "role": "rep", "capacity": cap},
            {"id": "m1", "role": "manager", "capacity": 5}]


def owned_qualified_opp(crm, email, amount, source="referral", actor="m1"):
    """Helper: add lead -> qualify -> convert. Returns (lead_id, opp_id)."""
    lid = crm.add_lead(email, "N", source, actor)
    crm.qualify(lid, actor)
    oid = crm.convert(lid, amount, actor)
    return lid, oid


class TestUnknownActor(unittest.TestCase):
    def test_permission_error_checked_first_everywhere(self):
        crm = CRM(std_reps())
        with self.assertRaises(PermissionError):
            crm.add_lead("not an email", "Bob", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ghost")
        with self.assertRaises(PermissionError):
            crm.convert("L1", -1, "ghost")
        with self.assertRaises(PermissionError):
            crm.advance("O1", "bogus", "ghost")
        with self.assertRaises(PermissionError):
            crm.discount("O1", 99, "ghost")
        with self.assertRaises(PermissionError):
            crm.transfer("O1", "r1", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.opps, {})


class TestAddLeadValidation(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(std_reps())

    def test_invalid_emails(self):
        for bad in ["noatsign.com", "a@b", "a@@b.com", "@b.com", "a@.com",
                    "a@com.", 123, None, ["a@b.com"]]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.add_lead(bad, "N", "web", "m1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_valid_emails_and_normalization(self):
        lid = self.crm.add_lead("  Jo.H@Example.COM  ", "  Nan  ", "web", "m1")
        lead = self.crm.leads[lid]
        self.assertEqual(lead["email"], "jo.h@example.com")
        self.assertEqual(lead["name"], "Nan")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["score"], 25)  # web 10 + domain bonus 15
        self.assertEqual(lead["id"], "L1")
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])
        # ".x.com" has a dot at index 2: neither first nor last char of the
        # domain, so per the spec letter this email is valid.
        lid2 = self.crm.add_lead("a@.x.com", "N", "web", "m1")
        self.assertEqual(self.crm.leads[lid2]["email"], "a@.x.com")

    def test_name_and_source_checks(self):
        for bad_name in ["   ", "", 42, None]:
            with self.assertRaises(ValueError, msg=repr(bad_name)):
                self.crm.add_lead("a@b.com", bad_name, "web", "m1")
        for bad_source in ["phone", "WEB", "", None]:
            with self.assertRaises(ValueError, msg=repr(bad_source)):
                self.crm.add_lead("a@b.com", "N", bad_source, "m1")

    def test_scores(self):
        cases = [
            ("w1@gmail.com", "web", 10), ("w2@example.com", "web", 25),
            ("r1@yahoo.com", "referral", 30), ("r2@example.com", "referral", 45),
            ("e1@outlook.com", "event", 20), ("e2@example.com", "event", 35),
        ]
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 100}])
        for email, source, expected in cases:
            lid = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lid]["score"], expected)

    def test_duplicate_lead_error(self):
        lid1 = self.crm.add_lead("A@B.com", "First", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            self.crm.add_lead(" a@b.com ", "Second", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, lid1)
        self.assertEqual(len(self.crm.leads), 1)
        # failed call: no extra log entry, no id consumed
        self.assertEqual(self.crm.log, [("add_lead", "L1", "m1")])
        lid2 = self.crm.add_lead("c@d.com", "Third", "web", "m1")
        self.assertEqual(lid2, "L2")  # counter counts successes only

    def test_duplicate_of_queued_lead(self):
        # Audit P5: duplicate detection covers leads waiting in the queue
        # (owner None), not just assigned ones.
        crm = CRM(std_reps())
        crm.add_lead("1@x.com", "A", "web", "m1")   # r1
        crm.add_lead("2@x.com", "B", "web", "m1")   # r2
        queued = crm.add_lead("Q@X.com", "C", "web", "m1")  # all full -> queue
        self.assertIsNone(crm.leads[queued]["owner"])
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" q@x.com ", "C2", "event", "m1")
        self.assertEqual(ctx.exception.existing_id, queued)
        # failed call: the queued lead is untouched, no log, no id consumed
        self.assertEqual(len(crm.leads), 3)
        self.assertEqual(crm.log, [("add_lead", lid, "m1") for lid in
                                   ("L1", "L2", queued)])
        nxt = crm.add_lead("3@x.com", "D", "web", "m1")
        self.assertEqual(nxt, "L4")


class TestAssignment(unittest.TestCase):
    def test_lowest_load_then_smallest_id_string_order(self):
        # "r10" < "r2" in string order; both start at load 0.
        crm = CRM([{"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "r10", "role": "rep", "capacity": 1}])
        lid = crm.add_lead("a@b.com", "N", "web", "r10")
        self.assertEqual(crm.leads[lid]["owner"], "r10")

    def test_lowest_load_not_first_listed(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2},
                   {"id": "r2", "role": "rep", "capacity": 5},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        crm.add_lead("1@x.com", "A", "web", "m1")  # tie at load 0 -> r1
        lid = crm.add_lead("2@x.com", "B", "web", "m1")  # r1 load 1, r2 load 0
        self.assertEqual(crm.leads[lid]["owner"], "r2")

    def test_capacity_and_queue(self):
        crm = CRM(std_reps())
        l1 = crm.add_lead("1@x.com", "A", "web", "m1")
        l2 = crm.add_lead("2@x.com", "B", "web", "m1")
        l3 = crm.add_lead("3@x.com", "C", "web", "m1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])
        # an add with no free capacity still succeeds (queued), with a log entry
        self.assertEqual(len(crm.log), 3)
        self.assertEqual(crm.log[-1], ("add_lead", "L3", "m1"))

    def test_managers_never_own(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 5}])
        lid = crm.add_lead("a@b.com", "N", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(one_rep())  # r1 capacity 10, m1 manager
        self.good = self.crm.add_lead("g@example.com", "G", "referral", "m1")  # 45
        self.low = self.crm.add_lead("l@gmail.com", "L", "web", "m1")          # 10

    def test_checks_in_order(self):
        with self.assertRaises(ValueError):
            self.crm.qualify("L99", "m1")           # check 1: exists
        # unowned lead: a rep that is not the owner (owner is None) -> PermissionError
        crm2 = CRM(std_reps())
        crm2.add_lead("9@x.com", "A", "referral", "m1")  # r1
        crm2.add_lead("8@x.com", "B", "referral", "m1")  # r2
        queued = crm2.add_lead("7@x.com", "C", "referral", "m1")  # owner None
        with self.assertRaises(PermissionError):
            crm2.qualify(queued, "r1")              # check 2 before score/status
        with self.assertRaises(ValueError):
            self.crm.qualify(self.low, "r1")        # check 4: score < 30
        self.crm.qualify(self.good, "r1")
        with self.assertRaises(ValueError):
            self.crm.qualify(self.good, "r1")       # check 3: status must be new

    def test_success_owner_and_manager(self):
        self.crm.qualify(self.good, "r1")
        self.assertEqual(self.crm.leads[self.good]["status"], "qualified")
        self.assertEqual(self.crm.log[-1], ("qualify", self.good, "r1"))
        g2 = self.crm.add_lead("g2@example.com", "G", "referral", "m1")
        self.crm.qualify(g2, "m1")  # manager may qualify any lead
        self.assertEqual(self.crm.leads[g2]["status"], "qualified")

    def test_manager_qualifies_unowned_queued_lead(self):
        # Audit remediation 3 (P4): manager qualifying an unowned (queued)
        # lead was only exercised as setup in TestConvert; asserted here in
        # its own right — status flips, owner stays None, log entry present.
        crm = CRM(std_reps())
        crm.add_lead("1@x.com", "A", "referral", "m1")   # r1
        crm.add_lead("2@x.com", "B", "referral", "m1")   # r2
        queued = crm.add_lead("3@x.com", "C", "referral", "m1")  # score 45, queued
        self.assertIsNone(crm.leads[queued]["owner"])
        n = len(crm.log)
        crm.qualify(queued, "m1")
        self.assertEqual(crm.leads[queued]["status"], "qualified")
        self.assertIsNone(crm.leads[queued]["owner"])  # qualify assigns nothing
        self.assertEqual(crm.log[n:], [("qualify", queued, "m1")])

    def test_failure_logs_nothing(self):
        n = len(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.qualify(self.low, "r1")
        self.assertEqual(self.crm.log, self.crm.log[:n])
        self.assertEqual(self.crm.leads[self.low]["status"], "new")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(one_rep())
        self.lid = self.crm.add_lead("g@x.co", "G", "referral", "m1")  # r1, 45
        self.crm.qualify(self.lid, "r1")

    def test_amount_validation(self):
        for bad in [0, -5, "100", 10.5, True, False, None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.convert(self.lid, bad, "r1")

    def test_checks_in_order(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L99", -1, "r1")       # exists (1) before amount (2)
        crm2 = CRM(std_reps())
        lid = crm2.add_lead("g@x.co", "G", "referral", "m1")  # owner r1
        with self.assertRaises(ValueError):
            crm2.convert(lid, 0, "r2")              # amount (2) before permission (3)
        with self.assertRaises(PermissionError):
            crm2.convert(lid, 100, "r2")
        with self.assertRaises(ValueError):
            crm2.convert("L98", 100, "r2")          # exists (1) before permission
        # qualified but unowned -> ValueError (check 5)
        crm3 = CRM([{"id": "r1", "role": "rep", "capacity": 0},
                    {"id": "m1", "role": "manager", "capacity": 5}])
        lid3 = crm3.add_lead("u@x.co", "U", "referral", "m1")
        crm3.qualify(lid3, "m1")
        with self.assertRaises(ValueError):
            crm3.convert(lid3, 100, "m1")
        # not qualified -> ValueError (check 4)
        crm4 = CRM(one_rep())
        lid4 = crm4.add_lead("n@x.co", "N", "referral", "m1")
        with self.assertRaises(ValueError):
            crm4.convert(lid4, 100, "r1")

    def test_success(self):
        oid = self.crm.convert(self.lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(self.crm.opps[oid], {
            "id": "O1", "lead_id": self.lid, "owner": "r1",
            "amount": 1000, "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[self.lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))
        # failed convert does not consume an opp id
        with self.assertRaises(ValueError):
            self.crm.convert(self.lid, -1, "r1")
        lid2 = self.crm.add_lead("g2@x.co", "G", "referral", "m1")
        self.crm.qualify(lid2, "m1")
        oid2 = self.crm.convert(lid2, 500, "m1")
        self.assertEqual(oid2, "O2")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(one_rep())
        self.lid, self.oid = owned_qualified_opp(self.crm, "g@x.co", 1000)

    def test_happy_path_and_logging(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        adv = [e for e in self.crm.log if e[0] == "advance"]
        self.assertEqual(adv, [("advance", "O1", "r1")] * 3)

    def test_no_skipping_no_same_stage(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", "r1")  # skip proposal
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "prospect", "r1")     # same stage
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")

    def test_lost_from_any_nonfinal(self):
        crm = CRM(one_rep())
        _, o1 = owned_qualified_opp(crm, "l1@x.co", 100)
        crm.advance(o1, "lost", "r1")
        self.assertEqual(crm.opps[o1]["stage"], "lost")
        _, o2 = owned_qualified_opp(crm, "l2@x.co", 100)
        crm.advance(o2, "proposal", "r1")
        crm.advance(o2, "lost", "r1")
        self.assertEqual(crm.opps[o2]["stage"], "lost")
        _, o3 = owned_qualified_opp(crm, "l3@x.co", 100)
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "m1")
        crm.advance(o3, "lost", "m1")
        self.assertEqual(crm.opps[o3]["stage"], "lost")

    def test_final_stages_are_final(self):
        self.crm.advance(self.oid, "lost", "r1")
        for stage in ["proposal", "prospect", "won", "lost"]:
            with self.assertRaises(ValueError, msg=stage):
                self.crm.advance(self.oid, stage, "r1")

    def test_checks_in_order(self):
        with self.assertRaises(ValueError):
            self.crm.advance("O9", "zzz", "r1")     # exists (1) first
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "zzz", "r1")  # stage validity (2)
        crm2 = CRM(std_reps())
        _, oid = owned_qualified_opp(crm2, "g@x.co", 1000)  # owner r1
        # stage check (2) precedes permission (3): r2 + illegal stage -> ValueError
        with self.assertRaises(ValueError):
            crm2.advance(oid, "zzz", "r2")
        with self.assertRaises(PermissionError):
            crm2.advance(oid, "proposal", "r2")
        # permission (3) precedes finality (4)
        crm2.advance(oid, "proposal", "m1")
        crm2.advance(oid, "negotiation", "m1")
        crm2.advance(oid, "won", "m1")
        with self.assertRaises(PermissionError):
            crm2.advance(oid, "lost", "r2")

    def test_big_deal_negotiation_needs_manager(self):
        crm = CRM(one_rep())
        _, oid = owned_qualified_opp(crm, "big@x.co", 60000)
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        # adjacency (5) precedes the manager rule (6): from proposal, "won" is
        # not the next stage -> ValueError even though amount is big
        with self.assertRaises(ValueError):
            crm.advance(oid, "won", "r1")
        crm.advance(oid, "negotiation", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")
        # exactly 50000 is not "greater than 50000": rep may proceed
        _, oid2 = owned_qualified_opp(crm, "even@x.co", 50000)
        crm.advance(oid2, "proposal", "r1")
        crm.advance(oid2, "negotiation", "r1")
        # the >50000 rule covers negotiation only; "won" needs no manager
        crm.advance(oid2, "won", "r1")
        self.assertEqual(crm.opps[oid2]["stage"], "won")

    def test_failed_advance_changes_nothing(self):
        n = len(self.crm.log)
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "prospect")
        self.assertEqual(self.crm.log, self.crm.log[:n])


class TestBackfill(unittest.TestCase):
    def test_slot_freed_on_close_assigns_fifo_with_system_log(self):
        crm = CRM(std_reps())
        lid0, oid0 = owned_qualified_opp(crm, "own@x.co", 100)      # r1
        crm.add_lead("q1@x.co", "Q", "web", "m1")                   # r2
        q2 = crm.add_lead("q2@x.co", "Q", "web", "m1")              # queued
        q3 = crm.add_lead("q3@x.co", "Q", "web", "m1")              # queued
        crm.advance(oid0, "lost", "r1")
        self.assertEqual(crm.leads[q2]["owner"], "r1")  # oldest waiting
        self.assertIsNone(crm.leads[q3]["owner"])       # capacity 1: one fill
        self.assertEqual(crm.log[-2:], [("advance", "O1", "r1"),
                                        ("assign", q2, "system")])

    def test_won_close_backfills_queue(self):
        # Audit remediation 1 (NC1 guard): the spec frees the owner's slot when
        # the new stage is "won" OR "lost"; the delivered suite's only
        # close-with-queue case was "lost", so breaking won's backfill stayed
        # green. This test must fail if advance() stops backfilling on "won".
        crm = CRM(std_reps())
        _, oid0 = owned_qualified_opp(crm, "own@x.co", 1000)        # r1 (O1)
        crm.add_lead("q1@x.co", "Q", "web", "m1")                   # r2
        queued = crm.add_lead("q2@x.co", "Q", "web", "m1")          # queued
        self.assertIsNone(crm.leads[queued]["owner"])
        crm.advance(oid0, "proposal", "r1")
        crm.advance(oid0, "negotiation", "r1")
        crm.advance(oid0, "won", "r1")
        self.assertEqual(crm.opps[oid0]["stage"], "won")
        self.assertEqual(crm.leads[queued]["owner"], "r1")  # won frees the slot
        self.assertEqual(crm.log[-2:], [("advance", "O1", "r1"),
                                        ("assign", queued, "system")])
        # the other rep was untouched: exactly one system-assign happened
        self.assertEqual([e for e in crm.log if e[0] == "assign"],
                         [("assign", queued, "system")])

    def test_no_backfill_on_nonfinal_advance(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        lid0, oid0 = owned_qualified_opp(crm, "own@x.co", 100)
        crm.add_lead("q@x.co", "Q", "web", "m1")        # queued
        crm.advance(oid0, "proposal", "m1")
        self.assertEqual(crm.log[-1], ("advance", "O1", "m1"))

    def test_transfer_frees_sending_rep_for_future_assignment(self):
        # The spec's transfer backfill ("free the previous owner's slot as in
        # advance") cannot be observed assigning a waiting lead: a lead joins
        # the queue only when every rep is at capacity, while a transfer needs
        # its target below capacity — and any close/transfer backfills the
        # freed slot immediately, so the queue is empty whenever a transfer is
        # legal. What IS observable: transfer appends exactly one log entry,
        # and the sending rep's capacity is freed for the next add_lead.
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        _, oid0 = owned_qualified_opp(crm, "own@x.co", 100)  # O1 owned by r1
        q1 = crm.add_lead("q1@x.co", "Q", "web", "m1")       # r2 (only slot)
        q2 = crm.add_lead("q2@x.co", "Q", "web", "m1")       # queued: all full
        n = len(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(oid0, "r2", "m1")                   # r2 at capacity
        self.assertEqual(len(crm.log), n)                    # failed call: no log
        crm.advance(oid0, "lost", "m1")               # close O1; r1's slot frees
        self.assertEqual(crm.leads[q2]["owner"], "r1")  # immediate backfill
        new = crm.add_lead("q3@x.co", "Q", "web", "m1")
        # r1 holds q2, r2 holds q1, so the new lead queues and logs one entry
        self.assertIsNone(crm.leads[new]["owner"])
        self.assertEqual(crm.log[n:], [("advance", "O1", "m1"),
                                       ("assign", q2, "system"),
                                       ("add_lead", new, "m1")])


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(one_rep())
        self.lid, self.oid = owned_qualified_opp(self.crm, "g@x.co", 1000)

    def test_pct_validation(self):
        for bad in [0, -1, 31, 100, "5", 5.0, True, False, None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                self.crm.discount(self.oid, bad, "r1")

    def test_checks_in_order(self):
        with self.assertRaises(ValueError):
            self.crm.discount("O9", 99, "r1")       # exists (1) before pct (2)
        crm2 = CRM(std_reps())
        _, oid = owned_qualified_opp(crm2, "g@x.co", 1000)  # owner r1
        with self.assertRaises(ValueError):
            crm2.discount(oid, 99, "r2")            # pct (2) before permission (3)
        with self.assertRaises(PermissionError):
            crm2.discount(oid, 25, "r2")
        crm2.advance(oid, "proposal", "m1")
        crm2.advance(oid, "negotiation", "m1")
        crm2.advance(oid, "won", "m1")
        with self.assertRaises(PermissionError):
            crm2.discount(oid, 25, "r2")            # permission (3) before final (4)
        with self.assertRaises(ValueError):
            crm2.discount(oid, 25, "r1")            # final (4) before rep cap (5)
        with self.assertRaises(ValueError):
            crm2.discount(oid, 5, "m1")             # final (4) before cumulative (6)

    def test_role_caps(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")   # rep limit is 10
        self.crm.discount(self.oid, 10, "r1")       # 1000 -> 900
        self.assertEqual(self.crm.opps[self.oid]["amount"], 900)
        # cap is per call: a manager may apply 20 (cumulative floor still holds)
        self.crm.discount(self.oid, 20, "m1")       # 900 -> 720, >= 700 ok
        self.assertEqual(self.crm.opps[self.oid]["amount"], 720)
        self.assertEqual(self.crm.log[-1], ("discount", "O1", "m1"))
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")   # cap applies on later calls too

    def test_cumulative_cap_on_original_amount(self):
        self.crm.discount(self.oid, 15, "m1")       # 1000 -> 850
        self.crm.discount(self.oid, 15, "m1")       # 850 -> 722 (72200 >= 70000)
        self.assertEqual(self.crm.opps[self.oid]["amount"], 722)
        self.crm.discount(self.oid, 3, "m1")        # 722 -> 700 exactly: allowed
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, "m1")    # 693 -> 69300 < 70000
        # failed call leaves amount and log untouched
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)
        self.assertEqual(self.crm.log[-1], ("discount", "O1", "m1"))

    def test_direct_30_ok_then_any_more_fails(self):
        self.crm.discount(self.oid, 30, "m1")       # 1000 -> 700
        self.assertEqual(self.crm.opps[self.oid]["amount"], 700)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, "m1")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                        {"id": "r2", "role": "rep", "capacity": 2},
                        {"id": "m1", "role": "manager", "capacity": 5}])
        self.lid, self.oid = owned_qualified_opp(self.crm, "g@x.co", 500)  # owner r1

    def test_manager_only(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")

    def test_checks_in_order(self):
        with self.assertRaises(ValueError):
            self.crm.transfer("O9", "ghost", "m1")      # exists (1)
        with self.assertRaises(PermissionError):
            self.crm.transfer("O9", "ghost", "ghost")   # actor (PermissionError) first
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "ghost", "r1")  # manager (2) before target (3)
        for bad_target in ["ghost", "m1"]:              # unknown, or not a rep
            with self.assertRaises(ValueError, msg=bad_target):
                self.crm.transfer(self.oid, bad_target, "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")     # same owner (5)

    def test_capacity_check(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        _, oid_a = owned_qualified_opp(crm, "a@x.co", 500)  # owner r1
        _, oid_b = owned_qualified_opp(crm, "b@x.co", 500)  # owner r2 (open, load 1)
        with self.assertRaises(ValueError):
            crm.transfer(oid_a, "r2", "m1")                 # r2 at capacity
        crm.advance(oid_b, "lost", "m1")                    # frees r2
        crm.transfer(oid_a, "r2", "m1")                     # now legal
        self.assertEqual(crm.opps[oid_a]["owner"], "r2")

    def test_final_stage(self):
        self.crm.advance(self.oid, "proposal", "m1")
        self.crm.advance(self.oid, "negotiation", "m1")
        self.crm.advance(self.oid, "won", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r2", "m1")

    def test_success(self):
        n = len(self.crm.log)
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", "O1", "m1"))
        # A legal transfer implies an empty queue, so its post-transfer slot
        # release never produces an "assign" entry (see invariant test below).
        self.assertEqual(len(self.crm.log), n + 1)

    def test_queued_leads_make_every_transfer_illegal(self):
        # Audit remediation 4 (invariant pin): the backfill branch inside
        # transfer is unreachable because a non-empty queue means EVERY rep is
        # at capacity (leads queue only when no rep had a free slot, and every
        # other load-decreasing path backfills immediately) — so check 6
        # rejects every rep target while the queue holds anyone.
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 1},
                   {"id": "r2", "role": "rep", "capacity": 1},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        _, oid = owned_qualified_opp(crm, "own@x.co", 500)   # r1 at capacity
        crm.add_lead("q1@x.co", "Q", "web", "m1")            # r2 at capacity
        queued = crm.add_lead("q2@x.co", "Q", "web", "m1")   # queue non-empty
        self.assertIsNone(crm.leads[queued]["owner"])
        n = len(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")                     # check 6: r2 full
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r1", "m1")                     # check 5: same owner
        self.assertEqual(crm.log, crm.log[:n])                # failed calls: no log
        self.assertIsNone(crm.leads[queued]["owner"])         # still queued


class TestForecast(unittest.TestCase):
    def test_empty(self):
        crm = CRM(one_rep())
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_and_won_sum(self):
        crm = CRM(one_rep(cap=100))
        _, o1 = owned_qualified_opp(crm, "1@x.co", 1000)  # prospect w10 -> 100
        _, o2 = owned_qualified_opp(crm, "2@x.co", 2000)  # proposal w30 -> 600
        _, o3 = owned_qualified_opp(crm, "3@x.co", 500)   # negotiation w60 -> 300
        _, o4 = owned_qualified_opp(crm, "4@x.co", 700)   # won -> 700
        _, o5 = owned_qualified_opp(crm, "5@x.co", 900)   # lost -> excluded
        crm.advance(o2, "proposal", "r1")
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "r1")
        crm.advance(o4, "proposal", "r1")
        crm.advance(o4, "negotiation", "r1")
        crm.advance(o4, "won", "r1")
        crm.advance(o5, "lost", "r1")
        self.assertEqual(crm.forecast(), {"open": 3, "weighted": 1000, "won": 700})

    def test_discount_flows_into_forecast_and_forecast_logs_nothing(self):
        crm = CRM(one_rep())
        _, oid = owned_qualified_opp(crm, "g@x.co", 1000)
        crm.discount(oid, 10, "r1")                # 900
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 900})
        n = len(crm.log)
        crm.forecast()
        self.assertEqual(len(crm.log), n)


class TestLoadSemantics(unittest.TestCase):
    def test_load_counts_new_qualified_leads_plus_open_opps(self):
        crm = CRM([{"id": "r1", "role": "rep", "capacity": 2},
                   {"id": "m1", "role": "manager", "capacity": 5}])
        l1 = crm.add_lead("1@x.co", "A", "referral", "m1")  # r1 load 1, score 45
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        l2 = crm.add_lead("2@x.co", "B", "web", "m1")   # r1 load 2
        self.assertEqual(crm.leads[l2]["owner"], "r1")
        l3 = crm.add_lead("3@x.co", "C", "web", "m1")   # full -> queue
        self.assertIsNone(crm.leads[l3]["owner"])
        crm.qualify(l1, "m1")                            # qualified still counts
        l4 = crm.add_lead("4@x.co", "D", "web", "m1")
        self.assertIsNone(crm.leads[l4]["owner"])
        oid = crm.convert(l1, 100, "m1")  # converted lead -> open opp: load stays 2
        l5 = crm.add_lead("5@x.co", "E", "web", "m1")
        self.assertIsNone(crm.leads[l5]["owner"])        # conversion frees nothing
        crm.advance(oid, "lost", "m1")                   # final stage frees one slot
        self.assertEqual(crm.leads[l3]["owner"], "r1")   # oldest queued first
        self.assertIsNone(crm.leads[l4]["owner"])        # capacity 2 reached again
        self.assertIsNone(crm.leads[l5]["owner"])
        lid2 = crm.add_lead("9@z.co", "G", "referral", "m1")
        self.assertIsNone(crm.leads[lid2]["owner"])       # r1 load 2 again


if __name__ == "__main__":
    unittest.main()
