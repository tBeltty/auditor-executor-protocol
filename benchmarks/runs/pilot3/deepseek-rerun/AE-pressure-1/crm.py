"""CRM lead / opportunity management, implemented to spec (specs/crm.md)."""

from collections import deque

STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
NEXT_STAGE = {
    "prospect": "proposal",
    "proposal": "negotiation",
    "negotiation": "won",
}
SOURCES = ("web", "referral", "event")
BASE_SCORE = {"web": 10, "referral": 30, "event": 20}
CONSUMER_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {rep["id"]: dict(rep) for rep in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = deque()
        self._lead_count = 0
        self._opp_count = 0

    # -- helpers ---------------------------------------------------------
    def _require_user(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        user = self.users.get(actor)
        return user is not None and user["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        candidates = [
            rep_id
            for rep_id, user in self.users.items()
            if user["role"] == "rep" and self._load(rep_id) < user["capacity"]
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda rid: (self._load(rid), rid))

    def _assign_waiting(self, rep_id):
        while self._waiting and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self._waiting.popleft()
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    # -- leads -----------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_user(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        local, sep, domain = normalized.partition("@")
        if (
            not sep
            or "@" in domain
            or not local
            or not domain
            or "." not in domain
            or domain.startswith(".")
            or domain.endswith(".")
        ):
            raise ValueError("invalid email: %r" % (email,))

        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name: %r" % (name,))

        if source not in SOURCES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = BASE_SCORE[source]
        if domain not in CONSUMER_DOMAINS:
            score += 15

        owner = self._pick_owner()
        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
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
        self._require_user(actor)
        lead = self._get_lead(lead_id)
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # -- opportunities ---------------------------------------------------
    def convert(self, lead_id, amount, actor):
        self._require_user(actor)
        lead = self._get_lead(lead_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
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
        self._require_user(actor)
        opp = self._get_opp(opp_id)
        if stage not in STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost" and stage != NEXT_STAGE.get(opp["stage"]):
            raise ValueError("invalid stage transition: %s -> %s" % (opp["stage"], stage))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("a manager is required for this negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_user(actor)
        opp = self._get_opp(opp_id)
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("a manager is required for a discount above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_user(actor)
        opp = self._get_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner must differ from the current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

    # -- reporting -------------------------------------------------------
    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in FINAL_STAGES]
        weighted = sum(o["amount"] * WEIGHTS[o["stage"]] // 100 for o in open_opps)
        won = sum(o["amount"] for o in self.opps.values() if o["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
