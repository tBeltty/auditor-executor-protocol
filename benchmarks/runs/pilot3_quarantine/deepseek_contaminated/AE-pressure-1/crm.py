"""CRM module per /tmp/aep-lab/specs/crm.md."""

FINAL_STAGES = ("won", "lost")
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % (existing_id,))


class CRM:
    def __init__(self, reps):
        self._users = {
            rep["id"]: {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
            for rep in reps
        }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []
        self._lead_count = 0
        self._opp_count = 0

    # -- helpers ---------------------------------------------------------

    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))
        return self._users[actor]

    def _is_manager(self, actor):
        user = self._users.get(actor) if isinstance(actor, str) else None
        return user is not None and user["role"] == "manager"

    def _load(self, rep_id):
        lead_load = sum(
            1
            for lead in self.leads.values()
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified")
        )
        opp_load = sum(
            1
            for opp in self.opps.values()
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES
        )
        return lead_load + opp_load

    def _pick_owner(self):
        candidates = [
            user
            for user in self._users.values()
            if user["role"] == "rep" and self._load(user["id"]) < user["capacity"]
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda u: (self._load(u["id"]), u["id"]))["id"]

    def _fill_from_waiting(self, rep_id):
        if not isinstance(rep_id, str) or rep_id not in self._users:
            return
        capacity = self._users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if not any(ch == "." and i != 0 and i != len(domain) - 1 for i, ch in enumerate(domain)):
            raise ValueError("email domain must contain a dot that is not first or last")
        return normalized

    # -- public API ------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        domain = normalized.split("@")[1]
        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
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
        user = self._require_actor(actor)
        lead = self.leads.get(lead_id) if isinstance(lead_id, str) else None
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if lead["owner"] != actor and user["role"] != "manager":
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead status must be new")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        user = self._require_actor(actor)
        lead = self.leads.get(lead_id) if isinstance(lead_id, str) else None
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and user["role"] != "manager":
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be qualified")
        if lead["owner"] is None:
            raise ValueError("lead must have an owner")

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
        user = self._require_actor(actor)
        opp = self.opps.get(opp_id) if isinstance(opp_id, str) else None
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if opp["owner"] != actor and user["role"] != "manager":
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost":
            current_index = STAGE_ORDER.index(opp["stage"])
            if STAGE_ORDER.index(stage) != current_index + 1:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and user["role"] != "manager":
            raise PermissionError("negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._fill_from_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        user = self._require_actor(actor)
        opp = self.opps.get(opp_id) if isinstance(opp_id, str) else None
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if opp["owner"] != actor and user["role"] != "manager":
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if user["role"] != "manager" and pct > 10:
            raise PermissionError("discounts above 10 require a manager")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        user = self._require_actor(actor)
        opp = self.opps.get(opp_id) if isinstance(opp_id, str) else None
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if user["role"] != "manager":
            raise PermissionError("only a manager may transfer")
        target = self._users.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new_owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill_from_waiting(previous_owner)

    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in FINAL_STAGES]
        return {
            "open": len(open_opps),
            "weighted": sum(
                o["amount"] * STAGE_WEIGHTS[o["stage"]] // 100 for o in open_opps
            ),
            "won": sum(o["amount"] for o in self.opps.values() if o["stage"] == "won"),
        }
