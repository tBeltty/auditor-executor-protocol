"""CRM lead/opportunity management module."""

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}

SOURCES = ("web", "referral", "event")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

STAGES = ("prospect", "proposal", "negotiation", "won")
STAGE_AFTER = {
    "prospect": "proposal",
    "proposal": "negotiation",
    "negotiation": "won",
}
FINAL_STAGES = ("won", "lost")
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id=None):
        super().__init__("duplicate lead")
        self.existing_id = existing_id


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
        self._lead_counter = 0
        self._opp_counter = 0
        self._waiting = []

    # ------------------------------------------------------------------ utils
    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor")

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _reps(self):
        return [u for u in self.users.values() if u["role"] == "rep"]

    def load(self, user_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                total += 1
        return total

    def _pick_owner(self):
        best = None
        best_load = None
        for rep in self._reps():
            load = self.load(rep["id"])
            if load >= rep["capacity"]:
                continue
            if best is None or load < best_load or (load == best_load and rep["id"] < best):
                best = rep["id"]
                best_load = load
        return best

    def _assign_waiting(self, rep_id):
        capacity = self.users[rep_id]["capacity"]
        while self._waiting and self.load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _check_stage(self, stage):
        if not isinstance(stage, str) or stage not in ("prospect", "proposal", "negotiation", "won", "lost"):
            raise ValueError("invalid stage")

    # --------------------------------------------------------------- methods
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email")
        local, _, domain = normalized.partition("@")
        if not local:
            raise ValueError("invalid email")
        if "." not in domain:
            raise ValueError("invalid email")
        if domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email")
        if domain.index(".") in (0, len(domain) - 1):
            raise ValueError("invalid email")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")

        if source not in SOURCES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._pick_owner()

        self._lead_counter += 1
        lead_id = "L%d" % self._lead_counter
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
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("invalid amount")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_counter += 1
        opp_id = "O%d" % self._opp_counter
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
            raise ValueError("unknown opportunity")
        self._check_stage(stage)
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost" and STAGE_AFTER.get(opp["stage"]) != stage:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required")

        previous_owner = opp["owner"]
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(previous_owner)

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if isinstance(pct, bool) or not isinstance(pct, int) or pct < 1 or pct > 30:
            raise ValueError("invalid percentage")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount too large")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount too large")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("invalid new owner")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("same owner")
        if self.load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("no capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

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
            weighted += opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
