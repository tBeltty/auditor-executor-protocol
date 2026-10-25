"""CRM module per spec crm.md: lead intake, capacity routing, pipeline, forecasting."""

FINAL_STAGES = ("won", "lost")
ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead for existing id %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {u["id"]: u for u in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO list of lead ids with no owner
        self._lead_seq = 0
        self._opp_seq = 0

    # -- helpers -----------------------------------------------------------

    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _can_act_on(self, actor, owner_id):
        return actor == owner_id or self._is_manager(actor)

    def _load(self, rep_id):
        n = sum(
            1
            for lead in self.leads.values()
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified")
        )
        n += sum(
            1
            for opp in self.opps.values()
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES
        )
        return n

    def _is_final(self, opp):
        return opp["stage"] in FINAL_STAGES

    def _fill_owner_slots(self, rep_id):
        """Assign oldest waiting leads to rep while load is below capacity."""
        user = self.users.get(rep_id)
        if user is None or user["role"] != "rep":
            return
        while self._waiting and self._load(rep_id) < user["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- public API --------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        # 1. email validation
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
            raise ValueError("email domain must contain a dot that is neither first nor last")

        # 2. name validation
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        # 3. source validation
        if source not in SOURCE_SCORES:
            raise ValueError("source must be web, referral or event")

        # 4. duplicate check
        for lead_id, lead in self.leads.items():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead_id)

        # 5. id and score
        score = SOURCE_SCORES[source]
        if domain not in FREE_DOMAINS:
            score += 15

        # 6. owner selection: lowest load under capacity, ties by id string order
        owner = None
        best = None
        for uid, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= user["capacity"]:
                continue
            if best is None or (load, uid) < best:
                best = (load, uid)
        if best is not None:
            owner = best[1]

        # 7. create
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("no such lead: %r" % (lead_id,))
        if not self._can_act_on(actor, lead["owner"]):
            raise PermissionError("only the owner or a manager may qualify")
        if lead["status"] != "new":
            raise ValueError("lead status must be new")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("no such lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._can_act_on(actor, lead["owner"]):
            raise PermissionError("only the owner or a manager may convert")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
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
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("no such opportunity: %r" % (opp_id,))
        if stage not in ALL_STAGES:
            raise ValueError("invalid stage")
        if not self._can_act_on(actor, opp["owner"]):
            raise PermissionError("only the owner or a manager may advance")
        if self._is_final(opp):
            raise ValueError("opportunity is in a final stage")
        if stage != "lost" and NEXT_STAGE.get(opp["stage"]) != stage:
            raise ValueError("stage must be lost or the immediate next stage")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required to negotiate large deals")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._fill_owner_slots(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("no such opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if not self._can_act_on(actor, opp["owner"]):
            raise PermissionError("only the owner or a manager may discount")
        if self._is_final(opp):
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("no such opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        target = self.users.get(new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        if self._is_final(opp):
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from current owner")
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new_owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill_owner_slots(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            if self._is_final(opp):
                if opp["stage"] == "won":
                    won_total += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
