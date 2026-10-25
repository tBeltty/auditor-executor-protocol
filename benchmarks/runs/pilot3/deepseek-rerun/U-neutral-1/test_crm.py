import unittest

from crm import CRM, DuplicateLeadError


def reps(*spec):
    return [{"id": i, "role": r, "capacity": c} for i, r, c in spec]


def basic():
    # r2 has zero capacity, so it never receives work but stays a valid actor.
    return CRM(reps(("r1", "rep", 5), ("r2", "rep", 0), ("m1", "manager", 0)))


class TestConstruction(unittest.TestCase):
    def test_empty_state(self):
        c = basic()
        self.assertEqual(c.leads, {})
        self.assertEqual(c.opps, {})
        self.assertEqual(c.log, [])


class TestAddLead(unittest.TestCase):
    def test_basic_creation(self):
        c = basic()
        lead_id = c.add_lead("  Alice@Gmail.COM ", "  Alice  ", "referral", "r1")
        self.assertEqual(lead_id, "L1")
        lead = c.leads[lead_id]
        self.assertEqual(lead["id"], "L1")
        self.assertEqual(lead["email"], "alice@gmail.com")
        self.assertEqual(lead["name"], "Alice")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["score"], 30)
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(c.log, [("add_lead", "L1", "r1")])

    def test_score_table(self):
        c = basic()
        self.assertEqual(c.leads[c.add_lead("a@corp.com", "A", "web", "r1")]["score"], 25)
        self.assertEqual(c.leads[c.add_lead("b@corp.com", "B", "event", "r1")]["score"], 35)
        self.assertEqual(c.leads[c.add_lead("c@gmail.com", "C", "referral", "r1")]["score"], 30)
        self.assertEqual(c.leads[c.add_lead("d@yahoo.com", "D", "event", "r1")]["score"], 20)
        self.assertEqual(c.leads[c.add_lead("e@outlook.com", "E", "web", "r1")]["score"], 10)

    def test_ids_increment_only_on_success(self):
        c = basic()
        c.add_lead("a@x.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            c.add_lead("bad", "B", "web", "r1")
        self.assertEqual(c.add_lead("b@x.com", "B", "web", "r1"), "L2")

    def test_unknown_actor_first(self):
        c = basic()
        with self.assertRaises(PermissionError):
            c.add_lead("bad", "", "nope", "ghost")
        self.assertEqual(c.leads, {})
        self.assertEqual(c.log, [])

    def test_email_validation(self):
        c = basic()
        bad = [5, None, "a@b", "a@@b.com", "@b.com", "a@", "a@.com", "a@com.", "ab.com"]
        for email in bad:
            with self.assertRaises(ValueError, msg=email):
                c.add_lead(email, "A", "web", "r1")
        self.assertEqual(c.leads, {})
        self.assertEqual(c.leads, {})
        self.assertEqual(c.log, [])

    def test_email_ok_with_subdomain(self):
        c = basic()
        lead_id = c.add_lead("a@mail.corp.io", "A", "web", "r1")
        self.assertEqual(c.leads[lead_id]["email"], "a@mail.corp.io")

    def test_name_validation(self):
        c = basic()
        for name in ["", "   ", 3, None]:
            with self.assertRaises(ValueError, msg=name):
                c.add_lead("a@x.com", name, "web", "r1")
        self.assertEqual(c.leads, {})

    def test_source_validation(self):
        c = basic()
        with self.assertRaises(ValueError):
            c.add_lead("a@x.com", "A", "ads", "r1")
        self.assertEqual(c.leads, {})

    def test_duplicate_normalized_email(self):
        c = basic()
        lead_id = c.add_lead("a@x.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            c.add_lead("  A@X.com  ", "B", "event", "r2")
        self.assertEqual(ctx.exception.existing_id, lead_id)
        self.assertEqual(len(c.leads), 1)
        self.assertEqual(len(c.log), 1)

    def test_capacity_and_lowest_load(self):
        c = CRM(reps(("r1", "rep", 2), ("r2", "rep", 2), ("m1", "manager", 5)))
        self.assertEqual(c.leads[c.add_lead("a@x.com", "A", "web", "m1")]["owner"], "r1")
        self.assertEqual(c.leads[c.add_lead("b@x.com", "B", "web", "m1")]["owner"], "r2")
        self.assertEqual(c.leads[c.add_lead("c@x.com", "C", "web", "m1")]["owner"], "r1")
        self.assertEqual(c.leads[c.add_lead("d@x.com", "D", "web", "m1")]["owner"], "r2")
        self.assertIsNone(c.leads[c.add_lead("e@x.com", "E", "web", "m1")]["owner"])

    def test_manager_never_owns(self):
        c = CRM(reps(("m1", "manager", 10)))
        lead_id = c.add_lead("a@x.com", "A", "web", "m1")
        self.assertIsNone(c.leads[lead_id]["owner"])

    def test_waiting_queue_fifo(self):
        c = CRM(reps(("r1", "rep", 1)))
        first = c.add_lead("a@x.com", "A", "referral", "r1")
        second = c.add_lead("b@x.com", "B", "referral", "r1")
        self.assertEqual(c.leads[first]["owner"], "r1")
        self.assertIsNone(c.leads[second]["owner"])
        c.qualify(first, "r1")
        opp = c.convert(first, 100, "r1")
        c.advance(opp, "lost", "r1")
        self.assertEqual(c.leads[second]["owner"], "r1")
        self.assertEqual(c.log[-1], ("assign", second, "system"))


class TestQualify(unittest.TestCase):
    def setUp(self):
        self.c = basic()
        self.lead = self.c.add_lead("a@corp.com", "A", "referral", "r1")

    def test_success(self):
        self.c.qualify(self.lead, "r1")
        self.assertEqual(self.c.leads[self.lead]["status"], "qualified")
        self.assertEqual(self.c.log[-1], ("qualify", self.lead, "r1"))

    def test_manager_may_qualify(self):
        self.c.qualify(self.lead, "m1")
        self.assertEqual(self.c.leads[self.lead]["status"], "qualified")

    def test_other_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.c.qualify(self.lead, "r2")
        self.assertEqual(self.c.leads[self.lead]["status"], "new")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.c.qualify("L99", "r1")

    def test_low_score(self):
        low = self.c.add_lead("b@gmail.com", "B", "web", "r1")
        with self.assertRaises(ValueError):
            self.c.qualify(low, "r1")
        self.assertEqual(self.c.leads[low]["status"], "new")

    def test_not_new(self):
        self.c.qualify(self.lead, "r1")
        with self.assertRaises(ValueError):
            self.c.qualify(self.lead, "r1")

    def test_unknown_actor(self):
        with self.assertRaises(PermissionError):
            self.c.qualify(self.lead, "ghost")

    def test_order_exists_before_permission(self):
        c = CRM(reps(("r1", "rep", 1), ("m1", "manager", 0)))
        low = c.add_lead("a@gmail.com", "A", "web", "r1")
        # actor is stranger and score is low: existence passes, permission fails
        with self.assertRaises(PermissionError):
            c.qualify(low, "ghost")


class TestConvert(unittest.TestCase):
    def setUp(self):
        self.c = basic()
        self.lead = self.c.add_lead("a@corp.com", "A", "referral", "r1")
        self.c.qualify(self.lead, "r1")

    def test_success(self):
        opp = self.c.convert(self.lead, 1000, "r1")
        self.assertEqual(opp, "O1")
        self.assertEqual(
            self.c.opps[opp],
            {
                "id": "O1",
                "lead_id": self.lead,
                "owner": "r1",
                "amount": 1000,
                "original_amount": 1000,
                "stage": "prospect",
            },
        )
        self.assertEqual(self.c.leads[self.lead]["status"], "converted")
        self.assertEqual(self.c.log[-1], ("convert", "O1", "r1"))

    def test_amount_validation(self):
        for amount in [0, -5, 1.5, "10", True, False, None]:
            with self.assertRaises(ValueError, msg=amount):
                self.c.convert(self.lead, amount, "r1")
        self.assertEqual(self.c.opps, {})

    def test_requires_qualified(self):
        other = self.c.add_lead("b@corp.com", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            self.c.convert(other, 100, "r1")
        self.assertEqual(self.c.opps, {})

    def test_requires_owner(self):
        c = CRM(reps(("m1", "manager", 0)))
        lead = c.add_lead("a@corp.com", "A", "referral", "m1")
        c.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            c.convert(lead, 100, "m1")
        self.assertEqual(c.opps, {})

    def test_other_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.c.convert(self.lead, 100, "r2")

    def test_manager_may_convert(self):
        self.assertEqual(self.c.convert(self.lead, 100, "m1"), "O1")

    def test_unknown_lead(self):
        with self.assertRaises(ValueError):
            self.c.convert("L99", 100, "r1")

    def test_ids_count_successes(self):
        other = self.c.add_lead("b@corp.com", "B", "referral", "r1")
        self.c.qualify(other, "r1")
        with self.assertRaises(ValueError):
            self.c.convert(other, 0, "r1")
        self.assertEqual(self.c.convert(other, 5, "r1"), "O1")
        self.assertEqual(self.c.convert(self.lead, 5, "r1"), "O2")


class TestAdvance(unittest.TestCase):
    def setUp(self):
        self.c = basic()
        lead = self.c.add_lead("a@corp.com", "A", "referral", "r1")
        self.c.qualify(lead, "r1")
        self.opp = self.c.convert(lead, 1000, "r1")

    def test_happy_path(self):
        self.c.advance(self.opp, "proposal", "r1")
        self.assertEqual(self.c.opps[self.opp]["stage"], "proposal")
        self.c.advance(self.opp, "negotiation", "r1")
        self.c.advance(self.opp, "won", "r1")
        self.assertEqual(self.c.opps[self.opp]["stage"], "won")
        self.assertEqual(
            [entry for entry in self.c.log if entry[0] == "advance"],
            [
                ("advance", self.opp, "r1"),
                ("advance", self.opp, "r1"),
                ("advance", self.opp, "r1"),
            ],
        )

    def test_lost_from_prospect(self):
        self.c.advance(self.opp, "lost", "r1")
        self.assertEqual(self.c.opps[self.opp]["stage"], "lost")

    def test_skip_stage_rejected(self):
        with self.assertRaises(ValueError):
            self.c.advance(self.opp, "won", "r1")
        self.assertEqual(self.c.opps[self.opp]["stage"], "prospect")

    def test_invalid_stage(self):
        with self.assertRaises(ValueError):
            self.c.advance(self.opp, "closed", "r1")

    def test_final_cannot_move(self):
        self.c.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.c.advance(self.opp, "won", "r1")

    def test_other_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.c.advance(self.opp, "proposal", "r2")

    def test_manager_allowed(self):
        self.c.advance(self.opp, "proposal", "m1")

    def test_negotiation_threshold(self):
        lead = self.c.add_lead("b@corp.com", "B", "referral", "r1")
        self.c.qualify(lead, "r1")
        big = self.c.convert(lead, 60000, "r1")
        self.c.advance(big, "proposal", "r1")
        with self.assertRaises(PermissionError):
            self.c.advance(big, "negotiation", "r1")
        self.assertEqual(self.c.opps[big]["stage"], "proposal")
        self.c.advance(big, "negotiation", "m1")
        self.assertEqual(self.c.opps[big]["stage"], "negotiation")

    def test_threshold_is_strict(self):
        lead = self.c.add_lead("b@corp.com", "B", "referral", "r1")
        self.c.qualify(lead, "r1")
        exact = self.c.convert(lead, 50000, "r1")
        self.c.advance(exact, "proposal", "r1")
        self.c.advance(exact, "negotiation", "r1")

    def test_final_frees_slot_and_assigns(self):
        c = CRM(reps(("r1", "rep", 1), ("m1", "manager", 0)))
        first = c.add_lead("a@corp.com", "A", "referral", "m1")
        second = c.add_lead("b@corp.com", "B", "referral", "m1")
        self.assertEqual(c.leads[first]["owner"], "r1")
        self.assertIsNone(c.leads[second]["owner"])
        c.qualify(first, "r1")
        opp = c.convert(first, 10, "r1")
        c.advance(opp, "proposal", "r1")
        c.advance(opp, "negotiation", "r1")
        c.advance(opp, "won", "r1")
        self.assertEqual(c.leads[second]["owner"], "r1")
        self.assertEqual(c.log[-1], ("assign", second, "system"))

    def test_no_assignment_when_full(self):
        c = CRM(reps(("r1", "rep", 1), ("m1", "manager", 0)))
        first = c.add_lead("a@corp.com", "A", "referral", "m1")
        second = c.add_lead("b@corp.com", "B", "referral", "m1")
        third = c.add_lead("c@corp.com", "C", "referral", "m1")
        c.qualify(first, "r1")
        opp = c.convert(first, 10, "r1")
        # the new opportunity still occupies the single slot
        self.assertIsNone(c.leads[second]["owner"])
        self.assertIsNone(c.leads[third]["owner"])
        c.advance(opp, "lost", "r1")
        self.assertEqual(c.leads[second]["owner"], "r1")
        self.assertIsNone(c.leads[third]["owner"])

    def test_queue_drains_one_slot_at_a_time(self):
        c = CRM(reps(("r1", "rep", 3), ("m1", "manager", 0)))
        listed = [
            c.add_lead("a%d@corp.com" % i, "A", "referral", "m1") for i in range(5)
        ]
        self.assertEqual([c.leads[lid]["owner"] for lid in listed], ["r1", "r1", "r1", None, None])
        c.qualify(listed[0], "r1")
        opp = c.convert(listed[0], 10, "r1")
        c.advance(opp, "lost", "r1")
        self.assertEqual(c.leads[listed[3]]["owner"], "r1")
        self.assertIsNone(c.leads[listed[4]]["owner"])
        self.assertEqual(
            [entry for entry in c.log if entry[0] == "assign"],
            [("assign", listed[3], "system")],
        )

    def test_tie_break_uses_string_order(self):
        c = CRM(reps(("r10", "rep", 5), ("r2", "rep", 5), ("m1", "manager", 0)))
        self.assertEqual(c.leads[c.add_lead("a@corp.com", "A", "web", "m1")]["owner"], "r10")
        self.assertEqual(c.leads[c.add_lead("b@corp.com", "B", "web", "m1")]["owner"], "r2")


class TestDiscount(unittest.TestCase):
    def setUp(self):
        self.c = basic()
        lead = self.c.add_lead("a@corp.com", "A", "referral", "r1")
        self.c.qualify(lead, "r1")
        self.opp = self.c.convert(lead, 1000, "r1")

    def test_rep_ten_percent(self):
        self.c.discount(self.opp, 10, "r1")
        self.assertEqual(self.c.opps[self.opp]["amount"], 900)
        self.assertEqual(self.c.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.c.log[-1], ("discount", self.opp, "r1"))

    def test_pct_validation(self):
        for pct in [0, 31, -1, 1.0, True, "5", None]:
            with self.assertRaises(ValueError, msg=pct):
                self.c.discount(self.opp, pct, "r1")
        self.assertEqual(self.c.opps[self.opp]["amount"], 1000)

    def test_rep_above_ten_forbidden(self):
        with self.assertRaises(PermissionError):
            self.c.discount(self.opp, 11, "r1")
        self.assertEqual(self.c.opps[self.opp]["amount"], 1000)

    def test_manager_thirty(self):
        self.c.discount(self.opp, 30, "m1")
        self.assertEqual(self.c.opps[self.opp]["amount"], 700)

    def test_cumulative_limit(self):
        self.c.discount(self.opp, 10, "r1")
        self.c.discount(self.opp, 10, "r1")
        self.c.discount(self.opp, 10, "r1")
        self.assertEqual(self.c.opps[self.opp]["amount"], 729)
        with self.assertRaises(ValueError):
            self.c.discount(self.opp, 10, "r1")
        self.assertEqual(self.c.opps[self.opp]["amount"], 729)

    def test_final_stage_rejected(self):
        self.c.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.c.discount(self.opp, 5, "m1")

    def test_other_rep_forbidden(self):
        with self.assertRaises(PermissionError):
            self.c.discount(self.opp, 5, "r2")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.c.discount("O99", 5, "r1")

    def test_failure_leaves_no_log(self):
        self.c.discount(self.opp, 10, "m1")
        self.c.discount(self.opp, 10, "m1")
        self.c.discount(self.opp, 10, "m1")
        before = len(self.c.log)
        with self.assertRaises(ValueError):
            self.c.discount(self.opp, 10, "m1")
        with self.assertRaises(ValueError):
            self.c.discount(self.opp, 10, "m1")
        self.assertEqual(len(self.c.log), before)
        self.assertEqual(self.c.opps[self.opp]["amount"], 729)


class TestTransfer(unittest.TestCase):
    def setUp(self):
        self.c = CRM(reps(("r1", "rep", 3), ("r2", "rep", 3), ("m1", "manager", 0)))
        lead = self.c.add_lead("a@corp.com", "A", "referral", "r1")
        self.c.qualify(lead, "r1")
        self.opp = self.c.convert(lead, 1000, "r1")

    def test_success(self):
        self.c.transfer(self.opp, "r2", "m1")
        self.assertEqual(self.c.opps[self.opp]["owner"], "r2")
        self.assertEqual(self.c.log[-1], ("transfer", self.opp, "m1"))

    def test_only_manager(self):
        with self.assertRaises(PermissionError):
            self.c.transfer(self.opp, "r2", "r1")
        with self.assertRaises(PermissionError):
            self.c.transfer(self.opp, "r2", "r2")
        self.assertEqual(self.c.opps[self.opp]["owner"], "r1")

    def test_new_owner_must_be_rep(self):
        for target in ["m1", "ghost", 5, None]:
            with self.assertRaises(ValueError, msg=target):
                self.c.transfer(self.opp, target, "m1")
        self.assertEqual(self.c.opps[self.opp]["owner"], "r1")

    def test_same_owner_rejected(self):
        with self.assertRaises(ValueError):
            self.c.transfer(self.opp, "r1", "m1")

    def test_final_rejected(self):
        self.c.advance(self.opp, "lost", "r1")
        with self.assertRaises(ValueError):
            self.c.transfer(self.opp, "r2", "m1")

    def test_capacity_rejected(self):
        c = CRM(reps(("r1", "rep", 3), ("r2", "rep", 1), ("m1", "manager", 0)))
        lead = c.add_lead("a@corp.com", "A", "referral", "m1")
        c.qualify(lead, "r1")
        opp = c.convert(lead, 10, "r1")
        c.add_lead("b@corp.com", "B", "web", "m1")
        self.assertEqual(c.leads["L2"]["owner"], "r2")
        with self.assertRaises(ValueError):
            c.transfer(opp, "r2", "m1")
        self.assertEqual(c.opps[opp]["owner"], "r1")

    def test_check_order_permission_before_stage(self):
        self.c.advance(self.opp, "lost", "r1")
        with self.assertRaises(PermissionError):
            self.c.transfer(self.opp, "r2", "r1")
        with self.assertRaises(ValueError):
            self.c.transfer(self.opp, "r2", "m1")

    def test_unknown_opp(self):
        with self.assertRaises(ValueError):
            self.c.transfer("O99", "r2", "m1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(basic().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_stages(self):
        c = basic()
        ids = []
        for i, amount in enumerate([1000, 1000, 1000, 1000, 1000]):
            lead = c.add_lead("a%d@corp.com" % i, "A", "referral", "r1")
            c.qualify(lead, "r1")
            ids.append(c.convert(lead, amount, "r1"))
        c.advance(ids[1], "proposal", "r1")
        c.advance(ids[2], "proposal", "r1")
        c.advance(ids[2], "negotiation", "r1")
        c.advance(ids[3], "proposal", "r1")
        c.advance(ids[3], "negotiation", "r1")
        c.advance(ids[3], "won", "r1")
        c.advance(ids[4], "lost", "r1")
        self.assertEqual(c.forecast(), {"open": 3, "weighted": 100 + 300 + 600, "won": 1000})

    def test_uses_discounted_amount(self):
        c = basic()
        lead = c.add_lead("a@corp.com", "A", "referral", "r1")
        c.qualify(lead, "r1")
        opp = c.convert(lead, 1000, "r1")
        c.discount(opp, 10, "m1")
        self.assertEqual(c.forecast()["weighted"], 90)

    def test_no_log_entry(self):
        c = basic()
        c.forecast()
        self.assertEqual(c.log, [])

    def test_no_actor_argument(self):
        with self.assertRaises(TypeError):
            basic().forecast("r1")


class TestLogIntegrity(unittest.TestCase):
    def test_full_flow_log(self):
        c = CRM(reps(("r1", "rep", 5), ("m1", "manager", 0)))
        lead = c.add_lead("a@corp.com", "A", "referral", "r1")
        c.qualify(lead, "r1")
        opp = c.convert(lead, 1000, "r1")
        c.discount(opp, 5, "r1")
        c.advance(opp, "proposal", "r1")
        c.advance(opp, "negotiation", "r1")
        c.advance(opp, "won", "r1")
        self.assertEqual(
            c.log,
            [
                ("add_lead", lead, "r1"),
                ("qualify", lead, "r1"),
                ("convert", opp, "r1"),
                ("discount", opp, "r1"),
                ("advance", opp, "r1"),
                ("advance", opp, "r1"),
                ("advance", opp, "r1"),
            ],
        )

    def test_load_counting(self):
        c = CRM(reps(("r1", "rep", 10), ("m1", "manager", 0)))
        lead = c.add_lead("a@corp.com", "A", "referral", "m1")
        self.assertEqual(c._load("r1"), 1)
        c.qualify(lead, "r1")
        self.assertEqual(c._load("r1"), 1)
        opp = c.convert(lead, 100, "r1")
        self.assertEqual(c._load("r1"), 1)
        c.advance(opp, "proposal", "r1")
        self.assertEqual(c._load("r1"), 1)
        c.advance(opp, "lost", "r1")
        self.assertEqual(c._load("r1"), 0)


if __name__ == "__main__":
    unittest.main()
