"""CRM module implementing lead intake, qualification, conversion and pipeline
management as specified in the module spec.

The public surface is ``CRM`` and ``DuplicateLeadError``.  Every mutating method
takes the acting user id as its ``actor`` argument, validates the acting user
before anything else, and performs all validation before touching state so a
failed call leaves the instance byte-for-byte unchanged and logs nothing.
"""

from collections import deque

_LEAD_SOURCES = ("web", "referral", "event")
_STAGES = ("prospect", "proposal", "negotiation", "won")
_FINAL_STAGES = ("won", "lost")
_OPEN_STAGES = ("prospect", "proposal", "negotiation")
_CONSUMER_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
_BASE_SCORES = {"web": 10, "referral": 30, "event": 20}
_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead already exists for the normalized email."""

    def __init__(self, existing_id):
        super().__init__("lead already exists: %s" % existing_id)
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
        self.waiting = deque()
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _role(self, actor):
        return self.users[actor]["role"]

    def _is_manager(self, actor):
        return self._role(actor) == "manager"

    def _load(self, rep_id):
        """A rep's load: open leads it owns + open opportunities it owns."""
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] in _OPEN_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        """Lowest-load rep below capacity, ties broken by smallest id."""
        candidates = []
        for rep_id, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self._load(rep_id)
            if load < user["capacity"]:
                candidates.append((load, rep_id))
        if not candidates:
            return None
        candidates.sort(key=lambda item: (item[0], item[1]))
        return candidates[0][1]

    def _assign_waiting(self, rep_id):
        """Give queued leads to ``rep_id`` while it has free capacity (FIFO)."""
        capacity = self.users[rep_id]["capacity"]
        while self.waiting and self._load(rep_id) < capacity:
            lead_id = self.waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
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
        # Spec rule: the domain must contain "." at some index that is
        # neither the first nor the last character.  This is existential --
        # a domain such as "b.com." is valid because of the dot at index 1,
        # even though it also ends with a dot.
        if not any(
            ch == "." and 0 < index < len(domain) - 1
            for index, ch in enumerate(domain)
        ):
            raise ValueError("email domain must contain an interior '.'")
        return normalized

    @staticmethod
    def _email_domain(email):
        return email.split("@", 1)[1]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in _LEAD_SOURCES:
            raise ValueError("source must be web, referral or event")
        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])

        score = _BASE_SCORES[source]
        if self._email_domain(normalized) not in _CONSUMER_DOMAINS:
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
        lead = self._get_lead(lead_id)
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead status must be new")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._get_lead(lead_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be qualified")
        if lead["owner"] is None:
            raise ValueError("lead must have an owner")

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
        opp = self._get_opp(opp_id)
        if stage not in _STAGES and stage != "lost":
            raise ValueError("unknown stage: %r" % (stage,))
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not advance this opportunity")
        current = opp["stage"]
        if current in _FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost" and stage != _STAGES[_STAGES.index(current) + 1]:
            raise ValueError("stage may only move to the immediate next stage")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("negotiation over 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer opportunities")
        if not isinstance(new_owner, str) or new_owner not in self.users:
            raise ValueError("new_owner must be a known user")
        if self.users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner has no free capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in _OPEN_STAGES:
                open_count += 1
                weighted += opp["amount"] * _STAGE_WEIGHTS[stage] // 100
            elif stage == "won":
                won += opp["amount"]
        return {"open": open_count, "weighted": weighted, "won": won}

    # ------------------------------------------------------------------
    # Lookup helpers (raise ValueError for anything that is not a known id)
    # ------------------------------------------------------------------
    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]
