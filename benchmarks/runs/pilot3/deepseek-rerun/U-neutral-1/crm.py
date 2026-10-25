"""CRM module: leads, opportunities, assignment and forecasting.

Implements the contract described in the project specification.
"""

from collections import deque

FREEMAIL_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})
SOURCES = ("web", "referral", "event")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = frozenset({"won", "lost"})
ALL_STAGES = frozenset(STAGE_ORDER) | FINAL_STAGES
FORECAST_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
MANAGER_DISCOUNT_LIMIT = 10
NEGOTIATION_AMOUNT_LIMIT = 50000
MIN_ORIGINAL_FRACTION = 70  # cumulative discount ceiling of 30 percent


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id, message=None):
        self.existing_id = existing_id
        if message is None:
            message = "duplicate lead: %s" % (existing_id,)
        super().__init__(message)


def _is_int(value):
    """True for ints that are not bools."""
    return isinstance(value, int) and not isinstance(value, bool)


def _normalize_email(email):
    """Validate and normalize an email, raising ValueError when invalid."""
    if not isinstance(email, str):
        raise ValueError("email must be a string")
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        raise ValueError("email must contain exactly one '@'")
    local, _, domain = normalized.partition("@")
    if not local:
        raise ValueError("email must have a non-empty local part")
    if not domain:
        raise ValueError("email must have a domain")
    if "." not in domain:
        raise ValueError("email domain must contain a '.'")
    if domain[0] == "." or domain[-1] == ".":
        raise ValueError("email domain dot must not be first or last")
    return normalized


class CRM:
    """In-memory CRM with reps, leads, opportunities and an audit log."""

    def __init__(self, reps):
        self.reps = {}
        for rep in reps:
            self.reps[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = deque()
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.reps:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.reps[actor]["role"] == "manager"

    def _load(self, rep_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                total += 1
        return total

    def _pick_owner(self):
        best_id = None
        best_load = None
        for rep_id in sorted(self.reps):
            rep = self.reps[rep_id]
            if rep["role"] != "rep":
                continue
            load = self._load(rep_id)
            if load >= rep["capacity"]:
                continue
            if best_id is None or load < best_load:
                best_id = rep_id
                best_load = load
        return best_id

    def _assign_waiting(self, rep_id):
        while self.waiting:
            rep = self.reps[rep_id]
            if self._load(rep_id) >= rep["capacity"]:
                break
            lead_id = self.waiting.popleft()
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized = _normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SOURCE_SCORES[source]
        domain = normalized.partition("@")[2]
        if domain not in FREEMAIL_DOMAINS:
            score += 15
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
        if owner is None:
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("%s may not qualify %s" % (actor, lead_id))
        if lead["status"] != "new":
            raise ValueError("lead %s is not new" % (lead_id,))
        if lead["score"] < 30:
            raise ValueError("lead %s score is too low" % (lead_id,))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not _is_int(amount) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("%s may not convert %s" % (actor, lead_id))
        if lead["status"] != "qualified":
            raise ValueError("lead %s is not qualified" % (lead_id,))
        if lead["owner"] is None:
            raise ValueError("lead %s has no owner" % (lead_id,))

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
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("%s may not advance %s" % (actor, opp_id))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        current_index = STAGE_ORDER.index(opp["stage"])
        if stage != "lost":
            next_stage = STAGE_ORDER[current_index + 1]
            if stage != next_stage:
                raise ValueError("cannot move from %s to %s" % (opp["stage"], stage))
        if (
            stage == "negotiation"
            and opp["amount"] > NEGOTIATION_AMOUNT_LIMIT
            and not self._is_manager(actor)
        ):
            raise PermissionError("negotiation above threshold requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not _is_int(pct) or pct < 1 or pct > 30:
            raise ValueError("pct must be an int from 1 to 30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("%s may not discount %s" % (actor, opp_id))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if not self._is_manager(actor) and pct > MANAGER_DISCOUNT_LIMIT:
            raise PermissionError("only managers may discount above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * MIN_ORIGINAL_FRACTION:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("%s is not a manager" % (actor,))
        if (
            not isinstance(new_owner, str)
            or new_owner not in self.reps
            or self.reps[new_owner]["role"] != "rep"
        ):
            raise ValueError("new owner must be a rep: %r" % (new_owner,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already owned by %s" % (new_owner,))
        if self._load(new_owner) >= self.reps[new_owner]["capacity"]:
            raise ValueError("new owner %s is at capacity" % (new_owner,))

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
            weight = FORECAST_WEIGHTS[opp["stage"]]
            weighted += opp["amount"] * weight // 100
        return {"open": open_count, "weighted": weighted, "won": won}
