"""Minimal CRM module implementing the behaviour described in the spec."""

FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCES = ("web", "referral", "event")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self._reps = {}
        for rep in reps:
            self._reps[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self.queue = []
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------ utils
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self._reps:
            raise PermissionError("unknown actor: %r" % (actor,))
        return self._reps[actor]

    def _is_manager(self, actor):
        return self._reps[actor]["role"] == "manager"

    def _load(self, user_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                n += 1
        return n

    def _pick_rep(self):
        best_id = None
        best_load = None
        for rep_id in sorted(self._reps):
            rep = self._reps[rep_id]
            if rep["role"] != "rep":
                continue
            load = self._load(rep_id)
            if load >= rep["capacity"]:
                continue
            if best_load is None or load < best_load:
                best_id, best_load = rep_id, load
        return best_id

    def _free_slot(self, owner_id):
        if owner_id is None:
            return
        rep = self._reps.get(owner_id)
        if rep is None or rep["role"] != "rep":
            return
        while self.queue and self._load(owner_id) < rep["capacity"]:
            lead_id = self.queue.pop(0)
            lead = self.leads.get(lead_id)
            if lead is None:
                continue
            lead["owner"] = owner_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------- public API
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        parts = normalized.split("@")
        if len(parts) != 2 or not parts[0]:
            raise ValueError("invalid email")
        domain = parts[1]
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email domain")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        if source not in SOURCES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        if domain not in FREE_DOMAINS:
            score += 15

        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
        owner = self._pick_rep()
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
            self.queue.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_count += 1
        opp_id = "O%d" % self._opp_count
        opp = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        self.opps[opp_id] = opp
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if stage not in STAGES:
            raise ValueError("invalid stage")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        valid = stage == "lost"
        if not valid:
            idx = STAGE_ORDER.index(opp["stage"])
            valid = idx + 1 < len(STAGE_ORDER) and STAGE_ORDER[idx + 1] == stage
        if not valid:
            raise ValueError("invalid transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if not isinstance(pct, int) or isinstance(pct, bool) or pct < 1 or pct > 30:
            raise ValueError("invalid pct")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("pct too high")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount too deep")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        if not isinstance(new_owner, str) or new_owner not in self._reps:
            raise ValueError("unknown user")
        if self._reps[new_owner]["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("already owner")
        if self._load(new_owner) >= self._reps[new_owner]["capacity"]:
            raise ValueError("new owner at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
