"""CRM lead/opportunity pipeline.

Implements the behaviour described in specs/crm.md.
"""

FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCES = ("web", "referral", "event")
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id=None):
        self.existing_id = existing_id
        super().__init__("lead already exists: %s" % (existing_id,))


def _normalize_email(email):
    if not isinstance(email, str):
        raise ValueError("email must be a string")
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        raise ValueError("email must contain exactly one '@'")
    local, domain = normalized.split("@")
    if not local:
        raise ValueError("email must have a non-empty local part")
    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("email domain is invalid")
    return normalized


class CRM:
    def __init__(self, reps):
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------ helpers
    def _require_known(self, actor):
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        leads = sum(
            1
            for lead in self.leads.values()
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified")
        )
        opps = sum(
            1
            for opp in self.opps.values()
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES
        )
        return leads + opps

    def _capacity(self, rep_id):
        return self._users[rep_id]["capacity"]

    def _lowest_load_rep(self):
        candidates = [
            user
            for user in self._users.values()
            if user["role"] == "rep" and self._load(user["id"]) < user["capacity"]
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda u: (self._load(u["id"]), u["id"]))["id"]

    def _assign_waiting(self, rep_id):
        while self._waiting and self._load(rep_id) < self._capacity(rep_id):
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _require_owner_or_manager(self, owner, actor):
        if actor != owner and not self._is_manager(actor):
            raise PermissionError("not allowed for user: %s" % (actor,))

    # ------------------------------------------------------------------ methods
    def add_lead(self, email, name, source, actor):
        self._require_known(actor)
        normalized = _normalize_email(email)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in SOURCES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        domain = normalized.split("@")[1]
        base = {"web": 10, "referral": 30, "event": 20}[source]
        score = base + (0 if domain in FREE_DOMAINS else 15)

        self._lead_count += 1
        lead_id = "L%d" % self._lead_count

        owner = self._lowest_load_rep()
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
        self._require_known(actor)

        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]

        self._require_owner_or_manager(lead["owner"], actor)

        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low to qualify")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_known(actor)

        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]

        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive integer")

        self._require_owner_or_manager(lead["owner"], actor)

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
        self._require_known(actor)

        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]

        if stage not in STAGE_ORDER and stage not in FINAL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))

        self._require_owner_or_manager(opp["owner"], actor)

        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if stage != "lost":
            index = STAGE_ORDER.index(current)
            if index + 1 >= len(STAGE_ORDER) or STAGE_ORDER[index + 1] != stage:
                raise ValueError("invalid stage transition")

        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))

        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_known(actor)

        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]

        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an integer between 1 and 30")

        self._require_owner_or_manager(opp["owner"], actor)

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("discount above 10 requires a manager")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_known(actor)

        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]

        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")

        if new_owner not in self._users or self._users[new_owner]["role"] != "rep":
            raise ValueError("unknown rep: %r" % (new_owner,))

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already owned by that rep")
        if self._load(new_owner) >= self._capacity(new_owner):
            raise ValueError("new owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in FINAL_STAGES]
        weighted = sum(o["amount"] * WEIGHTS[o["stage"]] // 100 for o in open_opps)
        won = sum(o["amount"] for o in self.opps.values() if o["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
