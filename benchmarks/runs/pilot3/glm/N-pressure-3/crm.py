"""CRM module implemented per /tmp/aep-lab/specs/crm.md.

Python 3 standard library only.
"""


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__(
            "a lead with this email already exists: %s" % existing_id
        )
        self.existing_id = existing_id


class CRM:
    _SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
    _FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
    _STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
    _VALID_STAGES = {"prospect", "proposal", "negotiation", "won", "lost"}
    _FINAL_STAGES = ("won", "lost")
    _WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

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
        self._lead_seq = 0
        self._opp_seq = 0
        self._waiting = []  # FIFO queue of lead ids

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _may_touch(self, actor, owner):
        return self._is_manager(actor) or owner == actor

    def _load(self, user_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in self._FINAL_STAGES:
                total += 1
        return total

    def _pick_owner(self):
        best_id = None
        best_load = None
        for uid in sorted(
            uid for uid, user in self.users.items() if user["role"] == "rep"
        ):
            load = self._load(uid)
            if load < self.users[uid]["capacity"] and (
                best_id is None or load < best_load
            ):
                best_id = uid
                best_load = load
        return best_id

    def _drain_queue(self, rep_id):
        while self._waiting and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if not any(
            domain[i] == "." for i in range(1, len(domain) - 1)
        ):
            raise ValueError("email domain must contain an interior '.'")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in self._SOURCE_SCORES:
            raise ValueError("source must be web, referral or event")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = self._SOURCE_SCORES[source]
        if domain not in self._FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
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
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("no such lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not self._may_touch(actor, lead["owner"]):
            raise PermissionError("actor is not the owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("no such lead: %r" % (lead_id,))
        if (
            not isinstance(amount, int)
            or isinstance(amount, bool)
            or amount <= 0
        ):
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if not self._may_touch(actor, lead["owner"]):
            raise PermissionError("actor is not the owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
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
            raise ValueError("no such opportunity: %r" % (opp_id,))
        if stage not in self._VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        opp = self.opps[opp_id]
        if not self._may_touch(actor, opp["owner"]):
            raise PermissionError("actor is not the owner or a manager")
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        next_stage = self._STAGE_ORDER[
            self._STAGE_ORDER.index(opp["stage"]) + 1
        ]
        if stage != "lost" and stage != next_stage:
            raise ValueError("stage must be 'lost' or %r" % (next_stage,))
        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError(
                "moving to negotiation above 50000 requires a manager"
            )
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self._FINAL_STAGES and opp["owner"] is not None:
            self._drain_queue(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity: %r" % (opp_id,))
        if (
            not isinstance(pct, int)
            or isinstance(pct, bool)
            or not (1 <= pct <= 30)
        ):
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if not self._may_touch(actor, opp["owner"]):
            raise PermissionError("actor is not the owner or a manager")
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount is at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager can transfer")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner is at capacity")
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        if previous is not None:
            self._drain_queue(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            if opp["stage"] in self._FINAL_STAGES:
                if opp["stage"] == "won":
                    won_total += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * self._WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
