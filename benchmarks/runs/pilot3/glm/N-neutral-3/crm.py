"""crm.py — a small CRM with leads, opportunities, permissions, forecasting.

Implements `CRM` and `DuplicateLeadError` per the module spec:
- every method first verifies the actor is a known user (PermissionError);
- a failed call changes nothing and appends nothing to `log`;
- checks inside each method run in the documented order;
- reps below capacity own new leads (lowest load wins, ties by smallest id);
- leads added while nobody has capacity wait in a FIFO queue and are
  assigned ("system") whenever a rep's slot is freed;
- opportunities advance prospect -> proposal -> negotiation -> won, may go
  to "lost" from any non-final stage, support capped discounts and
  manager-only transfers.
"""

from collections import deque

__all__ = ["CRM", "DuplicateLeadError"]


class DuplicateLeadError(Exception):
    """Raised by add_lead when the normalized email already exists."""

    def __init__(self, existing_id=None, message=None):
        self.existing_id = existing_id
        if message is None:
            message = "a lead with this email already exists: %s" % (existing_id,)
        super().__init__(message)


_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})
_STAGE_NEXT = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_VALID_STAGES = frozenset(_STAGE_NEXT) | {"won", "lost"}
_FINAL_STAGES = frozenset({"won", "lost"})
_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
_ACTIVE_LEAD_STATUSES = frozenset({"new", "qualified"})


def _normalized_email_is_valid(normalized):
    if normalized.count("@") != 1:
        return False
    local, domain = normalized.split("@")
    if not local:
        return False
    return "." in domain and domain[0] != "." and domain[-1] != "."


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


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
        self._lead_seq = 0
        self._opp_seq = 0
        self._waiting = deque()

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #
    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _check_owner_or_manager(self, actor, owner):
        if actor != owner and not self._is_manager(actor):
            raise PermissionError(
                "actor %r is not the owner %r or a manager" % (actor, owner))

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in _ACTIVE_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _reps(self):
        return [u for u in self.users.values() if u["role"] == "rep"]

    def _assign_lead(self, lead_id, rep_id):
        lead = self.leads[lead_id]
        lead["owner"] = rep_id
        self.log.append(("assign", lead_id, "system"))

    def _free_slot(self, rep_id):
        if rep_id is None or rep_id not in self.users:
            return
        while self._waiting:
            if self._load(rep_id) >= self.users[rep_id]["capacity"]:
                break
            self._assign_lead(self._waiting.popleft(), rep_id)

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    def _check_not_final(self, opp):
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity %r is final (%s)" % (opp["id"], opp["stage"]))

    # ------------------------------------------------------------------ #
    # leads
    # ------------------------------------------------------------------ #
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if not _normalized_email_is_valid(normalized):
            raise ValueError("invalid email: %r" % (email,))
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in _SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(existing_id=lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq

        domain = normalized.split("@", 1)[1]
        score = _SOURCE_SCORES[source]
        if domain not in _FREE_DOMAINS:
            score += 15

        owner = None
        candidates = [u["id"] for u in self._reps()
                      if self._load(u["id"]) < u["capacity"]]
        if candidates:
            owner = min(candidates, key=lambda rid: (self._load(rid), rid))

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
        lead = self._get_lead(lead_id)
        self._check_owner_or_manager(actor, lead["owner"])
        if lead["status"] != "new":
            raise ValueError("lead %r is not new (status=%s)" % (lead_id, lead["status"]))
        if lead["score"] < 30:
            raise ValueError("lead %r score %d is below 30" % (lead_id, lead["score"]))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self._get_lead(lead_id)
        if not _is_positive_int(amount):
            raise ValueError("amount must be a positive int")
        self._check_owner_or_manager(actor, lead["owner"])
        if lead["status"] != "qualified":
            raise ValueError("lead %r is not qualified (status=%s)"
                             % (lead_id, lead["status"]))
        if lead["owner"] is None:
            raise ValueError("lead %r has no owner" % (lead_id,))

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

    # ------------------------------------------------------------------ #
    # opportunities
    # ------------------------------------------------------------------ #
    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if stage not in _VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        self._check_owner_or_manager(actor, opp["owner"])
        self._check_not_final(opp)
        if stage != "lost" and _STAGE_NEXT[opp["stage"]] != stage:
            raise ValueError("cannot advance from %s to %s" % (opp["stage"], stage))
        if (stage == "negotiation" and opp["amount"] > 50000
                and not self._is_manager(actor)):
            raise PermissionError(
                "moving to negotiation above 50000 requires a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if (not isinstance(pct, int) or isinstance(pct, bool)
                or not (1 <= pct <= 30)):
            raise ValueError("pct must be an int in [1, 30]")
        self._check_owner_or_manager(actor, opp["owner"])
        self._check_not_final(opp)
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount above 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("transfer requires a manager")
        if (not isinstance(new_owner, str) or new_owner not in self.users
                or self.users[new_owner]["role"] != "rep"):
            raise ValueError("new_owner must be a known rep: %r" % (new_owner,))
        self._check_not_final(opp)
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner %r has no free capacity" % (new_owner,))
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    # ------------------------------------------------------------------ #
    # reporting
    # ------------------------------------------------------------------ #
    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] == "won":
                won += opp["amount"]
            elif opp["stage"] != "lost":
                open_count += 1
                weighted += opp["amount"] * _STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
