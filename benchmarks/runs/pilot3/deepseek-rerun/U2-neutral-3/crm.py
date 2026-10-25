"""In-memory CRM for leads, opportunities and forecasts.

The module implements the behaviour described in the project spec:

* leads are created from a normalized email, scored by source and domain,
  and handed to the least loaded rep that still has capacity;
* leads that find no free rep wait in a FIFO queue and are assigned as soon
  as a rep frees a slot (by closing an opportunity or by a transfer);
* opportunities move through ``prospect -> proposal -> negotiation -> won``
  (or to ``lost`` from any open stage) and support discounts and transfers;
* every successful mutation appends one or more entries to ``log``.

Any failed call raises before mutating state and therefore leaves both the
objects and the log untouched.
"""

FREE_EMAIL_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})

SOURCES = ("web", "referral", "event")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
CORPORATE_DOMAIN_BONUS = 15

STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
NEXT_STAGE = {
    "prospect": "proposal",
    "proposal": "negotiation",
    "negotiation": "won",
}
FINAL_STAGES = frozenset({"won", "lost"})
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

MIN_QUALIFY_SCORE = 30
MAX_DISCOUNT_PCT = 30
MAX_REP_DISCOUNT_PCT = 10
MANAGER_APPROVAL_AMOUNT = 50000
MAX_CUMULATIVE_DISCOUNT_PCT = 30


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id=None):
        super().__init__("duplicate lead")
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
        self._lead_counter = 0
        self._opp_counter = 0
        self._waiting = []

    # ------------------------------------------------------------------ utils
    @staticmethod
    def _lookup(mapping, key):
        """``mapping.get(key)`` that tolerates unhashable keys."""
        try:
            return mapping.get(key)
        except TypeError:
            return None

    def _require_actor(self, actor):
        try:
            known = actor in self.users
        except TypeError:
            known = False
        if not known:
            raise PermissionError("unknown actor")

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _reps(self):
        return [u for u in self.users.values() if u["role"] == "rep"]

    def _lead(self, lead_id):
        lead = self._lookup(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        return lead

    def _opp(self, opp_id):
        opp = self._lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        return opp

    def load(self, user_id):
        """Number of open leads plus open opportunities owned by ``user_id``."""
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                total += 1
        return total

    def _pick_owner(self):
        """Least loaded rep with spare capacity; ties break on smallest id."""
        best = None
        best_load = None
        for rep in self._reps():
            load = self.load(rep["id"])
            if load >= rep["capacity"]:
                continue
            if best is None or load < best_load or (load == best_load and rep["id"] < best):
                best = rep["id"]
                best_load = load
        return best

    def _assign_waiting(self, rep_id):
        """Fill ``rep_id``'s freed slots from the FIFO queue."""
        if rep_id not in self.users:
            return
        capacity = self.users[rep_id]["capacity"]
        while self._waiting and self.load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        """Return ``(normalized_email, domain)`` or raise ValueError."""
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email")
        local, _, domain = normalized.partition("@")
        if not local or not domain:
            raise ValueError("invalid email")
        dot = domain.find(".")
        if dot <= 0 or domain.endswith("."):
            raise ValueError("invalid email")
        return normalized, domain

    @staticmethod
    def _validate_stage(stage):
        if not isinstance(stage, str) or stage not in STAGES:
            raise ValueError("invalid stage")

    # --------------------------------------------------------------- methods
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        normalized, domain = self._normalize_email(email)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")

        if source not in SOURCES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += CORPORATE_DOMAIN_BONUS

        owner = self._pick_owner()

        self._lead_counter += 1
        lead_id = "L%d" % self._lead_counter
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

        lead = self._lead(lead_id)
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < MIN_QUALIFY_SCORE:
            raise ValueError("score too low")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = self._lead(lead_id)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("invalid amount")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_counter += 1
        opp_id = "O%d" % self._opp_counter
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

        opp = self._opp(opp_id)
        self._validate_stage(stage)
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost" and NEXT_STAGE.get(opp["stage"]) != stage:
            raise ValueError("invalid stage transition")
        if (
            stage == "negotiation"
            and opp["amount"] > MANAGER_APPROVAL_AMOUNT
            and not self._is_manager(actor)
        ):
            raise PermissionError("manager required")

        owner = opp["owner"]
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(owner)

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self._opp(opp_id)
        if isinstance(pct, bool) or not isinstance(pct, int):
            raise ValueError("invalid percentage")
        if pct < 1 or pct > MAX_DISCOUNT_PCT:
            raise ValueError("invalid percentage")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > MAX_REP_DISCOUNT_PCT:
            raise PermissionError("discount too large")

        new_amount = opp["amount"] * (100 - pct) // 100
        floor = opp["original_amount"] * (100 - MAX_CUMULATIVE_DISCOUNT_PCT)
        if new_amount * 100 < floor:
            raise ValueError("cumulative discount too large")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = self._opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        target = self._lookup(self.users, new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("invalid new owner")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("same owner")
        if self.load(new_owner) >= target["capacity"]:
            raise ValueError("no capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
