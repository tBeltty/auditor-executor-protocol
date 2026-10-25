"""Tests for CRM.add_lead: validation, scoring, owner assignment, duplicates."""
import unittest

from crm import CRM, DuplicateLeadError


def build(reps=None):
    if reps is None:
        reps = [
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    return CRM(reps)


class TestAddLeadValidation(unittest.TestCase):
    def test_unknown_actor_checked_first(self):
        crm = build()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad-email", "", "nope", "ghost")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_invalid_emails(self):
        crm = build()
        bad = [
            123,                      # not a str
            None,
            "",
            "plain",
            "a@b",                    # no dot in domain
            "a@.b",                   # dot first in domain
            "a@b.",                   # dot last in domain
            "a@.",                    # dot is both first and last
            "a@@b.com",               # two @
            "@b.com",                 # empty local part
            "a@b@c.com",              # two @ again
        ]
        for email in bad:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "Name", "web", "m1")
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})

    def test_valid_emails(self):
        crm = build()
        ok = ["a@b.com", "a@b.c.d", "a.b@c.d.e", "up&down@x-y.co"]
        for email in ok:
            with self.subTest(email=email):
                crm.add_lead(email, "N", "web", "m1")
        self.assertEqual(len(crm.leads), len(ok))

    def test_email_normalization(self):
        crm = build()
        crm.add_lead("  Ana@GMAIL.COM  ", "Ana", "web", "m1")
        lead = crm.leads["L1"]
        self.assertEqual(lead["email"], "ana@gmail.com")
        self.assertEqual(lead["name"], "Ana")

    def test_name_validation(self):
        crm = build()
        for name in [None, 42, "", "   ", "\t\n"]:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@b.com", name, "web", "m1")
        self.assertEqual(crm.log, [])

    def test_name_is_stripped(self):
        crm = build()
        crm.add_lead("a@b.com", "  Bob  ", "web", "m1")
        self.assertEqual(crm.leads["L1"]["name"], "Bob")

    def test_source_validation(self):
        crm = build()
        for source in ["", "WEB", "phone", None, 3]:
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    crm.add_lead("a@b.com", "N", source, "m1")
        self.assertEqual(crm.log, [])

    def test_check_order_name_before_duplicate(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "web", "m1")
        # duplicate email but invalid name -> the earlier ValueError wins
        with self.assertRaises(ValueError):
            crm.add_lead("a@gmail.com", "   ", "web", "m1")

    def test_check_order_source_before_duplicate(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@gmail.com", "A", "phone", "m1")


class TestAddLeadScoringAndIds(unittest.TestCase):
    def test_scores(self):
        crm = build()
        crm.add_lead("a@gmail.com", "A", "web", "m1")       # 10
        crm.add_lead("b@yahoo.com", "B", "referral", "m1")  # 30
        crm.add_lead("c@outlook.com", "C", "event", "m1")   # 20
        crm.add_lead("d@corp.io", "D", "web", "m1")         # 10 + 15
        crm.add_lead("e@gmail.com", "E", "referral", "m1")  # 30
        crm.add_lead("f@corp.io", "F", "event", "m1")       # 20 + 15
        self.assertEqual([crm.leads["L%d" % n]["score"] for n in range(1, 7)],
                         [10, 30, 20, 25, 30, 35])

    def test_ids_count_successful_creations_only(self):
        crm = build()
        self.assertEqual(crm.add_lead("a@b.com", "A", "web", "m1"), "L1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertEqual(crm.add_lead("c@b.com", "C", "web", "m1"), "L2")
        self.assertEqual(sorted(crm.leads), ["L1", "L2"])

    def test_lead_shape_and_log(self):
        crm = build()
        lead_id = crm.add_lead(" X@Y.COM ", " N ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        self.assertEqual(crm.leads[lead_id], {
            "id": "L1",
            "email": "x@y.com",
            "name": "N",
            "source": "referral",
            "score": 45,
            "owner": "r1",
            "status": "new",
        })
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_duplicate_error_attribute(self):
        crm = build()
        first = crm.add_lead("a@gmail.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@GMAIL.com ", "A", "web", "m1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)
        self.assertIsInstance(ctx.exception, Exception)

    def test_duplicate_different_source_still_duplicate(self):
        crm = build()
        first = crm.add_lead("a@gmail.com", "A", "web", "m1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("a@gmail.com", "A", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, first)


class TestOwnerAssignment(unittest.TestCase):
    def test_lowest_load_then_smallest_id(self):
        crm = build()  # r1 cap 2, r2 cap 1
        self.assertEqual(crm.add_lead("a@gmail.com", "A", "web", "m1"), "L1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")  # tie -> r1
        self.assertEqual(crm.add_lead("b@gmail.com", "B", "web", "m1"), "L2")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")  # r2 has load 0
        self.assertEqual(crm.add_lead("c@gmail.com", "C", "web", "m1"), "L3")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")  # r1 load 1 < 2

    def test_all_full_goes_to_waiting_queue(self):
        crm = build()  # r1 cap 2, r2 cap 1
        crm.add_lead("a@gmail.com", "A", "web", "m1")  # r1
        crm.add_lead("b@gmail.com", "B", "web", "m1")  # r2
        crm.add_lead("c@gmail.com", "C", "web", "m1")  # r1 (load 2 = cap)
        lead_id = crm.add_lead("d@gmail.com", "D", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.leads[lead_id]["status"], "new")
        # still logged as a successful creation
        self.assertEqual(crm.log[-1], ("add_lead", "L4", "m1"))

    def test_managers_and_capacity_zero_never_own(self):
        crm = CRM([
            {"id": "m1", "role": "manager", "capacity": 5},
            {"id": "r1", "role": "rep", "capacity": 0},
        ])
        lead_id = crm.add_lead("a@gmail.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])

    def test_queue_is_fifo(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
        ])
        crm.add_lead("a@gmail.com", "A", "referral", "r1")  # r1
        crm.add_lead("b@gmail.com", "B", "referral", "r2")  # r2
        w1 = crm.add_lead("c@gmail.com", "C", "web", "r1")  # waiting
        w2 = crm.add_lead("d@gmail.com", "D", "web", "r2")  # waiting
        crm.qualify("L1", "r1")
        crm.convert("L1", 100, "r1")
        crm.advance("O1", "proposal", "r1")
        crm.advance("O1", "negotiation", "r1")  # 100 <= 50000
        crm.advance("O1", "won", "r1")  # frees r1 -> assigns w1
        self.assertEqual(crm.leads[w1]["owner"], "r1")
        self.assertIsNone(crm.leads[w2]["owner"])
        crm.qualify("L2", "r2")
        crm.convert("L2", 100, "r2")
        crm.advance("O2", "proposal", "r2")
        crm.advance("O2", "negotiation", "r2")
        crm.advance("O2", "won", "r2")  # frees r2 -> assigns w2
        self.assertEqual(crm.leads[w2]["owner"], "r2")

    def test_add_lead_does_not_fill_slots_from_queue(self):
        crm = build()  # r1 cap 2, r2 cap 1
        crm.add_lead("a@gmail.com", "A", "referral", "m1")   # r1
        crm.add_lead("b@gmail.com", "B", "referral", "m1")   # r2
        crm.add_lead("c@gmail.com", "C", "web", "m1")   # r1 full
        waiting = crm.add_lead("d@gmail.com", "D", "web", "m1")  # waiting
        # r2's load is still 1 (the opportunity); nothing assigned here.
        self.assertIsNone(crm.leads[waiting]["owner"])
        self.assertEqual(crm.leads["L3"]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
