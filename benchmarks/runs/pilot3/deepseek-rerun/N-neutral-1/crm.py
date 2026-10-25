"""Tiny CRM domain model.

Implements the behavior described in specs/crm.md: lead capture with a
round-robin-ish load balancer, qualification, conversion to opportunities,
pipeline advancement, discounts, manager-only transfers and a forecast.
"""

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

ROLE_REP = "rep"
ROLE_MANAGER = "manager"

STAGE_PROSPECT = "prospect"
STAGE_PROPOSAL = "proposal"
STAGE_NEGOTIATION = "negotiation"
STAGE_WON = "won"
STAGE_LOST = "lost"

STAGE_ORDER = [STAGE_PROSPECT, STAGE_PROPOSAL, STAGE_NEGOTIATION, STAGE_WON]
STAGES = set(STAGE_ORDER) | {STAGE_LOST}
FINAL_STAGES = {STAGE_WON, STAGE_LOST}

FORECAST_WEIGHTS = {
    STAGE_PROSPECT: 10,
    STAGE_PROPOSAL: 30,
    STAGE_NEGOTIATION: 60,
}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__(
            "a lead with this email already exists: %s" % (existing_id,)
        )


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep.get("capacity", 0),
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_seq = 0
        self._opp_seq = 0
        self._waiting = []

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == ROLE_MANAGER

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _best_owner(self):
        candidates = []
        for user in self.users.values():
            if user["role"] != ROLE_REP:
                continue
            load = self._load(user["id"])
            if load < user["capacity"]:
                candidates.append((load, user["id"]))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][1]

    def _fill_slot(self, rep_id):
        """Hand waiting leads to ``rep_id`` while it has spare capacity."""
        if rep_id is None or rep_id not in self.users:
            return
        capacity = self.users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        parts = normalized.split("@")
        if len(parts) != 2:
            raise ValueError("email must contain exactly one '@'")
        local, domain = parts
        if not local:
            raise ValueError("email must have a non-empty local part")
        length = len(domain)
        valid_dot = any(
            char == "." and index != 0 and index != length - 1
            for index, char in enumerate(domain)
        )
        if not valid_dot:
            raise ValueError("email domain must contain an inner '.'")
        return normalized, domain

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        normalized, domain = self._normalize_email(email)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        clean_name = name.strip()

        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._best_owner()

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        lead = {
            "id": lead_id,
            "email": normalized,
            "name": clean_name,
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
        lead = self._get_lead(lead_id)
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may qualify")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self._get_lead(lead_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may convert")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
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
            "stage": STAGE_PROSPECT,
        }
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if not isinstance(stage, str) or stage not in STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may advance")
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != STAGE_LOST:
            index = STAGE_ORDER.index(current)
            if index + 1 >= len(STAGE_ORDER) or STAGE_ORDER[index + 1] != stage:
                raise ValueError("cannot jump from %s to %s" % (current, stage))
        if (
            stage == STAGE_NEGOTIATION
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError("large deals need a manager to reach negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._fill_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int between 1 and 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may discount")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("cannot discount a final opportunity")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if (
            not isinstance(new_owner, str)
            or new_owner not in self.users
            or self.users[new_owner]["role"] != ROLE_REP
        ):
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("cannot transfer a final opportunity")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is already the owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner has no capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill_slot(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in FINAL_STAGES:
                if stage == STAGE_WON:
                    won_total += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * FORECAST_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
