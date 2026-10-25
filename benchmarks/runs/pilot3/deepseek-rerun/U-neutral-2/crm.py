"""Small CRM with lead routing, qualification, opportunities and forecasting."""

FREEMAIL_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

# Ordered pipeline; "lost" may be entered from any non-final stage.
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
VALID_STAGES = frozenset(STAGE_ORDER) | {"lost"}
FINAL_STAGES = frozenset({"won", "lost"})

STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, message="duplicate lead", existing_id=None):
        super().__init__(message)
        self.existing_id = existing_id


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


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
        self._waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internal helpers (no mutation until every check has passed)
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown user: %r" % (actor,))

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

    def _best_owner(self):
        best_id = None
        best_key = None
        for user in self.users.values():
            if user["role"] != "rep":
                continue
            load = self._load(user["id"])
            if load >= user["capacity"]:
                continue
            key = (load, user["id"])
            if best_key is None or key < best_key:
                best_key = key
                best_id = user["id"]
        return best_id

    def _free_slot(self, user_id):
        while self._waiting and self._load(user_id) < self.users[user_id]["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a local part")
        if not any(
            char == "." and 0 < index < len(domain) - 1
            for index, char in enumerate(domain)
        ):
            raise ValueError("email domain must contain an inner '.'")
        return normalized

    # ------------------------------------------------------------------
    # operations
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized = self._normalize_email(email)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(
                    "lead with email %r already exists" % normalized,
                    existing_id=lead["id"],
                )

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        domain = normalized.split("@")[1]
        score = SOURCE_SCORES[source]
        if domain not in FREEMAIL_DOMAINS:
            score += 15

        owner = self._best_owner()
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
        lead = self._get_lead(lead_id)

        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is too low")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._get_lead(lead_id)

        if not _is_int(amount) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
        opp = {
            "id": opp_id,
            "lead_id": lead["id"],
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
        opp = self._get_opp(opp_id)

        if not isinstance(stage, str) or stage not in VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not advance this opportunity")
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost":
            index = STAGE_ORDER.index(current)
            if index + 1 >= len(STAGE_ORDER) or STAGE_ORDER[index + 1] != stage:
                raise ValueError("cannot move from %r to %r" % (current, stage))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("a manager is required for large negotiations")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)

        if not _is_int(pct) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount above 10 requires a manager")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)

        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        target = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner already owns this opportunity")
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new_owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
