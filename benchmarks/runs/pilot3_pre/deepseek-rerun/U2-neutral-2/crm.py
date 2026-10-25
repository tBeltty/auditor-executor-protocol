"""CRM lead/opportunity pipeline.

Implements ``CRM`` and ``DuplicateLeadError`` exactly as described in the
module spec: strict check ordering, atomic failing calls, FIFO waiting queue
for unassigned leads and load based ownership.
"""

from collections import deque

__all__ = ["CRM", "DuplicateLeadError"]

STAGES = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
SOURCES = ("web", "referral", "event")
FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

MANAGER = "manager"
REP = "rep"


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id=None):
        self.existing_id = existing_id
        super().__init__("duplicate lead email (existing id: %r)" % (existing_id,))


def _normalize_email(email):
    """Return the normalized email or raise ValueError."""
    if not isinstance(email, str):
        raise ValueError("email must be a string")
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        raise ValueError("email must contain exactly one '@'")
    local, domain = normalized.split("@")
    if not local:
        raise ValueError("email must have a non-empty part before '@'")
    if not domain:
        raise ValueError("email must have a domain after '@'")
    if not any(ch == "." and 0 < index < len(domain) - 1 for index, ch in enumerate(domain)):
        raise ValueError("email domain must contain a '.' that is neither first nor last")
    return normalized


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
        self._waiting = deque()
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _get_user(self, key):
        try:
            return self.users.get(key)
        except TypeError:  # unhashable actor id
            return None

    def _require_actor(self, actor):
        user = self._get_user(actor)
        if user is None:
            raise PermissionError("unknown actor: %r" % (actor,))
        return user

    def _is_manager(self, actor):
        user = self._get_user(actor)
        return user is not None and user["role"] == MANAGER

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        best_id = None
        best_load = None
        for rep_id in sorted(self.users):
            user = self.users[rep_id]
            if user["role"] != REP:
                continue
            load = self._load(rep_id)
            if load >= user["capacity"]:
                continue
            if best_load is None or load < best_load:
                best_id = rep_id
                best_load = load
        return best_id

    def _free_slot(self, rep_id):
        """Hand waiting leads to ``rep_id`` while it has spare capacity."""
        if rep_id is None or rep_id not in self.users:
            return
        capacity = self.users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _require_opp(self, opp_id):
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return opp

    def _require_lead(self, lead_id):
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return lead

    def _require_owner_or_manager(self, owner, actor):
        if actor != owner and not self._is_manager(actor):
            raise PermissionError("actor %r may not act on this entity" % (actor,))

    # ------------------------------------------------------------------
    # leads
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        normalized = _normalize_email(email)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in SOURCES:
            raise ValueError("source must be one of %s" % (", ".join(SOURCES),))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        lead_id = "L%d" % (self._lead_seq + 1,)

        domain = normalized.split("@", 1)[1]
        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._pick_owner()

        self._lead_seq += 1
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
        lead = self._require_lead(lead_id)
        self._require_owner_or_manager(lead["owner"], actor)
        if lead["status"] != "new":
            raise ValueError("lead %r is not new" % (lead_id,))
        if lead["score"] < 30:
            raise ValueError("lead %r score is too low to qualify" % (lead_id,))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._require_lead(lead_id)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive integer")
        self._require_owner_or_manager(lead["owner"], actor)
        if lead["status"] != "qualified":
            raise ValueError("lead %r is not qualified" % (lead_id,))
        if lead["owner"] is None:
            raise ValueError("lead %r has no owner" % (lead_id,))

        opp_id = "O%d" % (self._opp_seq + 1,)
        self._opp_seq += 1
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

    # ------------------------------------------------------------------
    # opportunities
    # ------------------------------------------------------------------
    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if stage not in STAGES and stage != "lost":
            raise ValueError("unknown stage: %r" % (stage,))
        self._require_owner_or_manager(opp["owner"], actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %r is already final" % (opp_id,))
        if stage != "lost":
            current_index = STAGES.index(opp["stage"])
            if stage != STAGES[current_index + 1]:
                raise ValueError("cannot move from %r to %r" % (opp["stage"], stage))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("moving to negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an integer from 1 to 30")
        self._require_owner_or_manager(opp["owner"], actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %r is already final" % (opp_id,))
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer opportunities")
        new_user = self._get_user(new_owner)
        if new_user is None or new_user["role"] != REP:
            raise ValueError("new owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %r is already final" % (opp_id,))
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already belongs to %r" % (new_owner,))
        if self._load(new_owner) >= new_user["capacity"]:
            raise ValueError("new owner %r is at capacity" % (new_owner,))

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    # ------------------------------------------------------------------
    # reporting
    # ------------------------------------------------------------------
    def forecast(self):
        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * weights[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
