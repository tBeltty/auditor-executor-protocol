import copy
import unittest

from crm import CRM, DuplicateLeadError


def reps(*specs):
    return [
        {"id": rid, "role": role, "capacity": cap} for rid, role, cap in specs
    ]


def base_crm():
    return CRM(reps(("r1", "rep", 2), ("r2", "rep", 2),
                    ("m1", "manager", 0), ("m2", "manager", 0)))


class EmailAndAddLeadTests(unittest.TestCase):
    def test_email_validation(self):
        crm = base_crm()
        bad = ["not-an-email", "a@@b.com", "a@b", "a@b.", "a@.com", "", 42, None]
        for value in bad:
            with self.subTest(email=value):
                with self.assertRaises(ValueError):
                    crm.add_lead(value, "Ann", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_normalization_and_score(self):
        crm = base_crm()
        lid = crm.add_lead("  Ann@Example.COM ", "  Ann  ", "web", "r1")
        lead = crm.leads[lid]
        self.assertEqual(lead["email"], "ann@example.com")
        self.assertEqual(lead["name"], "Ann")
        self.assertEqual(lead["score"], 25)  # web 10 + 15 corporate domain
        self.assertEqual(lead["status"], "new")
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(crm.log, [("add_lead", lid, "r1")])

    def test_score_table(self):
        crm = base_crm()
        scores = [
            ("a@gmail.com", "web", 10),
            ("b@gmail.com", "referral", 30),
            ("c@gmail.com", "event", 20),
            ("d@corp.io", "referral", 45),
        ]
        for email, source, expected in scores:
            lid = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lid]["score"], expected)

    def test_name_and_source_validation(self):
        crm = base_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "   ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", None, "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("a@b.com", "N", "cold-call", "r1")

    def test_duplicate_email_uses_normalized_form(self):
        crm = base_crm()
        first = crm.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  A@B.COM ", "Other", "event", "r2")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(list(crm.leads), [first])

    def test_unknown_actor_is_checked_first(self):
        crm = base_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead("bad", "", "nope", "ghost")
        with self.assertRaises(PermissionError):
            crm.qualify("L404", "ghost")


class AssignmentTests(unittest.TestCase):
    def test_lowest_load_then_smallest_id(self):
        crm = CRM(reps(("b", "rep", 5), ("a", "rep", 5)))
        ids = [crm.add_lead("u%d@x.com" % i, "N", "web", "a") for i in range(4)]
        owners = [crm.leads[lid]["owner"] for lid in ids]
        # first tie goes to "a"; after that "b" has the lower load.
        self.assertEqual(owners, ["a", "b", "a", "b"])

    def test_capacity_and_fifo_queue(self):
        crm = CRM(reps(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        l2 = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        l3 = crm.add_lead("c@gmail.com", "C", "referral", "r1")
        l4 = crm.add_lead("d@gmail.com", "D", "referral", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])
        self.assertIsNone(crm.leads[l4]["owner"])

        # Converting does not free a slot by itself; advance to a final stage does.
        crm.qualify(l1, "r1")
        crm.convert(l1, 100, "r1")
        self.assertIsNone(crm.leads[l3]["owner"])

        crm.advance("O1", "lost", "r1")
        self.assertEqual(crm.leads[l3]["owner"], "r1")
        self.assertIsNone(crm.leads[l4]["owner"])
        self.assertEqual(crm.log[-2:],
                         [("advance", "O1", "r1"), ("assign", l3, "system")])

    def test_manager_never_owns(self):
        crm = CRM(reps(("m1", "manager", 10)))
        lid = crm.add_lead("a@b.com", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])


class QualifyConvertTests(unittest.TestCase):
    def setUp(self):
        # r2 has zero capacity, so every lead here belongs to r1.
        self.crm = CRM(reps(("r1", "rep", 10), ("r2", "rep", 0),
                            ("m1", "manager", 0), ("m2", "manager", 0)))
        self.lid = self.crm.add_lead("a@gmail.com", "A", "web", "r1")  # score 10

    def test_score_below_thirty_rejected(self):
        with self.assertRaises(ValueError):
            self.crm.qualify(self.lid, "r1")
        self.assertEqual(self.crm.leads[self.lid]["status"], "new")
        self.assertEqual(len(self.crm.log), 1)

    def test_permission_and_status_ordering(self):
        lid = self.crm.add_lead("b@gmail.com", "B", "referral", "r1")
        with self.assertRaises(PermissionError):
            self.crm.qualify(lid, "r2")  # not owner, not manager
        self.crm.qualify(lid, "m1")  # manager may qualify
        with self.assertRaises(ValueError):
            self.crm.qualify(lid, "r1")  # already qualified

    def test_convert_success_and_status(self):
        lid = self.crm.add_lead("b@gmail.com", "B", "referral", "r1")
        self.crm.qualify(lid, "r1")
        oid = self.crm.convert(lid, 500, "r1")
        self.assertEqual(oid, "O1")
        self.assertEqual(self.crm.opps[oid], {
            "id": "O1", "lead_id": lid, "owner": "r1", "amount": 500,
            "original_amount": 500, "stage": "prospect",
        })
        self.assertEqual(self.crm.leads[lid]["status"], "converted")
        self.assertEqual(self.crm.log[-1], ("convert", "O1", "r1"))

    def test_convert_validation_order(self):
        lid = self.crm.add_lead("b@gmail.com", "B", "referral", "r1")
        self.crm.qualify(lid, "r1")
        for bad in [0, -5, True, 1.5, "5", None]:
            with self.subTest(amount=bad):
                with self.assertRaises(ValueError):
                    self.crm.convert(lid, bad, "r1")
        # amount is checked before permission
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 0, "r2")

    def test_convert_unqualified_and_unowned(self):
        lid = self.crm.add_lead("b@gmail.com", "B", "referral", "r1")
        with self.assertRaises(ValueError):
            self.crm.convert(lid, 10, "r1")  # still "new"

    def test_unowned_lead_cannot_convert(self):
        crm = CRM(reps(("r1", "rep", 0), ("m1", "manager", 0)))
        lid = crm.add_lead("b@gmail.com", "B", "referral", "m1")
        crm.qualify(lid, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 10, "m1")
        self.assertEqual(crm.opps, {})


class AdvanceTests(unittest.TestCase):
    def setUp(self):
        self.crm = base_crm()
        self.lid = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.crm.qualify(self.lid, "r1")
        self.oid = self.crm.convert(self.lid, 10000, "r1")

    def test_happy_path_and_final_stage(self):
        self.crm.advance(self.oid, "proposal", "r1")
        self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "won", "r1")
        self.assertEqual(self.crm.opps[self.oid]["stage"], "won")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "lost", "m1")

    def test_invalid_transitions(self):
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "negotiation", "r1")
        self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "won", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "proposal", "r1")
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "garbage", "r1")
        self.crm.advance(self.oid, "lost", "r1")

    def test_permission_before_transition(self):
        # Stage validity (check 2) wins over actor permission (check 3) ...
        with self.assertRaises(ValueError):
            self.crm.advance(self.oid, "garbage", "r2")
        # ... but a valid stage by a non-owner is a permission failure.
        with self.assertRaises(PermissionError):
            self.crm.advance(self.oid, "proposal", "r2")

    def test_negotiation_threshold_requires_manager(self):
        crm = base_crm()
        lid = crm.add_lead("big@gmail.com", "B", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 50001, "r1")
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "proposal")
        crm.advance(oid, "negotiation", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")

    def test_fifty_thousand_is_allowed_for_owner(self):
        crm = base_crm()
        lid = crm.add_lead("edge@gmail.com", "E", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 50000, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "negotiation")


class DiscountTests(unittest.TestCase):
    def setUp(self):
        self.crm = base_crm()
        lid = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        self.oid = self.crm.convert(lid, 10000, "r1")

    def test_discount_math_and_log(self):
        self.crm.discount(self.oid, 1, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 9900)
        self.crm.discount(self.oid, 10, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 8910)
        self.assertEqual(self.crm.log[-1], ("discount", self.oid, "m1"))

    def test_reps_limited_to_ten(self):
        with self.assertRaises(PermissionError):
            self.crm.discount(self.oid, 11, "r1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 10000)

    def test_pct_validation(self):
        for bad in [0, 31, -1, True, 5.0, "5", None]:
            with self.subTest(pct=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.oid, bad, "m1")

    def test_cumulative_floor(self):
        self.crm.discount(self.oid, 30, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7000)
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 1, "m1")
        self.assertEqual(self.crm.opps[self.oid]["amount"], 7000)

    def test_lost_opportunity_cannot_be_discounted(self):
        self.crm.advance(self.oid, "lost", "r1")
        with self.assertRaises(ValueError):
            self.crm.discount(self.oid, 5, "m1")


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.crm = base_crm()
        lid = self.crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.crm.qualify(lid, "r1")
        self.oid = self.crm.convert(lid, 1000, "r1")

    def test_transfer_success(self):
        self.crm.transfer(self.oid, "r2", "m1")
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r2")
        self.assertEqual(self.crm.log[-1], ("transfer", self.oid, "m1"))

    def test_transfer_validation(self):
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "r2", "r1")  # not a manager
        with self.assertRaises(PermissionError):
            self.crm.transfer(self.oid, "ghost", "r1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "m2", "m1")  # manager is not a rep
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "ghost", "m1")
        with self.assertRaises(ValueError):
            self.crm.transfer(self.oid, "r1", "m1")  # same owner
        self.assertEqual(self.crm.opps[self.oid]["owner"], "r1")

    def test_target_capacity_and_final_stage(self):
        crm = CRM(reps(("r1", "rep", 1), ("r2", "rep", 1), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 100, "r1")
        crm.add_lead("b@gmail.com", "B", "referral", "m1")  # fills r2
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")
        crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")

    def test_transfer_moves_owner_and_frees_previous_load(self):
        crm = CRM(reps(("r1", "rep", 1), ("r2", "rep", 2), ("m1", "manager", 0)))
        l1 = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 100, "r1")
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        # r1's slot is free again, so the next lead is assigned to r1.
        l2 = crm.add_lead("b@gmail.com", "B", "referral", "m1")
        self.assertEqual(crm.leads[l2]["owner"], "r1")


class ForecastAndAtomicityTests(unittest.TestCase):
    def test_forecast(self):
        crm = CRM(reps(("r1", "rep", 10), ("m1", "manager", 0)))
        oids = []
        for i, amount in enumerate([100, 1000, 500, 200]):
            lid = crm.add_lead("u%d@gmail.com" % i, "N", "referral", "r1")
            crm.qualify(lid, "r1")
            oids.append(crm.convert(lid, amount, "r1"))
        crm.advance(oids[1], "proposal", "r1")
        crm.advance(oids[2], "proposal", "r1")
        crm.advance(oids[2], "negotiation", "r1")
        crm.advance(oids[2], "won", "r1")
        crm.advance(oids[3], "lost", "r1")
        # open: prospect 100, proposal 1000; negotiations: none; won: 500.
        self.assertEqual(crm.forecast(), {"open": 2, "weighted": 310, "won": 500})
        self.assertEqual(crm.log[-1], ("advance", oids[3], "r1"))

    def test_failed_calls_change_nothing(self):
        crm = base_crm()
        lid = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 10000, "r1")
        snapshot = copy.deepcopy((crm.leads, crm.opps, crm.log))
        failures = [
            lambda: crm.add_lead("bad", "", "nope", "ghost"),
            lambda: crm.add_lead("bad", "N", "web", "r1"),
            lambda: crm.add_lead("a@gmail.com", "Dup", "web", "r1"),
            lambda: crm.qualify("L99", "r1"),
            lambda: crm.qualify(lid, "r1"),
            lambda: crm.convert(oid, 100, "r1"),
            lambda: crm.advance(oid, "garbage", "r1"),
            lambda: crm.advance(oid, "proposal", "r2"),
            lambda: crm.discount(oid, 11, "r1"),
            lambda: crm.discount(oid, 40, "m1"),
            lambda: crm.transfer(oid, "ghost", "m1"),
            lambda: crm.transfer(oid, "r2", "r1"),
        ]
        for call in failures:
            with self.assertRaises((ValueError, PermissionError, DuplicateLeadError)):
                call()
        self.assertEqual((crm.leads, crm.opps, crm.log), snapshot)


if __name__ == "__main__":
    unittest.main()
