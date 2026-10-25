"""A small in-memory CRM with leads, opportunities and deterministic assignment."""

from collections import deque

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
NEXT_STAGE = {
    "prospect": "proposal",
    "proposal": "negotiation",
    "negotiation": "won",
}
FINAL_STAGES = {"won", "lost"}
FORECAST_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead already exists for the normalized email."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("lead already exists: %s" % (existing_id,))


class CRM:
    def __init__(self, reps):
        self.leads = {}
        self.opps = {}
        self.log = []
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self._waiting = deque()
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _is_rep(self, user_id):
        user = self._users.get(user_id)
        return user is not None and user["role"] == "rep"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _can_assign(self, rep_id):
        return self._load(rep_id) < self._users[rep_id]["capacity"]

    def _assign_waiting(self, rep_id):
        """Fill a freed slot from the FIFO queue while capacity remains."""
        while self._waiting and self._can_assign(rep_id):
            lead_id = self._waiting.popleft()
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not domain:
            raise ValueError("email must have a domain")
        if not any(
            ch == "." and 0 < i < len(domain) - 1 for i, ch in enumerate(domain)
        ):
            raise ValueError("email domain must contain a middle '.'")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        owner = None
        candidates = [
            user["id"]
            for user in self._users.values()
            if user["role"] == "rep" and self._can_assign(user["id"])
        ]
        if candidates:
            owner = min(candidates, key=lambda rid: (self._load(rid), rid))

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
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
        self._check_actor(actor)

        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is too low")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)

        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if (
            not isinstance(amount, int)
            or isinstance(amount, bool)
            or amount <= 0
        ):
            raise ValueError("amount must be a positive integer")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
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

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in ("prospect", "proposal", "negotiation", "won", "lost"):
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost" and stage != NEXT_STAGE[opp["stage"]]:
            raise ValueError("invalid stage transition")
        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError("a manager is required for large negotiations")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if (
            not isinstance(pct, int)
            or isinstance(pct, bool)
            or pct < 1
            or pct > 30
        ):
            raise ValueError("pct must be an integer from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10 percent")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer opportunities")
        if not self._is_rep(new_owner):
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already belongs to that rep")
        if not self._can_assign(new_owner):
            raise ValueError("new owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_opps = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] == "won":
                won += opp["amount"]
            elif opp["stage"] != "lost":
                open_opps += 1
                weighted += opp["amount"] * FORECAST_WEIGHTS[opp["stage"]] // 100
        return {"open": open_opps, "weighted": weighted, "won": won}
