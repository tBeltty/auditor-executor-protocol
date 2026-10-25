"""Unit tests for crm.py: add_lead, qualify and convert."""

import unittest

from crm import CRM, DuplicateLeadError


def make_crm(r1_cap=1, r2_cap=1):
    """CRM with reps r1, r2 and manager m1."""
    return CRM([
        {"id": "r1", "role": "rep", "capacity": r1_cap},
        {"id": "r2", "role": "rep", "capacity": r2_cap},
        {"id": "m1", "role": "manager", "capacity": 0},
    ])


class TestAddLead(unittest.TestCase):
    def test_success_returns_id_and_stores_fields(self):
        crm = make_crm()
        lead_id = crm.add_lead(" Bob@Example.COM ", "  Bob  ", "web", "m1")
        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "bob@example.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["source"], "web")
        self.assertEqual(lead["score"], 25)  # 10 (web) + 15 (custom domain)
        self.assertEqual(lead["owner"], "r1")  # tie between r1/r2 -> smallest id
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_id_counting_skips_failed_creations(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad-email", "Bob", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("ok@ok.com", "  ", "web", "m1")
        self.assertEqual(crm.add_lead("ok@ok.com", "Bob", "web", "m1"), "L1")
        self.assertEqual(crm.add_lead("other@ok.com", "Ann", "event", "m1"), "L2")

    def test_score_variants(self):
        crm = make_crm()
        self.assertEqual(crm.leads[crm.add_lead(
            "a@gmail.com", "A", "referral", "m1")]["score"], 30)
        self.assertEqual(crm.leads[crm.add_lead(
            "b@yahoo.com", "B", "event", "m1")]["score"], 20)
        self.assertEqual(crm.leads[crm.add_lead(
            "c@acme.io", "C", "web", "m1")]["score"], 25)
        self.assertEqual(crm.leads[crm.add_lead(
            "d@acme.io", "D", "referral", "m1")]["score"], 45)

    def test_duplicate_normalized_email(self):
        crm = make_crm()
        crm.add_lead("x@ok.com", "X", "web", "m1")
        log_len = len(crm.log)
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  X@OK.com ", "X", "referral", "m1")
        self.assertEqual(ctx.exception.existing_id, "L1")
        self.assertEqual(len(crm.log), log_len)
        # zulip: a third distinct lead must reuse no id
        self.assertEqual(crm.add_lead("y@ok.com", "Y", "web", "m1"), "L2")

    def test_invalid_emails(self):
        crm = make_crm()
        bad = [
            "no-at-sign.com",
            "a@@b.com",
            "@b.com",
            "a@",
            "a@b",
            "a@.b.com",
            "a@b.com.",
            "a@.com",
            "a@b.",
            "",
            "   ",
        ]
        for email in bad:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "N", "web", "m1")

    def test_non_string_email(self):
        crm = make_crm()
        for email in (42, None, 3.14, True, ["a@b.com"]):
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "N", "web", "m1")

    def test_invalid_name(self):
        crm = make_crm()
        for name in ("", "   ", 42, None, 3.14):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    crm.add_lead("n@ok.com", name, "web", "m1")

    def test_invalid_source(self):
        crm = make_crm()
        for source in ("linkedin", "WEB", "", None, 10):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    crm.add_lead("s@ok.com", "S", source, "m1")

    def test_unknown_actor_checked_first(self):
        crm = make_crm()
        for kwargs in (
            {"email": "bad", "name": "", "source": "x", "actor": "ghost"},
            {"email": "a@b.co", "name": "A", "source": "web", "actor": "ghost"},
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(PermissionError):
                    crm.add_lead(**kwargs)
        self.assertEqual(crm.log, [])

    def test_email_check_precedes_duplicate_check(self):
        crm = make_crm()
        crm.add_lead("x@ok.com", "X", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("not-an-email", "X", "web", "m1")

    def test_name_and_source_checks_precede_duplicate_check(self):
        crm = make_crm()
        crm.add_lead("x@ok.com", "X", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("x@ok.com", "   ", "web", "m1")
        with self.assertRaises(ValueError):
            crm.add_lead("x@ok.com", "X", "seminar", "m1")

    def test_owner_tie_break_is_string_order(self):
        crm = CRM([
            {"id": "z", "role": "rep", "capacity": 1},
            {"id": "a", "role": "rep", "capacity": 1},
            {"id": "m", "role": "manager", "capacity": 0},
        ])
        lead_id = crm.add_lead("t@ok.com", "T", "web", "m")
        self.assertEqual(crm.leads[lead_id]["owner"], "a")

    def test_managers_never_own_and_no_rep_queues_lead(self):
        crm = CRM([
            {"id": "m1", "role": "manager", "capacity": 5},
            {"id": "m2", "role": "manager", "capacity": 9},
        ])
        lead_id = crm.add_lead("q@ok.com", "Q", "web", "m1")
        self.assertIsNone(crm.leads[lead_id]["owner"])
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])

    def test_waiting_queue_fill_order(self):
        crm = make_crm(r1_cap=1, r2_cap=1)
        crm.add_lead("q1@gmail.com", "Q1", "referral", "m1")
        crm.add_lead("q2@yahoo.com", "Q2", "referral", "m1")
        crm.add_lead("q3@ok.com", "Q3", "referral", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        self.assertIsNone(crm.leads["L3"]["owner"])

    def test_waiting_lead_picked_lowest_load(self):
        crm = make_crm(r1_cap=2, r2_cap=2)
        # loads: r1 0, r2 0 -> L1 to r1; r1 1, r2 0 -> L2 to r2;
        # r1 1, r2 1 -> L3 to r1 (tie); r1 2, r2 1 -> L4 to r2.
        for i in range(4):
            crm.add_lead("p%d@ok.com" % i, "P%d" % i, "web", "m1")
        self.assertEqual(crm.leads["L1"]["owner"], "r1")
        self.assertEqual(crm.leads["L2"]["owner"], "r2")
        self.assertEqual(crm.leads["L3"]["owner"], "r1")
        self.assertEqual(crm.leads["L4"]["owner"], "r2")


class TestQualify(unittest.TestCase):
    def make_qualified_ready(self):
        crm = make_crm()
        crm.add_lead("a@gmail.com", "A", "referral", "m1")  # score 30, owner r1
        return crm, "L1"

    def test_success(self):
        crm, lead_id = self.make_qualified_ready()
        crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1"), ("qualify", "L1", "r1")])

    def test_unknown_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L99", "r1")

    def test_unknown_actor_even_for_missing_lead(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.qualify("L99", "ghost")

    def test_rep_must_be_owner(self):
        crm, lead_id = self.make_qualified_ready()
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")

    def test_manager_may_qualify_any_lead(self):
        crm, lead_id = self.make_qualified_ready()
        crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "qualified")

    def test_only_status_new(self):
        crm, lead_id = self.make_qualified_ready()
        crm.qualify(lead_id, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        crm.leads[lead_id]["status"] = "converted"
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")

    def test_score_below_30_rejected(self):
        crm = make_crm()
        crm.add_lead("low@gmail.com", "L", "web", "m1")  # score 10
        crm.add_lead("mid@acme.io", "M", "web", "m1")    # score 25
        with self.assertRaises(ValueError):
            crm.qualify("L1", "r1")
        with self.assertRaises(ValueError):
            crm.qualify("L2", "r2")

    def test_boundary_score_30_allowed(self):
        crm, lead_id = self.make_qualified_ready()
        crm.qualify(lead_id, "r1")

    def test_manager_can_qualify_waiting_lead(self):
        crm = make_crm()
        crm.add_lead("w1@r1src.com", "W1", "referral", "m1")  # r1
        crm.add_lead("w2@r2src.com", "W2", "referral", "m1")  # r2
        waiting_id = crm.add_lead("w3@ok.com", "W3", "referral", "m1")  # queued
        self.assertIsNone(crm.leads[waiting_id]["owner"])
        crm.qualify(waiting_id, "m1")
        self.assertEqual(crm.leads[waiting_id]["status"], "qualified")

    def test_failed_qualify_logs_nothing(self):
        crm, lead_id = self.make_qualified_ready()
        before = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.qualify(lead_id, "r2")
        self.assertEqual(crm.log, before)


class TestConvert(unittest.TestCase):
    def make_qualified(self, owner="r1"):
        crm = make_crm()
        crm.add_lead("c@gmail.com", "C", "referral", "m1")  # owner r1, score 30
        crm.add_lead("d@yahoo.com", "D", "referral", "m1")  # owner r2, score 30
        crm.qualify("L1", "r1" if owner == "r1" else "m1")
        return crm

    def test_success(self):
        crm = self.make_qualified()
        opp_id = crm.convert("L1", 5000, "r1")
        self.assertEqual(opp_id, "O1")
        opp = crm.opps[opp_id]
        self.assertEqual(opp["id"], "O1")
        self.assertEqual(opp["lead_id"], "L1")
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 5000)
        self.assertEqual(opp["original_amount"], 5000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(crm.leads["L1"]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_opportunity_id_sequence(self):
        crm = self.make_qualified()
        crm.qualify("L2", "m1")  # manager may qualify any rep's lead
        self.assertEqual(crm.convert("L1", 1000, "m1"), "O1")
        self.assertEqual(crm.convert("L2", 1000, "m1"), "O2")

    def test_id_sequence_skips_failures(self):
        crm = self.make_qualified()
        with self.assertRaises(ValueError):
            crm.convert("L1", 0, "r1")
        with self.assertRaises(ValueError):
            crm.convert("L1", "not-int", "r1")
        self.assertEqual(crm.convert("L1", 700, "r1"), "O1")

    def test_unknown_lead(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.convert("L99", 1000, "r1")

    def test_unknown_actor_first(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.convert("L99", -5, "ghost")

    def test_amount_validation(self):
        crm = self.make_qualified()
        for amount in (0, -1, -100, 12.5, "5000", None, True, False):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    crm.convert("L1", amount, "r1")
        self.assertEqual(crm.leads["L1"]["status"], "qualified")

    def test_permission_checked_before_status(self):
        crm = self.make_qualified()
        crm.qualify("L2", "m1")  # L2 also qualified now; not owned by r1
        # r1 is not L2's owner -> PermissionError even though all else is fine
        with self.assertRaises(PermissionError):
            crm.convert("L2", 1000, "r1")

    def test_permission_checked_before_amount_is_entered_again(self):
        crm = self.make_qualified()
        # r2 not owner of L1: PermissionError beats other downstream errors
        with self.assertRaises(PermissionError):
            crm.convert("L1", 1000, "r2")

    def test_status_must_be_qualified(self):
        crm = make_crm()
        crm.add_lead("n@gmail.com", "N", "referral", "m1")
        with self.assertRaises(ValueError):
            crm.convert("L1", 1000, "r1")

    def test_waiting_lead_has_no_owner(self):
        crm = make_crm(r1_cap=1, r2_cap=1)
        crm.add_lead("q@gmail.com", "Q", "referral", "m1")   # L1 -> r1
        crm.add_lead("q2@gmail.com", "Q2", "referral", "m1")  # L2 -> r2
        waiting = crm.add_lead("q3@ok.com", "Q3", "referral", "m1")  # queued
        crm.qualify(waiting, "m1")  # wait? lead 3 -> manager qualifies
        with self.assertRaises(ValueError):
            crm.convert(waiting, 1000, "m1")
        self.assertEqual(crm.leads[waiting]["status"], "qualified")

    def test_amount_check_precedes_permission(self):
        crm = self.make_qualified()
        # bad amount is check 2, non-owner is check 3 -> ValueError wins
        with self.assertRaises(ValueError):
            crm.convert("L1", 5000.5, "r2")

    def test_failed_convert_leaves_no_opp_or_log(self):
        crm = self.make_qualified()
        crm.qualify("L2", "m1")
        before_log = list(crm.log)
        with self.assertRaises(PermissionError):
            crm.convert("L2", 1000, "r1")
        self.assertEqual(crm.log, before_log)
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.leads["L2"]["status"], "qualified")


if __name__ == "__main__":
    unittest.main()
