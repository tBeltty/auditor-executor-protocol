"""Tiny CRM module with lead routing, opportunities and forecasting."""

FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCES = {"web", "referral", "event"}
STAGES = ["prospect", "proposal", "negotiation", "won"]
FINAL = {"won", "lost"}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
        self.existing_id = existing_id


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

    # -- helpers ---------------------------------------------------------
    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL:
                total += 1
        return total

    def _assign_waiting(self, rep_id):
        while self.waiting and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self.waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _pick_owner(self):
        best = None
        best_load = None
        for user in self.users.values():
            if user["role"] != "rep":
                continue
            load = self._load(user["id"])
            if load >= user["capacity"]:
                continue
            if best is None or load < best_load or (load == best_load and user["id"] < best):
                best = user["id"]
                best_load = load
        return best

    # -- commands --------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized = _valid_email(email)
        if normalized is None:
            raise ValueError("invalid email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in SOURCES:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        domain = normalized.split("@")[1]
        score = {"web": 10, "referral": 30, "event": 20}[source]
        if domain not in FREE_DOMAINS:
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
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "new":
            raise ValueError("lead not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("invalid amount")
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "qualified":
            raise ValueError("lead not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
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
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        if stage not in list(WEIGHTS) + ["won", "lost"]:
            raise ValueError("invalid stage")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in FINAL:
            raise ValueError("opportunity is final")
        current = opp["stage"]
        if stage != "lost" and stage != STAGES[STAGES.index(current) + 1]:
            raise ValueError("invalid transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for large negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("invalid pct")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in FINAL:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount too large for rep")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        if not self._is_manager(actor):
            raise PermissionError("manager only")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("invalid new owner")
        opp = self.opps[opp_id]
        if opp["stage"] in FINAL:
            raise ValueError("opportunity is final")
        previous = opp["owner"]
        if new_owner == previous:
            raise ValueError("same owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner at capacity")

        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in FINAL]
        weighted = 0
        for opp in open_opps:
            weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        won = sum(o["amount"] for o in self.opps.values() if o["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
