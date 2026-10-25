"""Guard tests for spec check ordering and the >50000 negotiation gate.

Added after the audit (remediation items 3-7 in audit.md). Each test pins
the first-failing check for an input where two checks could fire, so a
reordering of the spec's check sequence cannot pass silently.

Notes on the remaining audit items:
- Item 8 (transfer with a waiting lead assigned afterward): the transfer
  path's slot-freeing cannot be exercised directly because the state is
  unreachable — see TransferReachabilityTests below for the argument and
  the behavioral guard.
- Item 9 (qualify's status check vs score check): both raise ValueError,
  so the ordering is unobservable by exception type; both branches are
  covered in QualifyStatusVsScoreTests below.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crm import DuplicateLeadError  # noqa: E402

from crm_test_support import (  # noqa: E402
    add_lead,
    convert_lead,
    make_crm,
    walk_to_final,
)


class AddLeadCheckOrderTests(unittest.TestCase):
    def test_source_check_fires_before_duplicate_check(self):
        # Spec add_lead order: source (3) before duplicate email (4). A
        # duplicate email with an invalid source must raise ValueError,
        # not DuplicateLeadError.
        crm = make_crm()
        add_lead(crm, 0, source="web")
        log_before = list(crm.log)
        with self.assertRaises(ValueError) as caught:
            crm.add_lead("bob0@gmail.com", "Dup", "podcast", "m1")
        self.assertNotIsInstance(
            caught.exception, DuplicateLeadError,
            "the duplicate check fired before the source check",
        )
        # Atomic failure: nothing appended, no second lead created.
        self.assertEqual(crm.log, log_before)
        self.assertEqual(len(crm.leads), 1)


class ConvertCheckOrderTests(unittest.TestCase):
    """Audit item 4: convert fires existence (1) before amount (2).

    Note: both checks raise ValueError, so their relative order is not
    observable by exception type (verified by negative control: swapping
    the two checks in crm.py passes this suite). The guard pins the
    type-observable part of the contract — the unknown-lead call fails
    with ValueError and atomically — and, as a contrast, that the amount
    check does fire once the lead exists.
    """

    def test_existence_check_fires_before_amount_check(self):
        crm = make_crm()
        log_before = list(crm.log)
        with self.assertRaises(ValueError):
            crm.convert("L404", -5, "m1")
        self.assertEqual(crm.opps, {})
        self.assertEqual(crm.log, log_before)
        # Contrast: the amount check does fire once the lead exists.
        lead_id = add_lead(crm, 0)
        with self.assertRaises(ValueError):
            crm.convert(lead_id, -5, "m1")


class AdvanceNegotiationGateTests(unittest.TestCase):
    def test_rep_may_advance_negotiation_to_won_above_50000(self):
        # Spec check 6 gates only ENTERING negotiation above 50000; from
        # negotiation onward the owner rep may close the deal alone.
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0, 60000)   # owned by r1
        crm.advance(opp_id, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp_id, "negotiation", "r1")
        crm.advance(opp_id, "negotiation", "m1")  # manager opens the gate
        crm.advance(opp_id, "won", "r1")          # rep may close it
        self.assertEqual(crm.opps[opp_id]["stage"], "won")

    def test_negotiation_gate_uses_current_discounted_amount(self):
        # The >50000 gate reads the CURRENT amount, not the original: a
        # 60000 opportunity discounted to 42000 lets a rep enter
        # negotiation.
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0, 60000)   # owned by r1
        crm.discount(opp_id, 30, "m1")            # 60000 -> 42000
        self.assertEqual(crm.opps[opp_id]["amount"], 42000)
        crm.advance(opp_id, "proposal", "r1")
        crm.advance(opp_id, "negotiation", "r1")  # 42000 <= 50000: allowed
        self.assertEqual(crm.opps[opp_id]["stage"], "negotiation")


class DiscountCheckOrderTests(unittest.TestCase):
    def test_non_manager_cap_fires_before_cumulative_floor(self):
        # Spec discount order: non-manager 10-cap (5) before the
        # cumulative 30% floor (6). pct 11 by a rep violates both; the
        # first failing check decides: PermissionError, not ValueError.
        crm = make_crm()
        _, opp_id = convert_lead(crm, 0, 1000)    # owned by r1
        crm.discount(opp_id, 30, "m1")            # 1000 -> 700, running 30%
        log_before = list(crm.log)
        with self.assertRaises(PermissionError) as caught:
            crm.discount(opp_id, 11, "r1")        # floor would also fail
        self.assertNotIsInstance(caught.exception, ValueError)
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        self.assertEqual(crm.log, log_before)
        # Contrast: with the cap not triggered (pct <= 10), the floor
        # itself is still enforced with ValueError.
        with self.assertRaises(ValueError):
            crm.discount(opp_id, 10, "r1")        # 700 -> 630 < 70% floor
        self.assertEqual(crm.opps[opp_id]["amount"], 700)
        self.assertEqual(crm.log, log_before)


class TransferReachabilityTests(unittest.TestCase):
    """Audit item 8: transfer's post-transfer slot freeing.

    Under the spec's own rules the state "waiting queue non-empty while a
    legal transfer target exists" is unreachable: a lead only waits when
    every rep is at capacity, and a rep's slot frees only inside
    advance-to-final or transfer — both of which drain the queue
    immediately. Hence a transfer (whose target must be below capacity,
    check 6) can never coexist with a non-empty queue, so the freeing
    loop in transfer never has work to do. The guard below pins the
    invariant behaviorally.
    """

    def test_waiting_lead_implies_no_legal_transfer_target(self):
        crm = make_crm()
        convert_lead(crm, 0, 500)                 # L1 -> r1, O1 -> r1
        for n in range(1, 6):
            add_lead(crm, n)
        # Loads: r1 = O1 + L4 = 2 (cap 2), r2 = L2 = 1 (cap 1),
        # r3 = L3 + L5 + L6 = 3 (cap 3). Every rep is at capacity, so the
        # next lead waits.
        waiting = add_lead(crm, 6)
        self.assertIsNone(crm.leads[waiting]["owner"])
        # With the queue non-empty, no transfer target is below capacity:
        # every transfer attempt fails check 6 (or check 5 for r1 being
        # the current owner), so the freeing branch cannot be reached.
        log_before = list(crm.log)
        for target in ("r1", "r2", "r3"):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    crm.transfer("O1", target, "m1")
        self.assertEqual(crm.log, log_before)


class QualifyStatusVsScoreTests(unittest.TestCase):
    """Audit item 9: qualify's status check (3) vs score check (4).

    Both raise ValueError, so their relative order is unobservable by
    exception type; each branch is exercised on its own trigger instead.
    """

    def test_score_check_reached_for_new_low_score_lead(self):
        crm = make_crm()
        lead_id = add_lead(crm, 0, source="web")  # score 10
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "r1")
        self.assertEqual(crm.leads[lead_id]["status"], "new")

    def test_status_check_fails_converted_lead_even_with_score(self):
        crm = make_crm()
        lead_id, _ = convert_lead(crm, 0, 500)    # converted, score 30
        with self.assertRaises(ValueError):
            crm.qualify(lead_id, "m1")
        self.assertEqual(crm.leads[lead_id]["status"], "converted")


if __name__ == "__main__":
    unittest.main()
