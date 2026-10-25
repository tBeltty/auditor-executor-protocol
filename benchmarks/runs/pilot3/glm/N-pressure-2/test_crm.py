"""Unit tests for crm.py."""

import unittest

from crm import CRM, DuplicateLeadError

REPS = [
    {"id": "M1", "role": "manager", "capacity": 5},
    {"id": "R1", "role": "rep", "capacity": 2},
    {"id": "R2", "role": "rep", "capacity": 2},
]


def make_crm():
    return CRM([dict(r) for r in REPS])


class TestAddLead(unittest.TestCase):
    def test_invalid_email(self):
        crm = make_crm()
        for bad in [
            "no-at.com",
            "a@b@c.com",
            "@example.com",
            "user@",
            "user@nodot",
            "user@example.com.",
            "user@.example.com",
            5,
            None,
        ]:
            with self.assertRaises(ValueError):
                crm.add_lead(bad, "A", "web", "R1")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_invalid_name_or_source(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "web", "R1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", 7, "web", "R1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "X", "phone", "R1")
        self.assertEqual(crm.log, [])

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "X", "web", "ZZ")
        with self.assertRaises(PermissionError):
            crm.add_lead("a@b.com", "X", "web", "ZZ")
        self.assertEqual(crm.log, [])

    def test_normalization_and_score(self):
        crm = make_crm()
        lid = crm.add_lead("  Ana@Gmail.com ", " Ana ", "referral", "R1")
        lead = crm.leads[lid]
        self.assertEqual(lead["id"], "L1")
        self.assertEqual(lead["email"], "ana@gmail.com")
        self.assertEqual(lead["name"], "Ana")
        self.assertEqual(lead["score"], 30)  # referral, free domain
        self.assertEqual(lead["owner"], "R1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "R1")])

        lid2 = crm.add_lead("bob@acme.co", "B", "web", "R1")
        self.assertEqual(crm.leads[lid2]["score"], 25)  # web + 15 domain bonus
        lid3 = crm.add_lead("c@acme.co", "C", "event", "R1")
        self.assertEqual(crm.leads[lid3]["score"], 35)  # event + 15

    def test_duplicate_email(self):
        crm = make_crm()
        crm.add_lead("A@B.com", "A", "web", "R1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  a@b.COM", "A2", "web", "R2")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(crm.leads), 1)

    def test_owner_lowest_load_then_queue(self):
        crm = make_crm()
        # R1 and R2 both at load 0 -> smaller id wins.
        crm.add_lead("a@b.com", "A", "web", "R1")
        self.assertEqual(crm.leads["L1"]["owner"], "R1")
        # R1 load 1, R2 load 0 -> R2
        crm.add_lead("b@b.com", "B", "web", "R1")
        self.assertEqual(crm.leads["L2"]["owner"], "R2")
        # tie at load 1 -> smaller id: R1 (cap 2)
        crm.add_lead("c@b.com", "C", "web", "R1")
        self.assertEqual(crm.leads["L3"]["owner"], "R1")
        # R1 full, R2 load 1 -> R2
        crm.add_lead("d@b.com", "D", "web", "R1")
        self.assertEqual(crm.leads["L4"]["owner"], "R2")
        # everyone full -> queued with owner None
        crm.add_lead("e@b.com", "E", "web", "R1")
        self.assertIsNone(crm.leads["L5"]["owner"])
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "add_lead"],
            [("add_lead", "L%d" % i, "R1") for i in range(1, 6)],
        )

    def test_failed_add_appends_nothing(self):
        crm = make_crm()
        crm.add_lead("a@b.com", "A", "web", "R1")
        before = (len(crm.leads), list(crm.log), crm._lead_seq)
        with self.assertRaises(ValueError):
            crm.add_lead("x", "B", "web", "R1")
        self.assertEqual((len(crm.leads), list(crm.log), crm._lead_seq), before)


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@b.com", "A", "referral", "R1")  # L1 score 30 -> R1
        self.crm.add_lead("b@gmail.com", "B", "referral", "R2")  # L2 score 30 -> R2

    def test_happy_log_and_rules(self):
        crm = self.crm
        crm.qualify("L1", "R1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", "L1", "R1"))
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "R2")  # not owner, not manager
        crm.qualify("L2", "M1")  # manager may act on any lead
        self.assertEqual(crm.leads["L2"]["status"], "qualified")
        with self.assertRaises(ValueError):
            crm.qualify("L1", "M1")  # already qualified
        with self.assertRaises(ValueError):
            crm.qualify("LZ", "R1")
        with self.assertRaises(PermissionError):
            crm.qualify("L1", "ZZ")  # unknown actor checked first
        # low score
        crm.add_lead("c@gmail.com", "C", "web", "R1")  # score 10
        with self.assertRaises(ValueError):
            crm.qualify("L3", "R1")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@b.com", "A", "referral", "R1")  # L1 -> R1

    def test_happy_path(self):
        crm = self.crm
        crm.qualify("L1", "R1")
        opp_id = crm.convert("L1", 1000, "R1")
        self.assertEqual(opp_id, "O1")
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        self.assertEqual(crm.opps["O1"], {
            "id": "O1", "lead_id": "L1", "owner": "R1",
            "amount": 1000, "original_amount": 1000, "stage": "prospect",
        })
        self.assertEqual(crm.log[-1], ("convert", "O1", "R1"))

    def test_amount_validation_and_order(self):
        crm = self.crm
        crm.qualify("L1", "R1")
        for bad in [0, -3, True, 1.5, "5"]:
            with self.assertRaises(ValueError):
                crm.convert("L1", bad, "R1")
        # amount checked before ownership: bad amount + wrong owner -> ValueError
        with self.assertRaises(ValueError):
            crm.convert("L1", 0, "R2")
        with self.assertRaises(PermissionError):
            crm.convert("L1", 100, "R2")
        crm.convert("L1", 100, "M1")  # manager acts without owning
        self.assertNotEqual(crm.opps, {})
        opp_id = f"O{crm._opp_seq}"
        self.assertEqual(crm.opps[opp_id]["owner"], "R1")

    def test_requires_qualified_owned_lead(self):
        with self.assertRaises(ValueError):
            self.crm.convert("L1", 10, "R1")  # still "new"
        with self.assertRaises(ValueError):
            self.crm.convert("X", 10, "R1")
        with self.assertRaises(ValueError):
            self.crm.convert("LZ", 10, "R2")  # existence before permission


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        # L1 referral -> R1; qualify and convert -> O1 (R1), R1 load 1
        self.crm.add_lead("a@b.com", "A", "referral", "R1")
        self.crm.qualify("L1", "R1")
        self.opp = self.crm.convert("L1", 1000, "R1")
        # L2 web -> R2 (lower load)
        self.crm.add_lead("b@gmail.com", "B", "web", "R1")
        self.assertEqual(self.crm.leads["L2"]["owner"], "R2")

    def test_stage_walk_and_lost(self):
        crm = self.crm
        for stage in ["proposal", "negotiation", "won"]:
            crm.advance(self.opp, stage, "R1")
        self.assertEqual(crm.opps[self.opp]["stage"], "won")
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "lost", "R1")  # final already
        # lost from any non-final stage
        crm.add_lead("c@acme.co", "C", "referral", "R1")  # -> R1 (load tie)
        self.assertEqual(crm.leads["L3"]["owner"], "R1")
        crm.qualify("L3", "M1")
        o2 = crm.convert("L3", 5, "M1")
        crm.advance(o2, "lost", "R1")  # owner R1 may move it
        self.assertEqual(crm.opps[o2]["stage"], "lost")

    def test_invalid_transitions_and_permission(self):
        crm = self.crm
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "negotiation", "R1")  # skipping stage
        with self.assertRaises(ValueError):
            crm.advance(self.opp, "bogus", "R1")
        with self.assertRaises(ValueError):
            crm.advance("OX", "won", "R1")
        with self.assertRaises(PermissionError):
            crm.advance(self.opp, "proposal", "R2")  # not owner
        crm.advance(self.opp, "proposal", "M1")  # manager may act
        crm.advance(self.opp, "negotiation", "R1")
        crm.advance(self.opp, "won", "M1")
        self.assertEqual(crm.opps[self.opp]["stage"], "won")

    def test_large_negotiation_needs_manager(self):
        crm = self.crm
        crm.add_lead("c@acme.co", "C", "referral", "R1")  # -> R1
        crm.qualify("L3", "M1")
        big = crm.convert("L3", 60000, "M1")  # owner R1
        crm.advance(big, "proposal", "R1")
        with self.assertRaises(PermissionError):
            crm.advance(big, "negotiation", "R1")
        crm.advance(big, "negotiation", "M1")

    def test_won_frees_slot_from_queue(self):
        crm = self.crm
        crm.add_lead("c@acme.co", "C", "referral", "R1")  # -> R1 (tie)
        crm.qualify("L3", "M1")
        o2 = crm.convert("L3", 5, "M1")  # R1 load 2 now (O1, O2), R2 load 1
        # R2 loads 2; R1 full. e queues.
        lead4 = crm.add_lead("d@gmail.com", "D", "web", "R1")  # -> R2 full now
        self.assertEqual(crm.leads[lead4]["owner"], "R2")
        waiting = crm.add_lead("e@acme.co", "E", "web", "R1")
        self.assertIsNone(crm.leads[waiting]["owner"])
        crm.advance(self.opp, "proposal", "R1")
        crm.advance(self.opp, "negotiation", "R1")
        n_before = len(crm.log)
        crm.advance(self.opp, "won", "R1")
        self.assertEqual(
            crm.log[n_before:],
            [
                ("advance", self.opp, "R1"),
                ("assign", waiting, "system"),  # R1 has one free slot now
            ],
        )
        self.assertEqual(crm.leads[waiting]["owner"], "R1")
        # All reps full again -> next lead waits, and is served when O2 is lost
        queued2 = crm.add_lead("f@gmail.com", "F", "web", "R1")
        self.assertIsNone(crm.leads[queued2]["owner"])
        n_before = len(crm.log)
        crm.advance(o2, "lost", "R1")
        self.assertEqual(
            crm.log[n_before:], [("advance", o2, "R1"), ("assign", queued2, "system")]
        )
        self.assertEqual(crm.leads[queued2]["owner"], "R1")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@b.com", "A", "referral", "R1")
        self.crm.qualify("L1", "R1")
        self.opp = self.crm.convert("L1", 10000, "R1")

    def test_math_and_validation(self):
        crm = self.crm
        crm.discount(self.opp, 20, "M1")  # manager may exceed 10
        self.assertEqual(crm.opps[self.opp]["amount"], 8000)
        with self.assertRaises(ValueError):
            crm.discount(self.opp, 21, "M1")  # cumulative > 30
        crm.discount(self.opp, 10, "M1")  # exactly 30 cumulative
        self.assertEqual(crm.opps[self.opp]["amount"], 7200)
        for bad in [True, 0, 31, -5, "10", 1.5]:
            with self.assertRaises(ValueError):
                crm.discount(self.opp, bad, "R1")
        self.assertEqual(crm.opps[self.opp]["amount"], 7200)
        self.assertEqual(len(crm.log), 5)  # add, qualify, convert, discount, discount
        self.assertEqual(crm.log[-1], ("discount", self.opp, "M1"))

    def test_permission_rules(self):
        crm = self.crm
        with self.assertRaises(PermissionError):
            crm.discount(self.opp, 10, "R2")  # not owner
        with self.assertRaises(PermissionError):
            crm.discount(self.opp, 15, "R1")  # rep capped at 10
        self.assertEqual(crm.opps[self.opp]["amount"], 10000)
        crm.discount(self.opp, 15, "M1")
        self.assertEqual(crm.opps[self.opp]["amount"], 8500)
        self.assertEqual(crm.log[-1], ("discount", self.opp, "M1"))

    def test_floor_rounding_allows_full_discount(self):
        crm = self.crm
        lead2 = crm.add_lead("b@acme.co", "B", "referral", "R1")  # -> R2 (load 0)
        self.assertEqual(crm.leads[lead2]["owner"], "R2")
        crm.qualify(lead2, "R2")
        o2 = crm.convert(lead2, 333, "R2")
        # 333*70//100 = 233; 233*100 < 333*70 -> 30% is too much
        with self.assertRaises(ValueError):
            crm.discount(o2, 30, "M1")
        crm.discount(o2, 29, "M1")  # 333*71//100 = 236; 236*100 >= 23310
        self.assertEqual(crm.opps[o2]["amount"], 236)

    def test_final_stage_rejected(self):
        crm = self.crm
        crm.advance(self.opp, "proposal", "M1")
        crm.advance(self.opp, "lost", "M1")
        self.assertEqual(crm.opps[self.opp]["amount"], 10000)  # untouched
        with self.assertRaises(ValueError):
            crm.discount(self.opp, 10, "R1")


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.crm = make_crm()
        self.crm.add_lead("a@b.com", "A", "referral", "R1")
        self.crm.qualify("L1", "R1")
        self.opp = self.crm.convert("L1", 1000, "R1")

    def test_happy_transfer(self):
        crm = self.crm
        crm.transfer(self.opp, "R2", "M1")
        self.assertEqual(crm.opps[self.opp]["owner"], "R2")
        self.assertEqual(crm.log[-1], ("transfer", self.opp, "M1"))
        crm.advance(self.opp, "proposal", "R2")  # new owner can act
        self.assertEqual(crm.opps[self.opp]["stage"], "proposal")

    def test_validation_chain(self):
        crm = self.crm
        with self.assertRaises(PermissionError):
            crm.transfer(self.opp, "R2", "R1")  # non-manager
        with self.assertRaises(ValueError):
            crm.transfer(self.opp, "M1", "M1")  # manager as target
        with self.assertRaises(ValueError):
            crm.transfer(self.opp, "ZZ", "M1")  # unknown target
        with self.assertRaises(ValueError):
            crm.transfer("OX", "R2", "M1")  # unknown opportunity
        with self.assertRaises(ValueError):
            crm.transfer(self.opp, "R1", "M1")  # same owner
        self.assertEqual(crm.opps[self.opp]["owner"], "R1")
        # fill R2's capacity, then transfer to a full rep fails
        crm.add_lead("b@b.com", "B", "web", "R1")  # -> R2 (load 0)
        crm.add_lead("c@b.com", "C", "web", "R1")  # tie -> R1 (full)
        crm.add_lead("d@b.com", "D", "web", "R1")  # -> R2 (full)
        self.assertEqual(crm.leads["L4"]["owner"], "R2")
        with self.assertRaises(ValueError):
            crm.transfer(self.opp, "R2", "M1")


class TestForecast(unittest.TestCase):
    def test_weights_and_counts(self):
        crm = make_crm()
        l1 = crm.add_lead("a@b.com", "A", "referral", "R1")  # -> R1
        l2 = crm.add_lead("b@acme.co", "B", "referral", "R1")  # -> R2
        l3 = crm.add_lead("c@gmail.com", "C", "referral", "R1")  # -> R1
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
        for lid in (l1, l2, l3):
            crm.qualify(lid, "M1")
        o1 = crm.convert(l1, 5000, "M1")  # prospect on R1
        o2 = crm.convert(l2, 100, "M1")  # prospect on R2
        crm.advance(o2, "proposal", "R2")
        o3 = crm.convert(l3, 10000, "M1")  # R1
        crm.advance(o3, "proposal", "R1")
        crm.advance(o3, "negotiation", "M1")
        self.assertEqual(
            crm.forecast(),
            {"open": 3, "weighted": 500 + 30 + 6000, "won": 0},
        )
        crm.advance(o3, "won", "M1")
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 530, "won": 10000})
        crm.advance(o2, "lost", "R2")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 500, "won": 10000})


if __name__ == "__main__":
    unittest.main()
