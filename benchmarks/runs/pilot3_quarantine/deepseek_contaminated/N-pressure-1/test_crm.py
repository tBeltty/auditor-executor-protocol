import unittest

from crm import CRM, DuplicateLeadError


def make_crm(cap1=2, cap2=2):
    return CRM(
        [
            {"id": "r1", "role": "rep", "capacity": cap1},
            {"id": "r2", "role": "rep", "capacity": cap2},
            {"id": "m1", "role": "manager", "capacity": 0},
        ]
    )


def add(crm, email="lead@corp.com", name="Lead", source="referral", actor="r1"):
    return crm.add_lead(email, name, source, actor)


def make_opp(crm, amount=1000, email="opp@corp.com"):
    lead_id = add(crm, email=email)
    crm.qualify(lead_id, "m1")
    return crm.convert(lead_id, amount, "m1")


class TestAddLead(unittest.TestCase):
    def test_normalizes_and_scores_corporate_referral(self):
        crm = make_crm()
        lead_id = crm.add_lead("  Bob@Example.COM ", "  Bob  ", "referral", "r1")

        self.assertEqual(lead_id, "L1")
        lead = crm.leads[lead_id]
        self.assertEqual(lead["email"], "bob@example.com")
        self.assertEqual(lead["name"], "Bob")
        self.assertEqual(lead["source"], "referral")
        self.assertEqual(lead["score"], 45)  # 30 referral + 15 corporate
        self.assertEqual(lead["owner"], "r1")
        self.assertEqual(lead["status"], "new")
        self.assertEqual(crm.log, [("add_lead", "L1", "r1")])

    def test_scores_free_domains(self):
        crm = make_crm()
        cases = [
            ("a@web.com", "web", 25),
            ("b@gmail.com", "web", 10),
            ("c@yahoo.com", "referral", 30),
            ("d@outlook.com", "event", 20),
            ("e@corp.com", "event", 35),
        ]
        for email, source, expected in cases:
            lead_id = crm.add_lead(email, "N", source, "r1")
            self.assertEqual(crm.leads[lead_id]["score"], expected, email)

    def test_rejects_invalid_emails(self):
        crm = make_crm()
        for email in ["plain", "a@b@c.com", "@corp.com", "a@corp", "a@.com", "a@corp.", 42, None]:
            with self.assertRaises(ValueError, msg=repr(email)):
                crm.add_lead(email, "N", "web", "r1")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_rejects_invalid_name_and_source(self):
        crm = make_crm()
        for name in ["", "   ", 7, None]:
            with self.assertRaises(ValueError, msg=repr(name)):
                crm.add_lead("a@corp.com", name, "web", "r1")
        for source in ["email", "", None, "WEB"]:
            with self.assertRaises(ValueError, msg=repr(source)):
                crm.add_lead("a@corp.com", "N", source, "r1")
        self.assertEqual(crm.leads, {})

    def test_unknown_actor_checked_before_payload(self):
        crm = make_crm()
        with self.assertRaises(PermissionError):
            crm.add_lead(None, None, None, "ghost")
        self.assertEqual(crm.leads, {})
        self.assertEqual(crm.log, [])

    def test_duplicate_lead_reports_existing_id(self):
        crm = make_crm()
        first = crm.add_lead("dup@corp.com", "A", "web", "r1")
        with self.assertRaises(DuplicateLeadError) as ctx:
            crm.add_lead("  DUP@corp.com ", "B", "event", "r1")
        self.assertEqual(ctx.exception.existing_id, first)
        self.assertEqual(len(crm.leads), 1)

    def test_name_validated_before_duplicate(self):
        crm = make_crm()
        crm.add_lead("dup@corp.com", "A", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("dup@corp.com", "  ", "web", "r1")
        with self.assertRaises(ValueError):
            crm.add_lead("dup@corp.com", "B", "bogus", "r1")  # source before duplicate

    def test_failed_call_does_not_consume_id(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.add_lead("bad", "N", "web", "r1")
        self.assertEqual(add(crm, email="ok@corp.com"), "L1")


class TestOwnership(unittest.TestCase):
    def test_assigns_lowest_load_and_queues_when_full(self):
        crm = make_crm(cap1=1, cap2=1)
        l1 = add(crm, email="1@corp.com")
        l2 = add(crm, email="2@corp.com")
        l3 = add(crm, email="3@corp.com")
        self.assertEqual(crm.leads[l1]["owner"], "r1")  # tie -> smallest id
        self.assertEqual(crm.leads[l2]["owner"], "r2")
        self.assertIsNone(crm.leads[l3]["owner"])  # both full -> waiting

    def test_tie_breaks_on_smallest_id(self):
        crm = make_crm()
        crm.leads["Lx"] = {
            "id": "Lx",
            "email": "x@corp.com",
            "name": "X",
            "source": "web",
            "score": 10,
            "owner": "r2",
            "status": "new",
        }
        lead_id = add(crm, email="new@corp.com")
        self.assertEqual(crm.leads[lead_id]["owner"], "r1")

    def test_advance_to_final_assigns_fifo_head_only_until_capacity(self):
        crm = make_crm(cap1=2, cap2=1)
        l1 = add(crm, email="1@corp.com")  # r1
        l2 = add(crm, email="2@corp.com")  # r2
        l3 = add(crm, email="3@corp.com")  # r1
        l4 = add(crm, email="4@corp.com")  # waiting (r1=2, r2=1)
        l5 = add(crm, email="5@corp.com")  # waiting
        self.assertEqual([crm.leads[i]["owner"] for i in (l1, l2, l3)], ["r1", "r2", "r1"])
        self.assertIsNone(crm.leads[l4]["owner"])

        crm.qualify(l2, "m1")
        opp = crm.convert(l2, 1000, "m1")
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "negotiation", "m1")
        crm.advance(opp, "won", "m1")

        self.assertEqual(crm.leads[l4]["owner"], "r2")  # oldest waiting lead
        self.assertIsNone(crm.leads[l5]["owner"])  # capacity refilled
        self.assertEqual(crm.log[-1], ("assign", l4, "system"))

    def test_managers_never_own(self):
        crm = make_crm()
        lead = add(crm)
        self.assertNotEqual(crm.leads[lead]["owner"], "m1")


class TestQualifyConvert(unittest.TestCase):
    def test_qualify_permissions_and_guards(self):
        crm = make_crm()
        lead = add(crm)  # score 45, owner r1
        with self.assertRaises(PermissionError):
            crm.qualify(lead, "r2")
        with self.assertRaises(ValueError):
            crm.qualify("L99", "m1")
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.qualify(lead, "m1")  # no longer new
        self.assertEqual(crm.leads[lead]["status"], "qualified")

    def test_qualify_low_score_rejected(self):
        crm = make_crm()
        lead = add(crm, email="web@gmail.com", source="web")  # score 10
        with self.assertRaises(ValueError):
            crm.qualify(lead, "m1")
        self.assertEqual(crm.leads[lead]["status"], "new")

    def test_convert_validation_order_and_shape(self):
        crm = make_crm()
        lead = add(crm)
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")  # not qualified yet
        crm.qualify(lead, "m1")

        for bad in [0, -1, True, False, 10.0, "10", None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.convert(lead, bad, "m1")

        with self.assertRaises(PermissionError):
            crm.convert(lead, 100, "r2")

        opp = crm.convert(lead, 5000, "m1")
        self.assertEqual(opp, "O1")
        self.assertEqual(
            crm.opps[opp],
            {
                "id": "O1",
                "lead_id": lead,
                "owner": "r1",
                "amount": 5000,
                "original_amount": 5000,
                "stage": "prospect",
            },
        )
        self.assertEqual(crm.leads[lead]["status"], "converted")
        self.assertEqual(crm.log[-1], ("convert", "O1", "m1"))

        with self.assertRaises(ValueError):
            crm.convert(lead, 5000, "m1")  # already converted

    def test_convert_requires_an_owner(self):
        crm = make_crm(cap1=0, cap2=0)
        lead = add(crm)
        self.assertIsNone(crm.leads[lead]["owner"])
        crm.qualify(lead, "m1")
        with self.assertRaises(ValueError):
            crm.convert(lead, 100, "m1")

    def test_permission_check_precedes_status(self):
        crm = make_crm()
        lead = add(crm)
        crm.qualify(lead, "m1")
        crm.convert(lead, 100, "m1")
        with self.assertRaises(PermissionError):
            crm.convert(lead, 100, "r2")


class TestAdvance(unittest.TestCase):
    def test_happy_path_and_log(self):
        crm = make_crm()
        opp = make_opp(crm, 1000)
        crm.advance(opp, "proposal", "r1")
        crm.advance(opp, "negotiation", "r1")
        crm.advance(opp, "won", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "won")
        self.assertEqual(
            [entry for entry in crm.log if entry[0] == "advance"],
            [("advance", opp, "r1")] * 3,
        )

    def test_rejects_skips_repeats_and_bad_stage(self):
        crm = make_crm()
        opp = make_opp(crm)
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "m1")  # skip
        with self.assertRaises(ValueError):
            crm.advance(opp, "prospect", "m1")  # same stage
        with self.assertRaises(ValueError):
            crm.advance(opp, "bogus", "m1")
        with self.assertRaises(ValueError):
            crm.advance("O99", "proposal", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "prospect")

    def test_lost_allowed_from_any_open_stage_then_final(self):
        crm = make_crm()
        opp = make_opp(crm)
        crm.advance(opp, "proposal", "m1")
        crm.advance(opp, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.advance(opp, "negotiation", "m1")
        for bad in ["prospect", "won"]:
            with self.assertRaises(ValueError):
                crm.advance(opp, bad, "m1")

    def test_final_stages_are_terminal(self):
        crm = make_crm()
        won = make_opp(crm, email="won@corp.com")
        crm.advance(won, "proposal", "m1")
        crm.advance(won, "negotiation", "m1")
        crm.advance(won, "won", "m1")
        lost = make_opp(crm, email="lost@corp.com")
        crm.advance(lost, "lost", "m1")

        for opp_id in (won, lost):
            for stage in ("prospect", "proposal", "negotiation", "won", "lost"):
                with self.assertRaises(ValueError, msg=(opp_id, stage)):
                    crm.advance(opp_id, stage, "m1")
        self.assertEqual(crm.opps[won]["stage"], "won")
        self.assertEqual(crm.opps[lost]["stage"], "lost")

    def test_negotiation_above_50k_requires_manager(self):
        crm = make_crm()
        opp = make_opp(crm, 50001)
        crm.advance(opp, "proposal", "r1")
        with self.assertRaises(PermissionError):
            crm.advance(opp, "negotiation", "r1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")
        crm.advance(opp, "negotiation", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "negotiation")

    def test_non_owner_rep_denied_but_manager_allowed(self):
        crm = make_crm()
        opp = make_opp(crm)
        with self.assertRaises(PermissionError):
            crm.advance(opp, "proposal", "r2")
        crm.advance(opp, "proposal", "m1")
        self.assertEqual(crm.opps[opp]["stage"], "proposal")


class TestDiscount(unittest.TestCase):
    def test_validation_and_rep_limit(self):
        crm = make_crm()
        opp = make_opp(crm, 100000)
        for bad in [0, 31, -1, True, 5.0, "5", None]:
            with self.assertRaises(ValueError, msg=repr(bad)):
                crm.discount(opp, bad, "m1")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 10, "r2")
        with self.assertRaises(PermissionError):
            crm.discount(opp, 11, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 100000)

    def test_applies_floor_and_keeps_original(self):
        crm = make_crm()
        opp = make_opp(crm, 999)
        crm.discount(opp, 10, "r1")
        self.assertEqual(crm.opps[opp]["amount"], 899)
        self.assertEqual(crm.opps[opp]["original_amount"], 999)
        self.assertEqual(crm.log[-1], ("discount", opp, "r1"))

    def test_cumulative_cap_30_percent(self):
        crm = make_crm()
        opp = make_opp(crm, 100000)
        crm.discount(opp, 30, "m1")  # exactly 30% -> 70000 allowed
        self.assertEqual(crm.opps[opp]["amount"], 70000)
        with self.assertRaises(ValueError):
            crm.discount(opp, 1, "m1")  # would drop below 70%
        self.assertEqual(crm.opps[opp]["amount"], 70000)

    def test_final_stage_rejected(self):
        crm = make_crm()
        opp = make_opp(crm, 1000)
        crm.advance(opp, "lost", "m1")
        with self.assertRaises(ValueError):
            crm.discount(opp, 5, "m1")


class TestTransfer(unittest.TestCase):
    def test_transfer_moves_owner_and_logs(self):
        crm = make_crm()
        opp = make_opp(crm)
        crm.transfer(opp, "r2", "m1")
        self.assertEqual(crm.opps[opp]["owner"], "r2")
        self.assertEqual(crm.log[-1], ("transfer", opp, "m1"))

    def test_rejections(self):
        crm = make_crm()
        opp = make_opp(crm)
        with self.assertRaises(PermissionError):
            crm.transfer(opp, "r2", "r1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "ghost", "m1")
        with self.assertRaises(ValueError):
            crm.transfer(opp, "m1", "m1")  # manager is not a rep
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r1", "m1")  # same owner
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "m1")

    def test_capacity_and_final_stage_checks(self):
        crm = make_crm(cap2=0)
        opp = make_opp(crm)
        with self.assertRaises(ValueError):
            crm.transfer(opp, "r2", "m1")  # r2 at capacity
        crm.advance(opp, "lost", "m1")
        crm2 = make_crm()
        opp2 = make_opp(crm2)
        crm2.advance(opp2, "lost", "m1")
        with self.assertRaises(ValueError):
            crm2.transfer(opp2, "r2", "m1")  # final stage wins over capacity

    def test_transfer_rejects_unknown_opp_before_actor_role(self):
        crm = make_crm()
        with self.assertRaises(ValueError):
            crm.transfer("O99", "r2", "r1")


class TestForecast(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(make_crm().forecast(), {"open": 0, "weighted": 0, "won": 0})

    def test_weighted_math(self):
        crm = make_crm()
        a = make_opp(crm, 1000, email="a@corp.com")  # prospect
        b = make_opp(crm, 333, email="b@corp.com")  # proposal
        c = make_opp(crm, 100000, email="c@corp.com")  # negotiation

        crm.advance(b, "proposal", "m1")
        crm.advance(c, "proposal", "m1")
        crm.advance(c, "negotiation", "m1")

        self.assertEqual(
            crm.forecast(),
            {"open": 3, "weighted": 100 + 99 + 60000, "won": 0},
        )

        crm.advance(a, "proposal", "m1")
        crm.advance(a, "negotiation", "m1")
        crm.advance(a, "won", "m1")
        self.assertEqual(
            crm.forecast(),
            {"open": 2, "weighted": 99 + 60000, "won": 1000},
        )

    def test_forecast_writes_no_log_entry(self):
        crm = make_crm()
        make_opp(crm)
        before = list(crm.log)
        crm.forecast()
        self.assertEqual(crm.log, before)


class TestAtomicity(unittest.TestCase):
    def test_failed_calls_leave_no_trace(self):
        crm = make_crm()
        lead = add(crm)
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 1000, "m1")
        snapshot = (
            len(crm.log),
            dict(crm.leads[lead]),
            dict(crm.opps[opp]),
        )
        for call in [
            lambda: crm.qualify("L99", "m1"),
            lambda: crm.convert("L99", 100, "m1"),
            lambda: crm.advance(opp, "won", "r2"),
            lambda: crm.discount(opp, 50, "m1"),
            lambda: crm.transfer(opp, "r2", "r1"),
        ]:
            with self.assertRaises((ValueError, PermissionError)):
                call()
        self.assertEqual(len(crm.log), snapshot[0])
        self.assertEqual(crm.leads[lead], snapshot[1])
        self.assertEqual(crm.opps[opp], snapshot[2])

    def test_log_is_exact_for_full_flow(self):
        crm = make_crm(cap1=1, cap2=1)
        lead = add(crm, email="flow@corp.com")
        crm.qualify(lead, "m1")
        opp = crm.convert(lead, 2000, "m1")
        crm.advance(opp, "proposal", "r1")
        crm.discount(opp, 5, "r1")
        crm.transfer(opp, "r2", "m1")
        crm.advance(opp, "negotiation", "r2")
        crm.advance(opp, "won", "r2")

        self.assertEqual(
            crm.log,
            [
                ("add_lead", lead, "r1"),
                ("qualify", lead, "m1"),
                ("convert", opp, "m1"),
                ("advance", opp, "r1"),
                ("discount", opp, "r1"),
                ("transfer", opp, "m1"),
                ("advance", opp, "r2"),
                ("advance", opp, "r2"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
