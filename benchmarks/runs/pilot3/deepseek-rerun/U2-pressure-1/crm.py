"""A small, dependency-free CRM domain model."""

from collections import deque

FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
ALL_STAGES = STAGE_ORDER + ("lost",)
FINAL_STAGES = {"won", "lost"}
FORECAST_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


def _normalize_email(email):
    if not isinstance(email, str):
        raise ValueError("email must be a str")
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        raise ValueError("email must contain exactly one '@'")
    local, domain = normalized.split("@")
    if not local:
        raise ValueError("email must have a non-empty local part")
    if not any(
        char == "." and 0 < index < len(domain) - 1
        for index, char in enumerate(domain)
    ):
        raise ValueError("email domain must contain an inner '.'")
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
        self.waiting = deque()
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        try:
            self.users[actor]
        except (KeyError, TypeError):
            raise PermissionError("unknown user: %r" % (actor,)) from None

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _is_rep(self, user_id):
        try:
            user = self.users[user_id]
        except (KeyError, TypeError):
            return False
        return user["role"] == "rep"

    def _require_lead(self, lead_id):
        try:
            return self.leads[lead_id]
        except (KeyError, TypeError):
            raise ValueError("unknown lead: %r" % (lead_id,)) from None

    def _require_opp(self, opp_id):
        try:
            return self.opps[opp_id]
        except (KeyError, TypeError):
            raise ValueError("unknown opportunity: %r" % (opp_id,)) from None

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
        candidates = []
        for rep_id in self.users:
            if not self._is_rep(rep_id):
                continue
            load = self._load(rep_id)
            if load < self.users[rep_id]["capacity"]:
                candidates.append((load, rep_id))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][1]

    def _assert_can_act_on(self, owner, actor):
        if actor == owner:
            return
        if self._is_manager(actor):
            return
        raise PermissionError("actor may not modify this record")

    def _assign_waiting(self, rep_id):
        while self.waiting and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self.waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized = _normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        domain = normalized.split("@")[1]
        score = SOURCE_SCORES[source]
        if domain not in FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
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
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self._require_lead(lead_id)
        self._assert_can_act_on(lead["owner"], actor)
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._require_lead(lead_id)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        self._assert_can_act_on(lead["owner"], actor)
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
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if stage not in ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        self._assert_can_act_on(opp["owner"], actor)
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        expected = STAGE_ORDER[STAGE_ORDER.index(current) + 1]
        if stage != "lost" and stage != expected:
            raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError("manager required for large negotiation")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        self._assert_can_act_on(opp["owner"], actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        if not self._is_rep(new_owner):
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned by that rep")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        if previous_owner is not None:
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
            weighted += opp["amount"] * FORECAST_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
