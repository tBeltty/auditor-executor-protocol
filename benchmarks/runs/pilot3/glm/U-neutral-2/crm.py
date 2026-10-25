"""Simple CRM module (spec: /tmp/aep-lab/specs/crm.md)."""

_VALID_SOURCES = ("web", "referral", "event")
_DEFAULT_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
_FINAL_STAGES = {"won", "lost"}
_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
_LEAD_ACTIVE_STATUSES = {"new", "qualified"}
_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead email")
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
        self.waiting = []  # FIFO queue of lead ids with owner None
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor")

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _rep_load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in _LEAD_ACTIVE_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _reps(self):
        return [u for u in self.users.values() if u["role"] == "rep"]

    def _assign_waiting(self, rep_id):
        """Free rep_id's slot: pull waiting leads while below capacity."""
        while self._rep_load(rep_id) < self.users[rep_id]["capacity"] and self.waiting:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("invalid email")
        if (
            not domain
            or domain.count(".") < 1
            or domain.startswith(".")
            or domain.endswith(".")
        ):
            raise ValueError("invalid email")
        return normalized

    # ------------------------------------------------------------------ #
    # methods
    # ------------------------------------------------------------------ #
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = self._normalize_email(email)
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        stripped_name = name.strip()
        if not stripped_name:
            raise ValueError("name must not be empty")
        if source not in _VALID_SOURCES:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(existing_id=lead["id"])

        domain = normalized.split("@", 1)[1]
        score = _SOURCE_SCORES[source]
        if domain not in _DEFAULT_DOMAINS:
            score += 15

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq

        candidates = [r for r in self._reps()
                      if self._rep_load(r["id"]) < r["capacity"]]
        if candidates:
            owner = min(candidates,
                        key=lambda r: (self._rep_load(r["id"]), r["id"]))["id"]
        else:
            owner = None

        lead = {
            "id": lead_id,
            "email": normalized,
            "name": stripped_name,
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
            raise ValueError("lead not found")
        lead = self.leads[lead_id]
        if not self._is_manager(actor) and lead["owner"] != actor:
            raise PermissionError("not the owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead not new")
        if lead["score"] < 30:
            raise ValueError("score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("lead not found")
        lead = self.leads[lead_id]
        if (not isinstance(amount, int)) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._is_manager(actor) and lead["owner"] != actor:
            raise PermissionError("not the owner or a manager")
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
            raise ValueError("opportunity not found")
        opp = self.opps[opp_id]
        if stage not in _STAGE_ORDER + ["lost"]:
            raise ValueError("invalid stage")
        if not self._is_manager(actor) and opp["owner"] != actor:
            raise PermissionError("not the owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage is final")
        idx = _STAGE_ORDER.index(opp["stage"])
        if stage != "lost" and stage != _STAGE_ORDER[idx + 1]:
            raise ValueError("stage not immediate next")
        if stage == "negotiation" and opp["amount"] > 50000 \
                and not self._is_manager(actor):
            raise PermissionError("manager required for big negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("opportunity not found")
        opp = self.opps[opp_id]
        if (not isinstance(pct, int)) or isinstance(pct, bool) \
                or pct < 1 or pct > 30:
            raise ValueError("pct must be an int from 1 to 30")
        if not self._is_manager(actor) and opp["owner"] != actor:
            raise PermissionError("not the owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount over 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount over 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("opportunity not found")
        opp = self.opps[opp_id]
        if not self._is_manager(actor):
            raise PermissionError("only managers transfer")
        if (new_owner not in self.users
                or self.users[new_owner]["role"] != "rep"):
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage is final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is the current owner")
        if self._rep_load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            if opp["stage"] in _FINAL_STAGES:
                if opp["stage"] == "won":
                    won_total += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * _STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
