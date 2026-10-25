"""Regression guards for the findings in audit.md (AE-neutral-3).

Each test names the audit finding it closes and the mutation it must kill.
The delivered behaviour is correct; these tests exist so that a build which
breaks one clause can no longer keep the suite green.
"""

import unittest

from crm import CRM, DuplicateLeadError


def make_reps():
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 0},
    ]


def make_roomy_reps():
    # m1 has spare capacity on purpose: it makes the "role == rep" clause of
    # transfer rule 3 observable instead of shadowed by the capacity check.
    return [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 2},
        {"id": "m1", "role": "manager", "capacity": 5},
    ]


class GuardTestCase(unittest.TestCase):
    def setUp(self):
        self.crm = CRM(make_reps())
        self._email_seq = 0

    def next_email(self):
        self._email_seq += 1
        return "g%d@corp.com" % self._email_seq

    def add(self, source="referral", actor="m1"):
        return self.crm.add_lead(self.next_email(), "Lead", source, actor)

    def make_opp(self, amount=1000, stage="prospect", actor="m1", crm=None,
                 owner_actor="m1"):
        """Create an opportunity (owned by r1 when possible) at `stage`."""
        target = crm if crm is not None else self.crm
        email = "o%d@corp.com" % (len(target.leads) + 1)
        lead_id = target.add_lead(email, "Lead", "referral", owner_actor)
        target.qualify(lead_id, owner_actor)
        opp_id = target.convert(lead_id, amount, owner_actor)
        steps = {
            "prospect": [],
            "proposal": ["proposal"],
            "negotiation": ["proposal", "negotiation"],
            "won": ["proposal", "negotiation", "won"],
            "lost": ["lost"],
        }[stage]
        for step in steps:
            target.advance(opp_id, step, actor)
        return opp_id

    def tail(self, log_before):
        return self.crm.log[len(log_before):]


class TestAdvanceOrdering(GuardTestCase):
    def test_actor_checked_before_final_stage(self):
        # Finding 1: swap advance rules 3/4 and this test fails.
        opp_id = self.make_opp(stage="lost")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.advance(opp_id, "won", "r2")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "lost")
        self.assertEqual(self.crm.log, log_before)

    def test_transition_checked_before_negotiation_manager_rule(self):
        # Finding 2: an illegal jump to "negotiation" above 50 000 by the
        # owning rep is a ValueError, not the rule-6 PermissionError.
        opp_id = self.make_opp(amount=60000)
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")
        log_before = list(self.crm.log)
        # PermissionError is not a ValueError, so assertRaises(ValueError)
        # alone distinguishes the two builds.
        with self.assertRaises(ValueError):
            self.crm.advance(opp_id, "negotiation", "r1")
        self.assertEqual(self.crm.opps[opp_id]["stage"], "prospect")
        self.assertEqual(self.crm.log, log_before)

    def test_successful_advance_appends_exactly_one_entry(self):
        # Finding 12: a doubled ("advance", ...) append must fail.
        opp_id = self.make_opp()
        log_before = list(self.crm.log)
        self.crm.advance(opp_id, "proposal", "r1")
        self.assertEqual(
            self.tail(log_before),
            [("advance", opp_id, "r1")],
        )


class TestConvertOrderingAndIds(GuardTestCase):
    def test_actor_checked_before_lead_status(self):
        # Finding 3: swap convert rules 3/4 and this test fails.
        lead_id = self.add(actor="m1")  # owned by r1, status "new"
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.convert(lead_id, 100, "r2")
        self.assertEqual(self.crm.leads[lead_id]["status"], "new")
        self.assertEqual(self.crm.opps, {})
        self.assertEqual(self.crm.log, log_before)

    def test_rule_five_failure_consumes_no_opportunity_number(self):
        # Finding 4: bump _opp_seq before the rule-5 check and this test fails.
        crm = CRM(
            [
                {"id": "r1", "role": "rep", "capacity": 1},
                {"id": "m1", "role": "manager", "capacity": 0},
            ]
        )
        lead1 = crm.add_lead("a@corp.com", "A", "referral", "m1")
        crm.qualify(lead1, "m1")
        opp1 = crm.convert(lead1, 100, "m1")            # "O1", r1 now at capacity
        waiting = crm.add_lead("b@corp.com", "B", "referral", "m1")
        crm.qualify(waiting, "m1")                      # qualified, still ownerless

        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.convert(waiting, 100, "m1")             # fails on rule 5
        self.assertEqual(crm.leads[waiting]["status"], "qualified")
        self.assertEqual(crm.log, log_before)
        self.assertEqual(list(crm.opps), [opp1])

        crm.advance(opp1, "lost", "m1")                 # frees r1's slot
        self.assertEqual(crm.leads[waiting]["owner"], "r1")
        self.assertEqual(crm.convert(waiting, 100, "m1"), "O2")

    def test_successful_convert_appends_exactly_one_entry(self):
        # Finding 11: a doubled ("convert", ...) append must fail.
        lead_id = self.add()
        self.crm.qualify(lead_id, "r1")
        log_before = list(self.crm.log)
        opp_id = self.crm.convert(lead_id, 500, "r1")
        self.assertEqual(
            self.tail(log_before),
            [("convert", opp_id, "r1")],
        )


class TestDiscountOrdering(GuardTestCase):
    def test_actor_checked_before_final_stage(self):
        # Finding 5: swap discount rules 3/4 and this test fails.
        opp_id = self.make_opp(stage="lost")
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.discount(opp_id, 30, "r2")
        self.assertEqual(self.crm.opps[opp_id]["amount"], 1000)
        self.assertEqual(self.crm.log, log_before)

    def test_rep_limit_checked_before_cumulative_cap(self):
        # Finding 6: evaluate the cumulative cap before the rep limit and
        # this test fails (it would raise ValueError instead).
        opp_id = self.make_opp(amount=1000)
        self.crm.discount(opp_id, 30, "m1")             # 700 of 1000, manager
        self.assertEqual(self.crm.opps[opp_id]["amount"], 700)
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.discount(opp_id, 20, "r1")         # owner rep, cap would fail
        self.assertEqual(self.crm.opps[opp_id]["amount"], 700)
        self.assertEqual(self.crm.log, log_before)

    def test_successful_discount_appends_exactly_one_entry(self):
        # Finding 13: a doubled ("discount", ...) append must fail.
        opp_id = self.make_opp()
        log_before = list(self.crm.log)
        self.crm.discount(opp_id, 10, "r1")
        self.assertEqual(
            self.tail(log_before),
            [("discount", opp_id, "r1")],
        )


class TestTransferRules(GuardTestCase):
    def test_manager_checked_before_final_stage(self):
        # Finding 7: swap transfer rules 2/4 and this test fails.
        opp_id = self.make_opp(stage="won")
        log_before = list(self.crm.log)
        with self.assertRaises(PermissionError):
            self.crm.transfer(opp_id, "r2", "r1")
        self.assertEqual(self.crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(self.crm.log, log_before)

    def test_new_owner_manager_with_spare_capacity_is_rejected(self):
        # Finding 9: delete the role != "rep" clause and this test fails.
        # m1 has capacity 5, so only the role clause can reject it.
        crm = CRM(make_roomy_reps())
        opp_id = self.make_opp(crm=crm)
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.transfer(opp_id, "m1", "m1")
        self.assertEqual(crm.opps[opp_id]["owner"], "r1")
        self.assertEqual(crm.log, log_before)

    def test_successful_transfer_appends_exactly_one_entry(self):
        # Finding 14: a doubled ("transfer", ...) append must fail.
        opp_id = self.make_opp()
        log_before = list(self.crm.log)
        self.crm.transfer(opp_id, "r2", "m1")
        self.assertEqual(
            self.tail(log_before),
            [("transfer", opp_id, "m1")],
        )


class TestQualifyLog(GuardTestCase):
    def test_successful_qualify_appends_exactly_one_entry(self):
        # Finding 10: a doubled ("qualify", ...) append must fail.
        lead_id = self.add()
        log_before = list(self.crm.log)
        self.crm.qualify(lead_id, "r1")
        self.assertEqual(
            self.tail(log_before),
            [("qualify", lead_id, "r1")],
        )


class TestAddLeadGuard(GuardTestCase):
    def test_source_checked_before_duplicate(self):
        # Finding 8: check duplicates before source and this test raises
        # DuplicateLeadError instead of ValueError.
        existing = self.add()  # g1@corp.com, referenced below
        email = self.crm.leads[existing]["email"]
        log_before = list(self.crm.log)
        with self.assertRaises(ValueError) as ctx:
            self.crm.add_lead(email, "A", "bogus", "m1")
        self.assertNotIsInstance(ctx.exception, DuplicateLeadError)
        self.assertEqual(len(self.crm.leads), 1)
        self.assertEqual(self.crm.log, log_before)

    def test_multiple_at_signs_are_rejected_by_the_documented_rule(self):
        # Finding 15: delete the count("@") != 1 clause and the tuple unpack
        # raises "too many values to unpack" instead of the documented error.
        with self.assertRaisesRegex(ValueError, "exactly one '@'"):
            self.crm.add_lead("a@@b.com", "A", "web", "m1")
        self.assertEqual(self.crm.leads, {})
        self.assertEqual(self.crm.log, [])

    def test_empty_local_part_and_empty_domain_are_rejected(self):
        for email in ["@corp.com", "a@"]:
            with self.subTest(email=email):
                with self.assertRaisesRegex(ValueError, "must not be empty|domain"):
                    self.crm.add_lead(email, "A", "web", "m1")
                self.assertEqual(self.crm.leads, {})


if __name__ == "__main__":
    unittest.main()
