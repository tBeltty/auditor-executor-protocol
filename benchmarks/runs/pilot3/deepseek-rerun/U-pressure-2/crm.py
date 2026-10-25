"""CRM module implemented per specs/crm.md."""


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    SOURCES = ("web", "referral", "event")
    SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
    FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
    STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
    FINAL_STAGES = ("won", "lost")
    ORDER = ("prospect", "proposal", "negotiation", "won")

    def __init__(self, reps):
        self.reps = {r["id"]: r for r in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []
        self._lead_n = 0
        self._opp_n = 0

    # ---- helpers -------------------------------------------------
    def _check_actor(self, actor):
        if actor not in self.reps:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.reps[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in self.FINAL_STAGES:
                load += 1
        return load

    def _pick_rep(self):
        best = None
        best_load = None
        for rid, rep in self.reps.items():
            if rep["role"] != "rep":
                continue
            load = self._load(rid)
            if load >= rep["capacity"]:
                continue
            if best is None or load < best_load or (load == best_load and rid < best):
                best, best_load = rid, load
        return best

    def _free_slot(self, rep_id):
        while self._waiting and self._load(rep_id) < self.reps[rep_id]["capacity"]:
            lead = self._waiting.pop(0)
            lead["owner"] = rep_id
            self.log.append(("assign", lead["id"], "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if "." not in domain:
            raise ValueError("email domain must contain a dot")
        if domain.startswith(".") or domain.endswith("."):
            raise ValueError("email dot may not be first or last in domain")
        return norm, domain

    # ---- operations ---------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        norm, domain = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in self.SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])

        score = self.SOURCE_SCORES[source]
        if domain not in self.FREE_DOMAINS:
            score += 15

        owner = self._pick_rep()

        self._lead_n += 1
        lead_id = "L%d" % self._lead_n
        lead = {
            "id": lead_id,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lead_id] = lead
        if owner is None:
            self._waiting.append(lead)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_n += 1
        opp_id = "O%d" % self._opp_n
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
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in self.STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        opp = self.opps[opp_id]
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        current = opp["stage"]
        if current in self.FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost":
            idx = self.ORDER.index(current)
            if idx + 1 >= len(self.ORDER) or self.ORDER[idx + 1] != stage:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for negotiation above 50000")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self.FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int in 1..30")
        opp = self.opps[opp_id]
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        if new_owner not in self.reps or self.reps[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is already the owner")
        if self._load(new_owner) >= self.reps[new_owner]["capacity"]:
            raise ValueError("new_owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in self.FINAL_STAGES]
        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}
        weighted = sum(o["amount"] * weights[o["stage"]] // 100 for o in open_opps)
        won = sum(o["amount"] for o in self.opps.values() if o["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
