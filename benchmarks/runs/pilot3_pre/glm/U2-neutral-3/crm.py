"""CRM module: leads, opportunities, and workload distribution."""

_NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_FINAL_STAGES = {"won", "lost"}
_SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead email, existing lead %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = {"role": rep["role"], "capacity": rep["capacity"]}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._next_lead_id = 1
        self._next_opp_id = 1
        self._waiting = []  # FIFO of lead ids

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %s" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, user_id):
        count = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                count += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in _FINAL_STAGES:
                count += 1
        return count

    def _pick_owner(self):
        best = None
        for uid in sorted(self.users):
            user = self.users[uid]
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= user["capacity"]:
                continue
            if best is None:
                best = uid
                continue
            if load < self._load(best):
                best = uid
        return best

    def _can_touch(self, opp_or_lead, actor):
        return opp_or_lead["owner"] == actor or self._is_manager(actor)

    def _free_slot(self, owner_id):
        while self._waiting and self._load(owner_id) < self.users[owner_id]["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = owner_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------ #
    # methods
    # ------------------------------------------------------------------ #
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("email domain is invalid")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in _SOURCE_SCORE:
            raise ValueError("source must be 'web', 'referral' or 'event'")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        lead_id = "L%d" % self._next_lead_id
        self._next_lead_id += 1
        score = _SOURCE_SCORE[source]
        if domain not in _FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
        lead = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
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
        if lead_id not in self.leads:
            raise ValueError("lead %s does not exist" % (lead_id,))
        lead = self.leads[lead_id]
        if not self._can_touch(lead, actor):
            raise PermissionError("actor is not the lead owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("lead %s does not exist" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if not self._can_touch(lead, actor):
            raise PermissionError("actor is not the lead owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        opp_id = "O%d" % self._next_opp_id
        self._next_opp_id += 1
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
        if opp_id not in self.opps:
            raise ValueError("opportunity %s does not exist" % (opp_id,))
        all_stages = {"prospect", "proposal", "negotiation", "won", "lost"}
        if stage not in all_stages:
            raise ValueError("invalid stage: %r" % (stage,))
        opp = self.opps[opp_id]
        if not self._can_touch(opp, actor):
            raise PermissionError("actor is not the opportunity owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost" and _NEXT_STAGE.get(opp["stage"]) != stage:
            raise ValueError("stage %s cannot move to %s" % (opp["stage"], stage))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("moving to negotiation above 50000 requires a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("opportunity %s does not exist" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if not self._can_touch(opp, actor):
            raise PermissionError("actor is not the opportunity owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount is at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("opportunity %s does not exist" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner's load is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in _FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
