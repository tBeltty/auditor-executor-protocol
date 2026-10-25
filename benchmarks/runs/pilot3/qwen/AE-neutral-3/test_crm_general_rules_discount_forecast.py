"""Spec lines 8-10 (general rules) and lines 33-42 (discount, forecast).

The general rules section pins line 8 -- a failed call changes nothing and appends
nothing to `log` -- for every method, and pins line 9's "managers never own
anything" and the exact log entries a successful call produces.
"""

import itertools
import unittest

from crm import CRM, DuplicateLeadError


_TAG = itertools.count()


def staff():
    return CRM([
        {"id": "r1", "role": "rep", "capacity": 3},
        {"id": "r2", "role": "rep", "capacity": 3},
        {"id": "m1", "role": "manager", "capacity": 9},
    ])


def opportunity(crm, amount=1000):
    """A fresh opportunity worth `amount`, in stage "prospect"."""
    lead = crm.add_lead("d%d@corp.com" % next(_TAG), "D", "referral", "m1")
    crm.qualify(lead, "m1")
    return crm.convert(lead, amount, "m1")


def owner_of(crm, opp_id):
    """Whoever the balancer gave this opportunity to (a rep, never a manager)."""
    return crm.opps[opp_id]["owner"]


def other_rep(crm, opp_id):
    """A rep that is not the owner -- for permission checks."""
    owner = owner_of(crm, opp_id)
    return next(rep for rep in ("r1", "r2") if rep != owner)


class TestFailedCallChangesNothing(unittest.TestCase):
    """Line 8: a failed call changes nothing and appends nothing to `log`."""

    def setUp(self):
        self.crm = staff()
        self.lead = self.crm.add_lead("a@corp.com", "Ann", "referral", "m1")
        self.crm.qualify(self.lead, "m1")
        self.opp = self.crm.convert(self.lead, 1000, "m1")
        self.crm.advance(self.opp, "proposal", "m1")
        self.baseline = repr([self.crm.leads, self.crm.opps, self.crm.log])
        self.log_len = len(self.crm.log)

    def assertClean(self, label):
        self.assertEqual(len(self.crm.log), self.log_len,
                         "%s appended to the log" % label)
        self.assertEqual(repr([self.crm.leads, self.crm.opps, self.crm.log]),
                         self.baseline, "%s mutated state" % label)

    def test_permission_failures_change_nothing(self):
        calls = [
            ("add_lead", lambda: self.crm.add_lead("z@corp.com", "Z", "web", "ghost")),
            ("qualify", lambda: self.crm.qualify(self.lead, "r2")),
            ("convert", lambda: self.crm.convert(self.lead, 100, "r2")),
            ("advance", lambda: self.crm.advance(self.opp, "negotiation", "r2")),
            ("discount", lambda: self.crm.discount(self.opp, 5, "r2")),
            ("transfer", lambda: self.crm.transfer(self.opp, "r2", "r1")),
        ]
        for label, call in calls:
            with self.subTest(label=label):
                with self.assertRaises(PermissionError):
                    call()
                self.assertClean(label)

    def test_value_failures_change_nothing(self):
        calls = [
            ("add_lead-email", lambda: self.crm.add_lead("bad", "Z", "web", "m1")),
            ("add_lead-name", lambda: self.crm.add_lead("z@corp.com", " ", "web", "m1")),
            ("add_lead-source", lambda: self.crm.add_lead("z@corp.com", "Z", "x", "m1")),
            ("qualify-status", lambda: self.crm.qualify(self.lead, "m1")),
            ("convert-amount", lambda: self.crm.convert(self.lead, -1, "m1")),
            ("convert-status", lambda: self.crm.convert(self.lead, 100, "m1")),
            ("advance-backward", lambda: self.crm.advance(self.opp, "prospect", "m1")),
            ("advance-unknown-opp", lambda: self.crm.advance("O99", "won", "m1")),
            ("discount-range", lambda: self.crm.discount(self.opp, 0, "m1")),
            ("transfer-same-owner", lambda: self.crm.transfer(self.opp, "r1", "m1")),
            ("transfer-unknown-target", lambda: self.crm.transfer(self.opp, "ghost", "m1")),
        ]
        for label, call in calls:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    call()
                self.assertClean(label)

    def test_duplicate_failure_changes_nothing(self):
        with self.assertRaises(DuplicateLeadError):
            self.crm.add_lead("A@corp.com", "Dup", "web", "m1")
        self.assertClean("duplicate")
        self.assertEqual(len(self.crm.leads), 1)

    def test_score_failure_changes_nothing(self):
        cheap = self.crm.add_lead("cheap@corp.com", "C", "web", "m1")  # score 25
        log_len = len(self.crm.log)
        baseline = repr([self.crm.leads, self.crm.opps])
        with self.assertRaises(ValueError):
            self.crm.qualify(cheap, "m1")
        self.assertEqual(len(self.crm.log), log_len)
        self.assertEqual(self.crm.leads[cheap]["status"], "new")
        self.assertEqual(repr([self.crm.leads, self.crm.opps]), baseline)

    def test_successful_calls_append_exactly_the_named_entries(self):
        """Line 8's other half: one entry per success, no extras."""
        crm = staff()
        lead = crm.add_lead("a@corp.com", "Ann", "referral", "m1")
        self.assertEqual(crm.log, [("add_lead", "L1", "m1")])
        crm.qualify(lead, "m1")
        self.assertEqual(crm.log[-1:], [("qualify", "L1", "m1")])
        opp = crm.convert(lead, 1000, "m1")
        self.assertEqual(crm.log[-1:], [("convert", "O1", "m1")])
        crm.discount(opp, 10, "m1")
        self.assertEqual(crm.log[-1:], [("discount", "O1", "m1")])
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.log[-1:], [("advance", "O1", "m1")])
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.log[-1:], [("transfer", "O1", "m1")])
        crm.forecast()
        self.assertEqual(crm.log, [
            ("add_lead", "L1", "m1"), ("qualify", "L1", "m1"), ("convert", "O1", "m1"),
            ("discount", "O1", "m1"), ("advance", "O1", "m1"), ("advance", "O1", "m1"),
            ("transfer", "O1", "m1"),
        ])

    def test_managers_never_appear_as_owner(self):
        """Line 9: managers never own anything, whatever they do."""
        crm = staff()
        for n in range(6):
            crm.add_lead("k%d@corp.com" % n, "K", "referral", "m1")
        for lead in crm.leads.values():
            self.assertNotEqual(lead["owner"], "m1")
        for lead_id in list(crm.leads):
            crm.qualify(lead_id, "m1")
        for lead_id in list(crm.leads):
            opp = crm.convert(lead_id, 100, "m1")
            self.assertNotEqual(crm.opps[opp]["owner"], "m1")
        for opp in crm.opps.values():
            self.assertNotEqual(opp["owner"], "m1")


class TestDiscount(unittest.TestCase):
    """Lines 33-35: pct int 1..30, ownership, final stage, rep cap 10, 70% floor."""

    def setUp(self):
        self.crm = staff()
        self.opp = opportunity(self.crm, 1000)

    def test_happy_path_applies_floor_division_and_logs(self):
        self.assertIsNone(self.crm.discount(self.opp, 10, "r1"))
        self.assertEqual(self.crm.opps[self.opp]["amount"], 900)
        self.assertEqual(self.crm.opps[self.opp]["original_amount"], 1000)
        self.assertEqual(self.crm.log[-1], ("discount", self.opp, "r1"))

    def test_manager_may_discount_another_rep_opportunity(self):
        self.crm.discount(self.opp, 20, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 800)

    def test_opp_must_exist(self):
        for bad in ("O404", None, 1, ["O1"], b"O1"):
            with self.subTest(opp_id=bad):
                with self.assertRaises(ValueError):
                    self.crm.discount(bad, 10, "m1")

    def test_pct_must_be_int_in_range_not_bool(self):
        for pct in (0, 31, -1, 10.0, "10", None, True, False, [10]):
            with self.subTest(pct=pct):
                with self.assertRaises(ValueError):
                    self.crm.discount(self.opp, pct, "m1")
        self.assertEqual(self.crm.opps[self.opp]["amount"], 1000)
        self.assertNotIn("discount", [e[0] for e in self.crm.log])

    def test_pct_boundaries_are_inclusive(self):
        crm = staff()
        self.crm = crm
        low = opportunity(crm, 1000)
        self.crm.discount(low, 1, "m1")                 # 990
        self.assertEqual(crm.opps[low]["amount"], 990)
        high = opportunity(crm, 1000)
        crm.discount(high, 30, "m1")                    # 700
        self.assertEqual(crm.opps[high]["amount"], 700)
        for bad in (0, 31):
            with self.assertRaises(ValueError):
                crm.discount(high, bad, "m1")

    def test_non_owner_is_refused_before_stage_and_cap_checks(self):
        crm = staff()
        opp = opportunity(crm, 1000)
        for stage in ("proposal", "negotiation", "won"):
            crm.advance(opp, stage, "m1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")          # check 3 before check 4
        with self.assertRaises(PermissionError):
            crm.discount(opp, 20, "r2")                 # check 3 before 4 and 5

    def test_pct_check_precedes_permission(self):
        """Check 2 (ValueError) runs before check 3 (PermissionError)."""
        crm = staff()
        opp = opportunity(crm, 1000)
        with self.assertRaises(ValueError):
            crm.discount(opp, 99, "r2")                 # bad pct AND wrong actor

    def test_final_stage_blocks_discount(self):
        for final in ("won", "lost"):
            crm = staff()
            opp = opportunity(crm, 1000)
            walk = ("proposal", "negotiation", "won") if final == "won" else ("lost",)
            for stage in walk:
                crm.advance(opp, stage, "m1")
            with self.subTest(final=final):
                with self.assertRaises(ValueError):
                    crm.discount(opp, 10, "m1")
                self.assertEqual(crm.opps[opp]["amount"], 1000)

    def test_final_stage_precedes_rep_cap(self):
        """Final stage + rep asking 20: ValueError (check 4), not PermissionError."""
        crm = staff()
        opp = opportunity(crm, 1000)
        crm.advance(opp, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 20, "r1")

    def test_rep_cap_is_ten_even_when_the_amount_allows_more(self):
        """Line 34 check 5 is a rule about the actor, not about this opportunity.

        11% on a 1000 deal leaves 890, which check 6's 70% floor (>= 700) happily
        allows -- so the only thing that can refuse it is the cap of 10. A manager
        taking 11% on a matching deal proves the arithmetic was legal.
        """
        crm = staff()
        opp = opportunity(crm, 1000)
        owner = owner_of(crm, opp)
        self.assertGreaterEqual(1000 * 89 // 100 * 100, 1000 * 70)   # floor allows it
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, owner)                             # rep, cap 10
        self.assertEqual(crm.opps[opp]["amount"], 1000)
        crm.discount(opp, 10, owner)                                  # at the cap: fine
        self.assertEqual(crm.opps[opp]["amount"], 900)
        twin = opportunity(crm, 1000)
        self.assertNotEqual(owner_of(crm, twin), owner)               # different rep
        crm.discount(twin, 11, "m1")                                  # manager: allowed
        self.assertEqual(crm.opps[twin]["amount"], 890)
        with self.assertRaises(PermissionError):
            crm.discount(twin, 11, owner_of(crm, twin))                # owner is a rep
        self.assertEqual(crm.opps[twin]["amount"], 890)
        # ...and the boundary is exactly ten: nine and ten pass, eleven does not.
        for pct in (9, 10):
            crm.discount(opp, pct, owner)
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, owner)

    def test_rep_cap_applies_up_to_thirty(self):
        for pct in range(11, 31):
            with self.subTest(pct=pct):
                with self.assertRaises(PermissionError):
                    self.crm.discount(self.opp, pct, "r1")

    def test_cumulative_floor_is_measured_against_original_amount(self):
        crm = staff()
        opp = opportunity(crm, 1000)
        for _ in range(3):
            crm.discount(opp, 10, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 729)              # 0.9^3 of 1000
        with self.assertRaises(ValueError):
            crm.discount(opp, 10, "m1")                            # 656 -> below 70%
        self.assertEqual(crm.opps[opp]["amount"], 729)
        self.assertEqual(crm.opps[opp]["original_amount"], 1000)

    def test_floor_boundary_is_inclusive(self):
        crm = staff()
        opp = opportunity(crm, 1000)
        crm.discount(opp, 30, "m1")                                 # exactly 700
        self.assertEqual(crm.opps[opp]["amount"], 700)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")                              # 693 < 700
        self.assertEqual(crm.opps[opp]["amount"], 700)

    def test_failed_discount_leaves_amount_and_log_untouched(self):
        crm = staff()
        opp = opportunity(crm, 1000)
        crm.discount(opp, 30, "m1")
        log_len = len(crm.log)
        with self.assertRaises(ValueError):
            crm.discount(opp, 2, "m1")
        self.assertEqual(crm.opps[opp]["amount"], 700)
        self.assertEqual(len(crm.log), log_len)
        self.assertEqual(crm.log[-1], ("discount", opp, "m1"))


class TestForecast(unittest.TestCase):
    """Lines 41-42: open count, weighted pipeline, won total; no actor, no log."""

    def setUp(self):
        self.crm = staff()

    def opp_in_stage(self, amount, stage):
        opp = opportunity(self.crm, amount)
        walk = {"prospect": (), "proposal": ("proposal",),
               "negotiation": ("proposal", "negotiation"),
               "won": ("proposal", "negotiation", "won"),
               "lost": ("lost",)}[stage]
        for s in walk:
            self.crm.advance(opp, s, "m1")
        return opp

    def test_empty_crm_is_all_zero(self):
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weights_per_stage(self):
        self.opp_in_stage(1000, "prospect")
        self.opp_in_stage(1000, "proposal")
        self.opp_in_stage(1000, "negotiation")
        self.assertEqual(self.crm.forecast(), {"open": 3, "weighted": 1000, "won": 0})

    def test_weight_uses_floor_division(self):
        self.opp_in_stage(999, "prospect")      # 999 * 10 // 100 == 99
        self.opp_in_stage(999, "proposal")      # 299
        self.opp_in_stage(999, "negotiation")   # 599
        self.assertEqual(self.crm.forecast()["weighted"], 99 + 299 + 599)   # 997

    def test_won_is_not_open_and_sums_amount(self):
        self.opp_in_stage(1500, "won")
        self.opp_in_stage(1000, "negotiation")
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 600, "won": 1500})

    def test_lost_is_excluded_from_every_field(self):
        self.opp_in_stage(5000, "lost")
        self.opp_in_stage(1000, "proposal")
        self.assertEqual(self.crm.forecast(), {"open": 1, "weighted": 300, "won": 0})

    def test_discounted_amount_is_what_gets_weighted(self):
        opp = self.opp_in_stage(1000, "proposal")
        self.crm.discount(opp, 10, "m1")                        # 900
        self.assertEqual(self.crm.forecast()["weighted"], 270)
        self.crm.advance(opp, "negotiation", "m1")
        self.assertEqual(self.crm.forecast()["weighted"], 540)

    def test_won_after_discount_counts_the_discounted_amount(self):
        opp = self.opp_in_stage(1000, "negotiation")
        self.crm.discount(opp, 10, "m1")
        self.crm.advance(opp, "won", "m1")
        self.assertEqual(self.crm.forecast(), {"open": 0, "weighted": 0, "won": 900})

    def test_forecast_needs_no_actor_and_logs_nothing(self):
        opp = opportunity(self.crm, 1000)
        before = list(self.crm.log)
        self.crm.advance(opp, "lost", "m1")
        forecast = self.crm.forecast()
        self.assertEqual(self.crm.log, before + [("advance", opp, "m1")])
        self.assertNotIn("forecast", [entry[0] for entry in self.crm.log])
        self.assertEqual(forecast, {"open": 0, "weighted": 0, "won": 0})

    def test_forecast_is_a_plain_dict_of_three_ints(self):
        forecast = self.crm.forecast()
        self.assertIsInstance(forecast, dict)
        self.assertEqual(sorted(forecast), ["open", "weighted", "won"])
        for value in forecast.values():
            self.assertIsInstance(value, int)
            self.assertNotIsInstance(value, bool)

    def test_forecast_does_not_mutate_state(self):
        self.opp_in_stage(1000, "negotiation")
        baseline = repr([self.crm.leads, self.crm.opps, self.crm.log])
        self.crm.forecast()
        self.crm.forecast()
        self.assertEqual(repr([self.crm.leads, self.crm.opps, self.crm.log]), baseline)


if __name__ == "__main__":
    unittest.main()
