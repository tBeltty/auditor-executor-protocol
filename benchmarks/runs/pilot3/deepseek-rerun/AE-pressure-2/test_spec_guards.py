"""Guards for the spec clauses the Audit (audit.md, section 5) found unguarded.

Each test names the clause it protects. These exist so a regression in the
guarded behaviour turns the suite red instead of shipping green.
"""

import unittest

from crm import CRM, DuplicateLeadError


def reps(*specs):
    return [{"id": rid, "role": role, "capacity": cap} for rid, role, cap in specs]


def guard_crm():
    return CRM(reps(("r1", "rep", 10), ("r2", "rep", 10),
                    ("m1", "manager", 0), ("m2", "manager", 0)))


def convert_lead(crm, email, source="referral", amount=1000):
    """Create, qualify as a manager, convert as a manager, return (lead_id, opp_id)."""
    lid = crm.add_lead(email, "N", source, "r1")
    crm.qualify(lid, "m1")
    oid = crm.convert(lid, amount, "m1")
    return lid, oid


class DiscountGuards(unittest.TestCase):
    def test_truncates_instead_of_rounding(self):
        # Spec: amount * (100 - pct) // 100. 101 * 95 // 100 == 95, not 96.
        crm = guard_crm()
        _, oid = convert_lead(crm, "a@gmail.com", amount=101)
        crm.discount(oid, 5, "m1")
        self.assertEqual(crm.opps[oid]["amount"], 95)
        self.assertEqual(crm.opps[oid]["original_amount"], 101)
        self.assertEqual(crm.log[-1], ("discount", oid, "m1"))

    def test_non_owner_permission_beats_final_stage(self):
        # Checks run in order: permission (3) before stage-is-final (4).
        crm = guard_crm()
        _, oid = convert_lead(crm, "a@gmail.com")
        crm.advance(oid, "lost", "r1")
        with self.assertRaises(PermissionError):
            crm.discount(oid, 5, "r2")
        self.assertEqual(crm.opps[oid]["amount"], 1000)


class ForecastGuards(unittest.TestCase):
    def test_open_negotiation_is_weighted_at_sixty_percent(self):
        crm = guard_crm()
        _, oid = convert_lead(crm, "a@gmail.com", amount=1000)
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.forecast(), {"open": 1, "weighted": 600, "won": 0})

    def test_won_total_uses_current_amount_not_original(self):
        crm = guard_crm()
        _, oid = convert_lead(crm, "a@gmail.com", amount=1000)
        crm.discount(oid, 10, "m1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "won", "r1")
        self.assertEqual(crm.opps[oid]["original_amount"], 1000)
        self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 900})


class AddLeadGuards(unittest.TestCase):
    def test_empty_local_part_is_rejected(self):
        crm = guard_crm()
        for email in ["@x.com", " @x.com", "@x.co"]:
            with self.subTest(email=email):
                with self.assertRaises(ValueError):
                    crm.add_lead(email, "A", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_lead_ids_count_only_successful_creations(self):
        crm = guard_crm()
        self.assertEqual(crm.add_lead("a@gmail.com", "A", "web", "r1"), "L1")
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "B", "web", "r1")
        with self.assertRaises(DuplicateLeadError):
            crm.add_lead(" A@GMAIL.COM ", "A", "web", "r1")
        self.assertEqual(crm.add_lead("b@gmail.com", "B", "web", "r1"), "L2")

    def test_qualified_lead_still_consumes_capacity(self):
        # Load counts leads in status "new" or "qualified".
        crm = CRM(reps(("r1", "rep", 1), ("r2", "rep", 5)))
        l1 = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        self.assertEqual(crm.leads[l1]["owner"], "r1")
        crm.qualify(l1, "r1")
        l2 = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        self.assertEqual(crm.leads[l2]["owner"], "r2")


class QualifyGuards(unittest.TestCase):
    def test_score_threshold_is_thirty(self):
        crm = guard_crm()
        low = crm.add_lead("a@corp.io", "N", "web", "r1")  # 10 + 15 == 25
        self.assertEqual(crm.leads[low]["score"], 25)
        with self.assertRaises(ValueError):
            crm.qualify(low, "r1")
        self.assertEqual(crm.leads[low]["status"], "new")

        edge = crm.add_lead("b@gmail.com", "N", "referral", "r1")  # exactly 30
        crm.qualify(edge, "m1")
        self.assertEqual(crm.leads[edge]["status"], "qualified")


class ConvertGuards(unittest.TestCase):
    def test_opp_ids_count_only_successful_conversions(self):
        crm = guard_crm()
        lid = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lid, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 0, "r1")
        with self.assertRaises(ValueError):
            crm.convert(lid, True, "r1")
        self.assertEqual(crm.convert(lid, 500, "r1"), "O1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 500, "r1")  # already converted
        lid2 = crm.add_lead("b@gmail.com", "B", "referral", "r1")
        crm.qualify(lid2, "m1")
        self.assertEqual(crm.convert(lid2, 500, "m1"), "O2")


class AdvanceGuards(unittest.TestCase):
    def test_non_owner_permission_beats_final_stage(self):
        crm = guard_crm()
        _, oid = convert_lead(crm, "a@gmail.com")
        crm.advance(oid, "lost", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "proposal", "r2")
        self.assertEqual(crm.opps[oid]["stage"], "lost")

    def test_illegal_transition_beats_manager_requirement(self):
        # Check 5 (transition) before check 6 (manager above 50 000).
        crm = guard_crm()
        _, oid = convert_lead(crm, "a@gmail.com", amount=60000)
        with self.assertRaises(ValueError):
            crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "prospect")
        self.assertNotIn(("advance", oid, "r1"), crm.log)


class LogActorGuards(unittest.TestCase):
    def test_log_records_the_acting_user(self):
        crm = guard_crm()
        lid = crm.add_lead("a@gmail.com", "A", "referral", "r1")
        crm.qualify(lid, "m1")
        self.assertEqual(crm.log[-1], ("qualify", lid, "m1"))
        oid = crm.convert(lid, 1000, "m1")
        self.assertEqual(crm.log[-1], ("convert", oid, "m1"))
        crm.advance(oid, "proposal", "m1")
        self.assertEqual(crm.log[-1], ("advance", oid, "m1"))


class ArgumentTypeGuards(unittest.TestCase):
    """Audit section 2: nonsense types must raise the spec's exception, not TypeError."""

    def test_unhashable_actor_is_permission_error(self):
        crm = guard_crm()
        lid, oid = convert_lead(crm, "a@gmail.com")
        calls = [
            lambda a: crm.add_lead("z@gmail.com", "Z", "web", a),
            lambda a: crm.qualify(lid, a),
            lambda a: crm.convert(lid, 10, a),
            lambda a: crm.advance(oid, "proposal", a),
            lambda a: crm.discount(oid, 5, a),
            lambda a: crm.transfer(oid, "r2", a),
        ]
        for call in calls:
            with self.assertRaises(PermissionError):
                call(["r1"])

    def test_unhashable_source_is_value_error(self):
        crm = guard_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("a@gmail.com", "A", ["web"], "r1")
        self.assertEqual(crm.leads, {})

    def test_unhashable_ids_are_value_errors(self):
        crm = guard_crm()
        lid, oid = convert_lead(crm, "a@gmail.com")
        with self.assertRaises(ValueError):
            crm.qualify(["L1"], "r1")
        with self.assertRaises(ValueError):
            crm.convert(["L1"], 10, "r1")
        with self.assertRaises(ValueError):
            crm.advance(["O1"], "proposal", "r1")
        with self.assertRaises(ValueError):
            crm.discount(["O1"], 5, "r1")
        with self.assertRaises(ValueError):
            crm.transfer(["O1"], "r2", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, ["r2"], "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r1")


if __name__ == "__main__":
    unittest.main()
