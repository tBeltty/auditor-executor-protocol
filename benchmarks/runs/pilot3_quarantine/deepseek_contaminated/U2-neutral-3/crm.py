"""A small, in-memory CRM with leads, opportunities, and pipeline rules.

The lead lifecycle is::

    add_lead -> qualify -> convert -> advance/discount -> transfer

Every public method takes the acting user id as its last argument and
validates it before anything else.  Calls are atomic: when a call raises,
the CRM is left exactly as it was (including the audit log).
"""

FREE_EMAIL_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")

VALID_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")

FINAL_STAGES = frozenset({"won", "lost"})

STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

OPEN_LEAD_STATUSES = frozenset({"new", "qualified"})

MIN_QUALIFY_SCORE = 30

MAX_REP_DISCOUNT = 10


class DuplicateLeadError(Exception):
    """Raised when a lead already exists for the normalized email."""

    def __init__(self, *args, existing_id=None):
        super().__init__(*args)
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
        self._waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _check_actor(self, actor):
        """PermissionError unless *actor* is the id of a known user."""
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _is_rep(self, actor):
        user = self.users.get(actor) if isinstance(actor, str) else None
        return user is not None and user["role"] == "rep"

    def _load(self, user_id):
        """Units of work owned by *user_id*, as defined by the spec."""
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in OPEN_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _choose_owner(self):
        """Rep with the lowest load below capacity, smallest id on ties."""
        best_id = None
        best_key = None
        for user_id, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load >= user["capacity"]:
                continue
            key = (load, user_id)
            if best_key is None or key < best_key:
                best_id = user_id
                best_key = key
        return best_id

    def _assign_waiting(self, user_id):
        """Give queued leads to *user_id* while it has spare capacity (FIFO)."""
        if not self._is_rep(user_id):
            return
        capacity = self.users[user_id]["capacity"]
        while self._waiting and self._load(user_id) < capacity:
            lead_id = self._waiting.pop(0)
            lead = self.leads[lead_id]
            if lead["owner"] is not None:
                continue
            lead["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    def _lead_or_raise(self, lead_id):
        lead = self.leads.get(lead_id) if isinstance(lead_id, str) else None
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return lead

    def _opp_or_raise(self, opp_id):
        opp = self.opps.get(opp_id) if isinstance(opp_id, str) else None
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return opp

    @staticmethod
    def _normalize_email(email):
        """Validate *email* and return ``(normalized, domain)``."""
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
            raise ValueError("email domain must contain a valid '.'")
        return normalized, domain

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        normalized, domain = self._normalize_email(email)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("source must be 'web', 'referral' or 'event'")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(
                    "lead already exists for %s" % normalized,
                    existing_id=lead["id"],
                )

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._choose_owner()

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
        lead = self._lead_or_raise(lead_id)
        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("not allowed to qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < MIN_QUALIFY_SCORE:
            raise ValueError("lead score is below %d" % MIN_QUALIFY_SCORE)

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self._lead_or_raise(lead_id)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("not allowed to convert this lead")
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
            "stage": "prospect",
        }
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        opp = self._opp_or_raise(opp_id)
        if stage not in VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if not (actor == opp["owner"] or self._is_manager(actor)):
            raise PermissionError("not allowed to advance this opportunity")
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        next_stage = STAGE_ORDER[STAGE_ORDER.index(current) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("invalid stage transition")
        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError("manager required for large negotiations")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self._opp_or_raise(opp_id)
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if not (actor == opp["owner"] or self._is_manager(actor)):
            raise PermissionError("not allowed to discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if pct > MAX_REP_DISCOUNT and not self._is_manager(actor):
            raise PermissionError("manager required for discounts above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self._opp_or_raise(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if not self._is_rep(new_owner):
            raise ValueError("new owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is already the owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
