"""Minimal CRM lead/opportunity pipeline."""

FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCES = {"web", "referral", "event"}
BASE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGES = ("prospect", "proposal", "negotiation", "won")
ALL_STAGES = STAGES + ("lost",)
FINAL_STAGES = {"won", "lost"}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % existing_id)


def _valid_email(email):
    if not isinstance(email, str):
        return None
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        return None
    local, domain = normalized.split("@")
    if not local or not domain:
        return None
    dot = domain.find(".")
    if dot <= 0 or dot == len(domain) - 1:
        return None
    return normalized


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # -- internals ---------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))
        return self.users[actor]

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, user_id):
        if user_id is None:
            return 0
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        best = None
        best_key = None
        for user in self.users.values():
            if user["role"] != "rep":
                continue
            load = self._load(user["id"])
            if load >= user["capacity"]:
                continue
            key = (load, user["id"])
            if best_key is None or key < best_key:
                best = user["id"]
                best_key = key
        return best

    def _drain(self, user_id):
        if user_id is None or user_id not in self.users:
            return
        capacity = self.users[user_id]["capacity"]
        while self.waiting and self._load(user_id) < capacity:
            lead_id = self.waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    def _require_opp(self, opp_id):
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    # -- API ---------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        normalized = _valid_email(email)
        if normalized is None:
            raise ValueError("invalid email")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")

        if not isinstance(source, str) or source not in SOURCES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        domain = normalized.split("@")[1]
        score = BASE_SCORES[source]
        if domain not in FREE_DOMAINS:
            score += 15

        owner = self._pick_owner()
        lead_id = "L%d" % (self._lead_seq + 1)

        self._lead_seq += 1
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
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
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
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("invalid amount")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        opp_id = "O%d" % (self._opp_seq + 1)
        self._opp_seq += 1
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
        opp = self._require_opp(opp_id)
        if not isinstance(stage, str) or stage not in ALL_STAGES:
            raise ValueError("invalid stage")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost":
            try:
                expected = STAGES[STAGES.index(opp["stage"]) + 1]
            except (ValueError, IndexError):
                raise ValueError("invalid transition")
            if stage != expected:
                raise ValueError("invalid transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._drain(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("invalid pct")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount too large for rep")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30%")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        user = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if user is None or user["role"] != "rep":
            raise ValueError("invalid new owner")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new owner at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._drain(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in FINAL_STAGES:
                if stage == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
