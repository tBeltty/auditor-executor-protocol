"""Small in-memory CRM: leads, opportunities, assignment and approvals."""

FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
ALL_STAGES = {"prospect", "proposal", "negotiation", "won", "lost"}
FINAL_STAGES = {"won", "lost"}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % (existing_id,))


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = {"role": rep["role"], "capacity": rep["capacity"]}
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # -- internals ---------------------------------------------------------
    def _actor(self, actor):
        # >>> guard:actor
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))
        # <<< guard:actor
        return actor

    def _role(self, uid):
        user = self.users.get(uid) if isinstance(uid, str) else None
        return user["role"] if user else None

    def _is_manager(self, actor):
        return self._role(actor) == "manager"

    def _allowed(self, owner, actor):
        # >>> guard:permission
        if actor != owner and not self._is_manager(actor):
            raise PermissionError("%s may not act on this record" % (actor,))
        # <<< guard:permission

    def _load(self, uid):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == uid and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == uid and opp["stage"] not in FINAL_STAGES:
                total += 1
        return total

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    def _pick_rep(self):
        candidates = []
        for rid in sorted(self.users):
            user = self.users[rid]
            if user["role"] != "rep":
                continue
            # >>> guard:capacity
            if self._load(rid) >= user["capacity"]:
                continue
            # <<< guard:capacity
            candidates.append((self._load(rid), rid))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][1]

    def _free_slots(self, rid):
        capacity = self.users[rid]["capacity"]
        # >>> guard:drain
        while self.waiting and self._load(rid) < capacity:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = rid
            self.log.append(("assign", lead_id, "system"))
        # <<< guard:drain

    # -- operations --------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._actor(actor)
        # >>> guard:email
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("email must have a local part")
        if not any(ch == "." and 0 < i < len(domain) - 1 for i, ch in enumerate(domain)):
            raise ValueError("email domain must contain an internal dot")
        # <<< guard:email
        # >>> guard:name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        # <<< guard:name
        # >>> guard:source
        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("source must be web, referral or event")
        # <<< guard:source
        # >>> guard:duplicate
        for existing in self.leads.values():
            if existing["email"] == norm:
                raise DuplicateLeadError(existing["id"])
        # <<< guard:duplicate
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SOURCE_SCORES.get(source, 0)
        if domain not in FREE_DOMAINS:
            score += 15
        owner = self._pick_rep()
        self.leads[lead_id] = {
            "id": lead_id,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        # >>> guard:queue
        if owner is None:
            self.waiting.append(lead_id)
        # <<< guard:queue
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._actor(actor)
        lead = self._get_lead(lead_id)
        self._allowed(lead["owner"], actor)
        # >>> guard:status-new
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        # <<< guard:status-new
        # >>> guard:score
        if lead["score"] < 30:
            raise ValueError("lead score is below the qualification threshold")
        # <<< guard:score
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._actor(actor)
        lead = self._get_lead(lead_id)
        # >>> guard:amount
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        # <<< guard:amount
        self._allowed(lead["owner"], actor)
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
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
        self._actor(actor)
        opp = self._get_opp(opp_id)
        # >>> guard:stage-name
        if not isinstance(stage, str) or stage not in ALL_STAGES:
            raise ValueError("unknown stage: %r" % (stage,))
        # <<< guard:stage-name
        self._allowed(opp["owner"], actor)
        # >>> guard:transition
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        nxt = STAGE_ORDER[STAGE_ORDER.index(opp["stage"]) + 1]
        if stage != "lost" and stage != nxt:
            raise ValueError("illegal stage transition")
        # <<< guard:transition
        # >>> guard:bigdeal
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager approval required for deals above 50000")
        # <<< guard:bigdeal
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slots(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._actor(actor)
        opp = self._get_opp(opp_id)
        # >>> guard:pct-range
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int between 1 and 30")
        # <<< guard:pct-range
        self._allowed(opp["owner"], actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        # >>> guard:rep-cap
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")
        # <<< guard:rep-cap
        new_amount = opp["amount"] * (100 - pct) // 100
        # >>> guard:floor
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")
        # <<< guard:floor
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._actor(actor)
        opp = self._get_opp(opp_id)
        # >>> guard:transfer-manager
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer opportunities")
        # <<< guard:transfer-manager
        # >>> guard:transfer-target
        target = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a rep")
        # <<< guard:transfer-target
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        # >>> guard:transfer-same
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already belongs to that rep")
        # <<< guard:transfer-same
        # >>> guard:transfer-capacity
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
        # <<< guard:transfer-capacity
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slots(previous)

    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in FINAL_STAGES]
        weighted = 0
        for opp in open_opps:
            weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        won = sum(o["amount"] for o in self.opps.values() if o["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
