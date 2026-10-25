"""Simple CRM: lead capture, qualification, conversion, and pipeline management.

Implements the spec in specs/crm.md. Standard library only.
"""

_FINAL_STAGES = ("won", "lost")
_ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
_SOURCES = ("web", "referral", "event")
_BASE_SCORE = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when adding a lead whose normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead for existing id %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.leads = {}
        self.opps = {}
        self.log = []
        self._roles = {}
        self._capacity = {}
        self._queue = []  # FIFO of waiting lead ids (owner is None)
        self._lead_seq = 0
        self._opp_seq = 0
        for rep in reps:
            self._roles[rep["id"]] = rep["role"]
            self._capacity[rep["id"]] = rep["capacity"]

    # ---- internal helpers -------------------------------------------------

    def _require_user(self, actor):
        if not isinstance(actor, str) or actor not in self._roles:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._roles.get(actor) == "manager"

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                n += 1
        return n

    def _pick_rep(self):
        candidates = [
            uid
            for uid, role in self._roles.items()
            if role == "rep" and self._load(uid) < self._capacity[uid]
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda uid: (self._load(uid), uid))

    def _free_slot(self, rep_id):
        """Assign oldest waiting leads to rep_id while it has room."""
        while self._queue and self._load(rep_id) < self._capacity[rep_id]:
            lead_id = self._queue.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        """Return (normalized_email, domain); raise ValueError if invalid."""
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
            raise ValueError("email domain is invalid")
        return norm, domain

    # ---- public API --------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._require_user(actor)
        norm, domain = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in _SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])
        score = _BASE_SCORE[source]
        if domain not in _FREE_DOMAINS:
            score += 15
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        owner = self._pick_rep()
        lead = {
            "id": lead_id,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        if owner is None:
            self._queue.append(lead_id)
        self.leads[lead_id] = lead
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_user(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may qualify")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_user(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may convert")
        if lead["status"] != "qualified":
            raise ValueError("lead must be qualified")
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
        self._require_user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may advance")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is closed")
        expected_next = _STAGE_ORDER[_STAGE_ORDER.index(opp["stage"]) + 1]
        if stage != "lost" and stage != expected_next:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required to negotiate large deals")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may discount")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is closed")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if not isinstance(new_owner, str) or self._roles.get(new_owner) != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is closed")
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already owned by that rep")
        if self._load(new_owner) >= self._capacity[new_owner]:
            raise ValueError("new owner is at capacity")
        old_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(old_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            if opp["stage"] in _FINAL_STAGES:
                if opp["stage"] == "won":
                    won_total += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
