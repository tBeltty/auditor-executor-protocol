"""CRM module implemented per specs/crm.md."""

from collections import deque


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % existing_id)


_FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_SCORES = {"web": 10, "referral": 30, "event": 20}
_SOURCES = set(_SCORES)
_STAGES = ("prospect", "proposal", "negotiation", "won")
_FINAL_STAGES = ("won", "lost")


class CRM:
    def __init__(self, reps):
        self.users = {rep["id"]: rep for rep in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = deque()
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------ helpers
    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        candidates = [
            rep for rep in self.users.values()
            if rep["role"] == "rep" and self._load(rep["id"]) < rep["capacity"]
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda rep: (self._load(rep["id"]), rep["id"]))["id"]

    def _free_slot(self, rep_id):
        while self._waiting and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must not be empty")
        has_inner_dot = any(
            domain[i] == "." for i in range(len(domain)) if i != 0 and i != len(domain) - 1
        )
        if not has_inner_dot:
            raise ValueError("email domain must contain a '.' inside it")
        return normalized

    # ------------------------------------------------------------------ commands
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in _SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        domain = normalized.split("@")[1]
        score = _SCORES[source]
        if domain not in _FREE_DOMAINS:
            score += 15

        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
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
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_count += 1
        opp_id = "O%d" % self._opp_count
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
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _STAGES + _FINAL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is final")
        current = opp["stage"]
        next_stage = _STAGES[_STAGES.index(current) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for negotiation over 50000")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount over 10 requires a manager")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new owner must be a rep")
        opp = self.opps[opp_id]
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is the current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        weighted = 0
        open_count = 0
        won_total = 0
        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}
        for opp in self.opps.values():
            if opp["stage"] == "won":
                won_total += opp["amount"]
            elif opp["stage"] != "lost":
                open_count += 1
                weighted += opp["amount"] * weights[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
