"""crm.py — minimal CRM per spec (specs/crm.md)."""


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead email: %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    _SCORES = {"web": 10, "referral": 30, "event": 20}
    _FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
    _STAGES = ("prospect", "proposal", "negotiation", "won")
    _FINAL = ("won", "lost")
    _WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

    def __init__(self, reps):
        self._users = {}
        for r in reps:
            self._users[r["id"]] = {
                "id": r["id"],
                "role": r["role"],
                "capacity": r["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._next_lead = 1
        self._next_opp = 1
        self._waiting = []  # FIFO of lead ids with no owner

    # -- helpers -----------------------------------------------------------

    def _check_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in self._FINAL:
                n += 1
        return n

    def _can_take_work(self, user_id):
        user = self._users.get(user_id)
        return (
            user is not None
            and user["role"] == "rep"
            and self._load(user_id) < user["capacity"]
        )

    def _pick_owner(self):
        candidates = [uid for uid in self._users if self._can_take_work(uid)]
        if not candidates:
            return None
        candidates.sort(key=lambda uid: (self._load(uid), uid))
        return candidates[0]

    def _drain_waiting(self, rep_id):
        if rep_id is None:
            return
        while self._can_take_work(rep_id) and self._waiting:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- methods -----------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        # 1. email
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if "." not in domain[1:-1]:
            raise ValueError("invalid email domain")

        # 2. name
        if not isinstance(name, str):
            raise ValueError("name must be a str")
        stripped_name = name.strip()
        if not stripped_name:
            raise ValueError("name must be non-empty")

        # 3. source
        if source not in self._SCORES:
            raise ValueError("invalid source")

        # 4. duplicate normalized email
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(existing_id=lead["id"])

        lead_id = "L%d" % self._next_lead
        self._next_lead += 1
        score = self._SCORES[source]
        if domain not in self._FREE_DOMAINS:
            score += 15

        owner = self._pick_owner()
        lead = {
            "id": lead_id,
            "email": normalized,
            "name": stripped_name,
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lead_id] = lead
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not the lead's owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not the lead's owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        opp_id = "O%d" % self._next_opp
        self._next_opp += 1
        self.opps[opp_id] = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in ("prospect", "proposal", "negotiation", "won", "lost"):
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not the opportunity's owner or a manager")
        if opp["stage"] in self._FINAL:
            raise ValueError("opportunity stage is final")
        next_stage = self._STAGES[self._STAGES.index(opp["stage"]) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("stage must be 'lost' or the immediate next stage")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("moving to negotiation over 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self._FINAL:
            self._drain_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not the opportunity's owner or a manager")
        if opp["stage"] in self._FINAL:
            raise ValueError("opportunity stage is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount cap is 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager can transfer")
        user = self._users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        if opp["stage"] in self._FINAL:
            raise ValueError("opportunity stage is final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if not self._can_take_work(new_owner):
            raise ValueError("new_owner's load is not below its capacity")

        old_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._drain_waiting(old_owner)

    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in self._FINAL]
        weighted = sum(
            o["amount"] * self._WEIGHTS[o["stage"]] // 100 for o in open_opps
        )
        won = sum(o["amount"] for o in self.opps.values() if o["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
