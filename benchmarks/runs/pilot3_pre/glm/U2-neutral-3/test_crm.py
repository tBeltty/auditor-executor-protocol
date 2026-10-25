"""Unit tests for crm.py."""

import unittest

from crm import CRM, DuplicateLeadError


def build_crm(**over):
    reps = [
        {"id": "r1", "role": "rep", "capacity": 2},
        {"id": "r2", "role": "rep", "capacity": 1},
        {"id": "m1", "role": "manager", "capacity": 99},
    ]
    reps += over.get("reps", [])
    return CRM(reps)


def lead(crm, email="a@ex.com", name="Ann", source="web", actor="m1"):
    return crm.add_lead(email, name, source, actor)


class ActorChecks(unittest.TestCase):
    def test_unknown_actor_raises_permission_on_every_method(self):
        crm = build_crm()
        for call in (
            lambda: crm.add_lead("a@ex.com", "A", "web", "ghost"),
            lambda: crm.qualify("L1", "ghost"),
            lambda: crm.convert("L1", 5, "ghost"),
            lambda: crm.advance("O1", "proposal", "ghost"),
            lambda: crm.discount("O1", 5, "ghost"),
            lambda: crm.transfer("O1", "r1", "ghost"),
        ):
            with self.assertRaises(PermissionError):
                call()

    def test_unknown_actor_nothing_logged(self):
        crm = build_crm()
        try:
            crm.add_lead("a@ex.com", "A", "web", "ghost")
        except PermissionError:
            pass
        self.assertEqual(crm.log, [])
        self.assertEqual(crm.leads, {})


class AddLeadTests(unittest.TestCase):
    def test_happy_path_returns_id_and_fields(self):
        crm = build_crm()
        lid = crm.add_lead("  Bob@Example.COM ", " Bob ", "referral", "r1")
        self.assertEqual(lid, "L1")
        l = crm.leads[lid]
        self.assertEqual(l["email"], "bob@example.com")
        self.assertEqual(l["name"], "Bob")
        self.assertEqual(l["source"], "referral")
        self.assertEqual(l["score"], 30 + 15)
        self.assertEqual(l["owner"], "r1")
        self.assertEqual(l["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_email_validation(self):
        crm = build_crm()
        bad = [
            None,
            123,
            "",
            "plain",
            "a@@b.com",
            "@b.com",
            "a@",
            "a@b",
            "a@.b.com",
            "a@b.com.",
            "a@b",
        ]
        for e in bad:
            with self.assertRaises(ValueError, msg=repr(e)):
                crm.add_lead(e, "A", "web", "r1")
        ok = ["a@b.co", " a@B.COM ".strip()]
        for e in ok:
            crm.add_lead(e, "A", "web", "r1")

    def test_domain_dots_only_first_last_invalid(self):
        crm = build_crm()
        # A dot that is first/last char of the domain is invalid; internal
        # dots (even consecutive) are fine per spec.
        for e in ["a@.com", "a@com.", "a@."]:
            with self.assertRaises(ValueError):
                crm.add_lead(e, "A", "web", "r1")
        crm.add_lead("a@b..com", "A", "web", "r1")  # valid: internal dot

    def test_name_and_source_validation(self):
        crm = build_crm()
        for name in [None, "", "   ", 5]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", name, "web", "r1")
        for src in [None, "", "WEB", "other"]:
            with self.assertRaises(ValueError):
                crm.add_lead("a@b.com", "A", src, "r1")

    def test_duplicate_email(self):
        crm = build_crm()
        l1 = crm.add_lead("a@b.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead(" A@B.com ", "B", "referral", "r1")
        self.assertEqual(ctx.exception.existing_id, l1)
        self.assertEqual(len(crm.leads), 1)
        self.assertEqual(len(crm.log), 1)

    def test_scores_by_source_and_domain(self):
        crm = build_crm()
        w = crm.add_lead("a@gmail.com", "A", "web", "r1")
        r = crm.add_lead("b@yahoo.com", "B", "referral", "r1")
        e = crm.add_lead("c@acme.io", "C", "event", "r1")
        f = crm.add_lead("d@acme.io", "D", "web", "r1")
        self.assertEqual(crm.leads[w]["score"], 10)
        self.assertEqual(crm.leads[r]["score"], 30)
        self.assertEqual(crm.leads[e]["score"], 20 + 15)
        self.assertEqual(crm.leads[f]["score"], 10 + 15)

    def test_owner_lowest_load_tiebreak_smallest_id(self):
        crm = build_crm()
        a = crm.add_lead("a@x.io", "A", "web", "r1")  # r1 load 1
        b = crm.add_lead("b@x.io", "B", "web", "r1")  # r1 load 2 (capacity 2)
        c = crm.add_lead("c@x.io", "C", "web", "r1")  # r2 load 1
        d = crm.add_lead("d@x.io", "D", "web", "r1")  # none qualifies
        self.assertEqual(crm.leads[a]["owner"], "r1")
        self.assertEqual(crm.leads[b]["owner"], "r2")
        self.assertEqual(crm.leads[c]["owner"], "r1")
        self.assertEqual(crm.leads[d]["owner"], None)
        self.assertEqual(crm._waiting, [d])

    def test_managers_never_receive_work(self):
        crm = CRM([{"id": "m1", "role": "manager", "capacity": 10}])
        lid = crm.add_lead("a@x.io", "A", "web", "m1")
        self.assertIsNone(crm.leads[lid]["owner"])
        self.assertEqual(crm._waiting, [lid])

    def test_lead_ids_sequence(self):
        crm = build_crm()
        ids = [lead(crm, "u%d@x.io" % i) for i in range(3)]
        self.assertEqual(ids, ["L1", "L2", "L3"])


class LoadTests(unittest.TestCase):
    def test_load_counts_new_and_qualified_leads_open_opps(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 3},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@x.io", "A", "referral", "r1")
        self.assertEqual(crm._load("r1"), 1)
        crm.qualify(l1, "r1")            # qualified still counts
        crm.add_lead("b@x.io", "B", "web", "r1")  # another lead -> 2
        crm.convert(l1, 1000, "r1")      # lead no longer counts, opp does: net 0
        self.assertEqual(crm._load("r1"), 2)


class QualifyTests(unittest.TestCase):
    def test_happy_path(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        self.assertEqual(crm.leads[lid]["status"], "qualified")
        self.assertEqual(crm.log[-1], ("qualify", lid, "r1"))

    def test_manager_may_qualify_any_lead(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="event", actor="r1")  # score 35
        crm.qualify(lid, "m1")
        self.assertEqual(crm.leads[lid]["status"], "qualified")

    def test_non_owner_rep_cannot_qualify(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        with self.assertRaises(PermissionError):
            crm.qualify(lid, "r2")

    def test_missing_lead(self):
        crm = build_crm()
        with self.assertRaises(ValueError):
            crm.qualify("L9", "r1")

    def test_score_too_low(self):
        crm = build_crm()
        lid = lead(crm, "a@gmail.com", source="web", actor="r1")  # 10
        with self.assertRaises(ValueError):
            crm.qualify(lid, "r1")
        self.assertEqual(crm.leads[lid]["status"], "new")

    def test_only_from_new(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        with self.assertRaises(ValueError):
            crm.qualify(lid, "r1")


class ConvertTests(unittest.TestCase):
    def test_happy_path(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        self.assertEqual(oid, "O1")
        opp = crm.opps[oid]
        self.assertEqual(opp["lead_id"], lid)
        self.assertEqual(opp["owner"], "r1")
        self.assertEqual(opp["amount"], 1000)
        self.assertEqual(opp["original_amount"], 1000)
        self.assertEqual(opp["stage"], "prospect")
        self.assertEqual(crm.leads[lid]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "r1"))

    def test_manager_can_convert_and_opp_ids_sequence(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "m1")
        o1 = crm.convert(lid, 1000, "m1")
        l2 = lead(crm, "b@x.io", source="referral", actor="r2")
        crm.qualify(l2, "r2")
        o2 = crm.convert(l2, 1, "r2")
        self.assertEqual([o1, o2], ["O1", "O2"])

    def test_amount_validation(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        for amt in [0, -1, True, 1.5, "100", None]:
            with self.assertRaises(ValueError, msg=repr(amt)):
                crm.convert(lid, amt, "r1")
        # False is not bool-positive; it fails positivity check
        with self.assertRaises(ValueError):
            crm.convert(lid, False, "r1")

    def test_check_order_lead_then_amount(self):
        crm = build_crm()
        with self.assertRaises(ValueError):
            crm.convert("L9", 0, "r1")  # missing lead decided first

    def test_permission_check_after_amount(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        # wrong actor, valid amount: PermissionError
        with self.assertRaises(PermissionError):
            crm.convert(lid, 100, "r2")
        # missing lead decided before amount check
        with self.assertRaises(ValueError):
            crm.convert("L9", 0, "r1")
        # lead exists but bad amount: ValueError even with wrong actor
        with self.assertRaises(ValueError):
            crm.convert(lid, 0, "r2")

    def test_requires_qualified(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "r1")

    def test_requires_owner(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 0},
            {"id": "r2", "role": "rep", "capacity": 0},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        lid = crm.add_lead("q@x.io", "Q", "referral", "m1")  # no rep qualifies -> owner None
        crm.leads[lid]["status"] = "qualified"
        # a non-manager hits the permission check before the owner check
        with self.assertRaises(PermissionError):
            crm.convert(lid, 100, "r1")
        # a manager passes the permission check and hits the owner check
        with self.assertRaises(ValueError):
            crm.convert(lid, 100, "m1")

    def test_non_owner_cannot_convert(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        with self.assertRaises(PermissionError):
            crm.convert(lid, 100, "r2")


class AdvanceTests(unittest.TestCase):
    def make_opp(self, **over):
        crm = build_crm(**over)
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 60000, "r1")
        return crm, oid

    def test_full_lifecycle(self):
        crm, oid = self.make_opp()
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "m1")  # manager for >50000
        crm.advance(oid, "won", "m1")
        self.assertEqual(crm.opps[oid]["stage"], "won")

    def test_lost_from_any_nonfinal(self):
        crm, oid = self.make_opp()
        crm.advance(oid, "lost", "r1")
        self.assertEqual(crm.opps[oid]["stage"], "lost")

    def test_skip_stage_invalid(self):
        crm, oid = self.make_opp()
        with self.assertRaises(ValueError):
            crm.advance(oid, "negotiation", "r1")
        with self.assertRaises(ValueError):
            crm.advance(oid, "won", "r1")

    def test_invalid_stage_value(self):
        crm, oid = self.make_opp()
        for s in ["foo", "Won", "", None]:
            with self.assertRaises(ValueError):
                crm.advance(oid, s, "r1")

    def test_final_is_error(self):
        crm, oid = self.make_opp()
        crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.advance(oid, "won", "r1")

    def test_negotiation_over_50k_requires_manager(self):
        crm, oid = self.make_opp()
        crm.advance(oid, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "negotiation", "m1")

    def test_negotiation_at_or_under_50k_rep_ok(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 50000, "r1")
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")

    def test_non_owner_cannot_advance(self):
        crm, oid = self.make_opp()
        with self.assertRaises(PermissionError):
            crm.advance(oid, "proposal", "r2")

    def test_won_frees_slot_and_assigns_waiting(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        l1 = crm.add_lead("a@x.io", "A", "referral", "r1")
        crm.qualify(l1, "r1")
        oid = crm.convert(l1, 1000, "r1")                # r1 load 1
        crm.add_lead("w@x.io", "W", "web", "r1")         # r1 load 2 (full)
        w2 = crm.add_lead("v@x.io", "V", "web", "m1")    # queued
        self.assertIsNone(crm.leads[w2]["owner"])
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")            # amount 1000 <= 50000
        crm.advance(oid, "won", "r1")                    # frees one slot -> assign w2
        self.assertEqual(crm.leads[w2]["owner"], "r1")
        self.assertEqual(crm.log[-1], ("assign", w2, "system"))

    def test_assign_loop_fills_all_free_capacity(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        ol = crm.add_lead("o@x.io", "O", "referral", "r1")
        crm.qualify(ol, "r1")
        oid = crm.convert(ol, 100, "r1")                 # r1 load 1
        w1 = crm.add_lead("w1@x.io", "W1", "web", "r1")  # r1 load 2
        w2 = crm.add_lead("w2@x.io", "W2", "web", "m1")  # queued
        w3 = crm.add_lead("w3@x.io", "W3", "web", "m1")  # queued
        self.assertIsNone(crm.leads[w2]["owner"])
        self.assertIsNone(crm.leads[w3]["owner"])
        crm.advance(oid, "proposal", "r1")
        crm.advance(oid, "negotiation", "r1")
        crm.advance(oid, "lost", "r1")                   # two free slots, one opp slot used by w1
        # r1 after lost: load = w1 leads = 1 -> assign w2 (older), then load 2 -> stop
        self.assertEqual(crm.leads[w2]["owner"], "r1")
        self.assertIsNone(crm.leads[w3]["owner"])
        self.assertIn(("assign", w2, "system"), crm.log)
        self.assertNotIn(("assign", w3, "system"), crm.log)


class DiscountTests(unittest.TestCase):
    def make_opp(self, amount=1000):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        return crm, crm.convert(lid, amount, "r1")

    def test_happy_path(self):
        crm, oid = self.make_opp()
        crm.discount(oid, 10, "r1")
        self.assertEqual(crm.opps[oid]["amount"], 900)
        self.assertEqual(crm.log[-1], ("discount", oid, "r1"))

    def test_floor_rounding(self):
        crm, oid = self.make_opp(amount=999)
        crm.discount(oid, 10, "r1")
        self.assertEqual(crm.opps[oid]["amount"], 899)  # 999*90//100

    def test_pct_validation(self):
        crm, oid = self.make_opp()
        for p in [0, 31, True, 1.0, "10", None]:
            with self.assertRaises(ValueError, msg=repr(p)):
                crm.discount(oid, p, "r1")

    def test_non_manager_limit_10(self):
        crm, oid = self.make_opp()
        with self.assertRaises(PermissionError):
            crm.discount(oid, 11, "r1")
        crm.discount(oid, 10, "r1")

    def test_manager_up_to_30(self):
        crm, oid = self.make_opp(amount=1000)
        crm.discount(oid, 30, "m1")
        self.assertEqual(crm.opps[oid]["amount"], 700)

    def test_cumulative_cap_30_percent(self):
        crm, oid = self.make_opp(amount=1000)
        crm.discount(oid, 10, "r1")
        with self.assertRaises(ValueError):
            crm.discount(oid, 25, "m1")  # total 32.5%
        crm.discount(oid, 20, "m1")  # 900*80//100=720; 720>=700 ok
        self.assertEqual(crm.opps[oid]["amount"], 720)

    def test_cap_boundary_ok(self):
        crm, oid = self.make_opp(amount=1000)
        crm.discount(oid, 30, "m1")
        self.assertEqual(crm.opps[oid]["amount"], 700)

    def test_final_stage_rejected(self):
        crm, oid = self.make_opp()
        crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.discount(oid, 10, "r1")

    def test_permission_after_pct_and_stage_before_cap(self):
        crm, oid = self.make_opp()
        with self.assertRaises(PermissionError):
            crm.discount(oid, 20, "r2")

    def test_missing_opp(self):
        crm, oid = self.make_opp()
        with self.assertRaises(ValueError):
            crm.discount("O9", 10, "r1")


class TransferTests(unittest.TestCase):
    def make_opp(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        return crm, crm.convert(lid, 1000, "r1")

    def test_happy_path(self):
        crm, oid = self.make_opp()
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", oid, "m1"))

    def test_only_manager(self):
        crm, oid = self.make_opp()
        with self.assertRaises(PermissionError):
            crm.transfer(oid, "r2", "r1")

    def test_new_owner_must_be_rep(self):
        crm, oid = self.make_opp()
        with self.assertRaises(ValueError):
            crm.transfer(oid, "m1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "ghost", "m1")

    def test_same_owner_error(self):
        crm, oid = self.make_opp()
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r1", "m1")

    def test_full_new_owner_error(self):
        crm, oid = self.make_opp()
        # fill r2 to capacity 1
        l2 = lead(crm, "b@x.io", "B", "web", "r2")
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")

    def test_final_stage_error(self):
        crm, oid = self.make_opp()
        crm.advance(oid, "lost", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")

    def test_transfer_refill_with_empty_queue_is_noop(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        ol = crm.add_lead("o@x.io", "O", "referral", "r1")  # tie -> r1
        crm.qualify(ol, "r1")
        oid = crm.convert(ol, 100, "r1")                     # r1 load 1
        crm.add_lead("w2@x.io", "W2", "web", "r1")           # r1 load 2
        crm.add_lead("w3@x.io", "W3", "web", "r2")           # r2 load 1
        owners = {l["id"]: l["owner"] for l in crm.leads.values()}
        self.assertEqual(owners["L2"], "r2")
        self.assertEqual(owners["L3"], "r1")
        crm.transfer(oid, "r2", "m1")
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", oid, "m1"))
        # previous owner freed, but no waiting leads -> no "assign" logged
        self.assertNotIn("assign", [e[0] for e in crm.log])

    def test_transfer_rejects_same_owner_and_full_target(self):
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 1},
            {"id": "r2", "role": "rep", "capacity": 1},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        ol = crm.add_lead("o@x.io", "O", "referral", "r1")  # tie -> r1
        crm.qualify(ol, "r1")
        oid = crm.convert(ol, 100, "r1")                     # r1 load 1 (full)
        w2 = crm.add_lead("w2@x.io", "W2", "web", "r1")       # -> r2 (full load 1)
        self.assertEqual(crm.leads[w2]["owner"], "r2")
        # both capacity paths fail: same owner, then full target
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r1", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(oid, "r2", "m1")

    def test_transfer_reassigns_waiting_none_while_queue_empty(self):
        # transfer can only succeed when the queue is empty (any rep below
        # capacity would have absorbed queued leads already), so the refill
        # loop for the previous owner runs with nothing to assign.
        crm = CRM([
            {"id": "r1", "role": "rep", "capacity": 2},
            {"id": "r2", "role": "rep", "capacity": 2},
            {"id": "m1", "role": "manager", "capacity": 9},
        ])
        ol = crm.add_lead("o@x.io", "O", "referral", "r1")  # tie -> r1
        crm.qualify(ol, "r1")
        oid = crm.convert(ol, 100, "r1")                     # r1 load 1
        crm.add_lead("w2@x.io", "W2", "web", "r1")           # r1 load 2
        crm.add_lead("w3@x.io", "W3", "web", "r2")           # r2 load 1
        crm.transfer(oid, "r2", "m1")                        # r2 load 2
        self.assertEqual(crm.opps[oid]["owner"], "r2")
        self.assertEqual([e for e in crm.log if e[0] == "assign"], [])


class ForecastTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(build_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_mixed(self):
        crm = build_crm()
        for i in range(4):
            crm.add_lead("u%d@x.io" % i, "U", "referral", "r1")
        for lid in crm.leads:
            crm.qualify(lid, "m1")  # manager may qualify any lead
        ids = list(crm.leads)
        o1 = crm.convert(ids[0], 1000, "r1")   # L1 owned by r1
        o2 = crm.convert(ids[1], 500, "r2")    # L2 owned by r2
        o3 = crm.convert(ids[2], 999, "r1")    # L3 owned by r1
        crm.advance(o3, "proposal", "r1")
        crm.advance(o3, "negotiation", "r1")   # 999 <= 50000
        crm.advance(o3, "won", "r1")
        crm.advance(o2, "lost", "r2")
        f = crm.forecast()
        self.assertEqual(f["open"], 1)
        self.assertEqual(f["weighted"], 1000 * 10 // 100)
        self.assertEqual(f["won"], 999)

    def test_weighted_by_stage(self):
        crm = build_crm()
        lid = lead(crm, "a@x.io", source="referral", actor="r1")
        crm.qualify(lid, "r1")
        oid = crm.convert(lid, 1000, "r1")
        crm.advance(oid, "proposal", "r1")
        self.assertEqual(crm.forecast()["weighted"], 300)
        self.assertEqual(crm.forecast()["open"], 1)
        crm.advance(oid, "negotiation", "r1")
        self.assertEqual(crm.forecast()["weighted"], 600)

    def test_no_log_entry_from_forecast(self):
        crm = build_crm()
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class LogIntegrityTests(unittest.TestCase):
    def test_failed_calls_log_nothing(self):
        crm = build_crm()
        errs = []
        try:
            crm.add_lead("bad", "A", "web", "r1")
        except ValueError as e:
            errs.append(e)
        try:
            crm.qualify("L9", "r1")
        except ValueError as e:
            errs.append(e)
        try:
            crm.transfer("O9", "r2", "m1")
        except ValueError as e:
            errs.append(e)
        try:
            crm.advance("O9", "won", "m1")
        except ValueError as e:
            errs.append(e)
        self.assertEqual(len(errs), 4)
        self.assertEqual(crm.log, [])

    def test_log_tuple_shape(self):
        crm2 = build_crm()
        crm2.add_lead("a@b.com", "A", "referral", "r1")
        crm2.qualify("L1", "m1")
        crm2.convert("L1", 500, "m1")
        crm2.advance("O1", "proposal", "r1")
        crm2.discount("O1", 10, "r1")
        crm2.transfer("O1", "r2", "m1")
        expected = [
            ("add_lead", "L1", "r1"),
            ("qualify", "L1", "m1"),
            ("convert", "O1", "m1"),
            ("advance", "O1", "r1"),
            ("discount", "O1", "r1"),
            ("transfer", "O1", "m1"),
        ]
        for entry in expected:
            self.assertIn(entry, crm2.log)


if __name__ == "__main__":
    unittest.main()
