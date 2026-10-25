"""CRM module: leads, opportunities, permissions and forecasting."""

from collections import deque


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__(
            "a lead with this email already exists (id={})".format(existing_id)
        )
        self.existing_id = existing_id


class CRM:
    _SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
    _FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
    _STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
    _FINAL_STAGES = {"won", "lost"}
    _WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

    def __init__(self, reps):
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = deque()  # FIFO queue of lead ids with no owner
        self._emails = {}  # normalized email -> lead id
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _require_known_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor: {}".format(actor))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _is_owner_or_manager(self, owner, actor):
        return actor == owner or self._is_manager(actor)

    def _load(self, rep_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in self._FINAL_STAGES:
                total += 1
        return total

    def _pick_owner(self):
        candidates = []
        for user_id, user in self._users.items():
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load < user["capacity"]:
                candidates.append((load, user_id))
        if not candidates:
            return None
        return min(candidates)[1]

    def _normalize_email(self, email):
        """Validate a raw email and return its normalized form."""
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty part before '@'")
        if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
            raise ValueError("invalid email domain")
        return normalized

    def _free_slot(self, rep_id):
        """Assign waiting leads to rep_id while its load is below capacity."""
        while self._waiting:
            load = self._load(rep_id)
            if load >= self._users[rep_id]["capacity"]:
                break
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_known_actor(actor)
        # 1. email validation
        normalized = self._normalize_email(email)
        # 2. name validation
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        # 3. source validation
        if source not in self._SOURCE_SCORES:
            raise ValueError("invalid source")
        # 4. duplicate check
        existing_id = self._emails.get(normalized)
        if existing_id is not None:
            raise DuplicateLeadError(existing_id)
        # 5. id and score
        self._lead_count += 1
        lead_id = "L{}".format(self._lead_count)
        score = self._SOURCE_SCORES[source]
        _, domain = normalized.rsplit("@", 1)
        if domain not in self._FREE_DOMAINS:
            score += 15
        # 6. owner selection
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
        self._emails[normalized] = lead_id
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_known_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: {}".format(lead_id))
        lead = self.leads[lead_id]
        if not self._is_owner_or_manager(lead["owner"], actor):
            raise PermissionError("actor is not the owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_known_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: {}".format(lead_id))
        if (
            not isinstance(amount, int)
            or isinstance(amount, bool)
            or amount <= 0
        ):
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if not self._is_owner_or_manager(lead["owner"], actor):
            raise PermissionError("actor is not the owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_count += 1
        opp_id = "O{}".format(self._opp_count)
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
        self._require_known_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: {}".format(opp_id))
        if stage not in ("prospect", "proposal", "negotiation", "won", "lost"):
            raise ValueError("invalid stage: {}".format(stage))
        opp = self.opps[opp_id]
        if not self._is_owner_or_manager(opp["owner"], actor):
            raise PermissionError("actor is not the owner or a manager")
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        next_stage = self._STAGE_ORDER[self._STAGE_ORDER.index(opp["stage"]) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("stage must be lost or the immediate next stage")
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError("only a manager may advance to negotiation")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self._FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_known_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: {}".format(opp_id))
        if (
            not isinstance(pct, int)
            or isinstance(pct, bool)
            or not 1 <= pct <= 30
        ):
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if not self._is_owner_or_manager(opp["owner"], actor):
            raise PermissionError("actor is not the owner or a manager")
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("only a manager may discount more than 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount above 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_known_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: {}".format(opp_id))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if new_owner not in self._users or self._users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if self._load(new_owner) >= self._users[new_owner]["capacity"]:
            raise ValueError("new_owner has no free capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_amount = 0
        for opp in self.opps.values():
            if opp["stage"] in self._FINAL_STAGES:
                if opp["stage"] == "won":
                    won_amount += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * self._WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_amount}
