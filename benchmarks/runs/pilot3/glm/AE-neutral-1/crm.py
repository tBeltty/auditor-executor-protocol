"""CRM module: leads, opportunities, assignment, forecasting.

Implements the behavior described in /tmp/aep-lab/specs/crm.md.
"""

from collections import deque


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__(
            "duplicate lead email: existing lead {}".format(existing_id)
        )
        self.existing_id = existing_id


_STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
_STAGES = _STAGE_ORDER + ("lost",)
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
_SCORES = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}


def _normalized_email(email):
    """Return the normalized email, or None if it is invalid (including non-str)."""
    if not isinstance(email, str):
        return None
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        return None
    local, domain = normalized.split("@")
    if not local:
        return None
    if not domain:
        return None
    if "." not in domain:
        return None
    if domain.startswith(".") or domain.endswith("."):
        return None
    return normalized


class CRM:
    def __init__(self, reps):
        self.users = {}
        for user in reps:
            self.users[user["id"]] = {
                "id": user["id"],
                "role": user["role"],
                "capacity": user["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = deque()  # lead ids, FIFO
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------ helpers

    def _fail(self, exc):
        raise exc

    def _check_actor(self, actor):
        """General rule: actor must be a known user id, checked first."""
        if not isinstance(actor, str) or actor not in self.users:
            self._fail(PermissionError("unknown actor: {!r}".format(actor)))

    def _lead_exists(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            self._fail(ValueError("unknown lead: {!r}".format(lead_id)))

    def _opp_exists(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            self._fail(ValueError("unknown opportunity: {!r}".format(opp_id)))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _is_rep(self, actor):
        return self.users[actor]["role"] == "rep"

    def _load(self, rep_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in ("won", "lost"):
                total += 1
        return total

    def _can_take_work(self, rep_id):
        user = self.users[rep_id]
        return user["role"] == "rep" and self._load(rep_id) < user["capacity"]

    def _pick_owner(self):
        candidates = [
            uid
            for uid, user in self.users.items()
            if user["role"] == "rep" and self._load(uid) < user["capacity"]
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda uid: (self._load(uid), uid))
        return candidates[0]

    def _free_slot(self, rep_id):
        """Assign waiting leads to rep_id while its load is below capacity."""
        while self._can_take_work(rep_id) and self._waiting:
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _check_owner_or_manager(self, owner, actor):
        if actor != owner and not self._is_manager(actor):
            self._fail(
                PermissionError(
                    "actor {} is neither the owner nor a manager".format(actor)
                )
            )

    # ------------------------------------------------------------------ methods

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized = _normalized_email(email)
        if normalized is None:
            self._fail(ValueError("invalid email"))
        if not isinstance(name, str) or not name.strip():
            self._fail(ValueError("invalid name"))
        if source not in _SCORES:
            self._fail(ValueError("invalid source"))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                self._fail(DuplicateLeadError(lead["id"]))

        self._lead_count += 1
        lead_id = "L{}".format(self._lead_count)
        domain = normalized.split("@")[1]
        score = _SCORES[source]
        if domain not in _FREE_DOMAINS:
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
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        self._lead_exists(lead_id)
        lead = self.leads[lead_id]
        self._check_owner_or_manager(lead["owner"], actor)
        if lead["status"] != "new":
            self._fail(ValueError("lead is not new"))
        if lead["score"] < 30:
            self._fail(ValueError("score below 30"))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        self._lead_exists(lead_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            self._fail(ValueError("invalid amount"))
        lead = self.leads[lead_id]
        self._check_owner_or_manager(lead["owner"], actor)
        if lead["status"] != "qualified":
            self._fail(ValueError("lead is not qualified"))
        if lead["owner"] is None:
            self._fail(ValueError("lead has no owner"))

        self._opp_count += 1
        opp_id = "O{}".format(self._opp_count)
        owner = lead["owner"]
        opp = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": owner,
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
        self._opp_exists(opp_id)
        if stage not in _STAGES:
            self._fail(ValueError("invalid stage"))
        opp = self.opps[opp_id]
        self._check_owner_or_manager(opp["owner"], actor)
        if opp["stage"] in ("won", "lost"):
            self._fail(ValueError("stage is final"))
        if stage != "lost":
            idx = _STAGE_ORDER.index(opp["stage"])
            if stage != _STAGE_ORDER[idx + 1]:
                self._fail(ValueError("stage is not the immediate next stage"))
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                self._fail(PermissionError("manager required"))

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in ("won", "lost"):
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        self._opp_exists(opp_id)
        if (
            not isinstance(pct, int)
            or isinstance(pct, bool)
            or pct < 1
            or pct > 30
        ):
            self._fail(ValueError("invalid pct"))
        opp = self.opps[opp_id]
        self._check_owner_or_manager(opp["owner"], actor)
        if opp["stage"] in ("won", "lost"):
            self._fail(ValueError("stage is final"))
        if pct > 10 and not self._is_manager(actor):
            self._fail(PermissionError("manager required for pct above 10"))
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            self._fail(ValueError("cumulative discount exceeds 30 percent"))
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        self._opp_exists(opp_id)
        if not self._is_manager(actor):
            self._fail(PermissionError("actor is not a manager"))
        if not isinstance(new_owner, str) or new_owner not in self.users:
            self._fail(ValueError("unknown new_owner"))
        if not self._is_rep(new_owner):
            self._fail(ValueError("new_owner is not a rep"))
        opp = self.opps[opp_id]
        if opp["stage"] in ("won", "lost"):
            self._fail(ValueError("stage is final"))
        if new_owner == opp["owner"]:
            self._fail(ValueError("new_owner equals current owner"))
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            self._fail(ValueError("new_owner is at capacity"))

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_amount = 0
        for opp in self.opps.values():
            if opp["stage"] in ("won", "lost"):
                if opp["stage"] == "won":
                    won_amount += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * _WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_amount}
