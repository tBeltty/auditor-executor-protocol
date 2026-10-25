"""crm.py — CRM module per /tmp/aep-lab/specs/crm.md."""


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__(f"duplicate lead, existing id: {existing_id}")
        self.existing_id = existing_id


_VALID_SOURCES = ("web", "referral", "event")
_SCORE_BY_SOURCE = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")

_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_FINAL_STAGES = ("won", "lost")
_NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class CRM:
    def __init__(self, reps):
        self._users = {}
        for r in reps:
            self._users[r["id"]] = dict(r)
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO list of lead ids with no owner
        self._lead_counter = 0
        self._opp_counter = 0

    # -- helpers -----------------------------------------------------------

    def _check_actor(self, actor):
        if actor not in self._users:
            raise PermissionError(f"unknown actor: {actor}")

    def _is_manager(self, actor_id):
        return self._users.get(actor_id, {}).get("role") == "manager"

    def _reps(self):
        return [u["id"] for u in self._users.values() if u["role"] == "rep"]

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                n += 1
        return n

    def _capacity(self, rep_id):
        return self._users[rep_id]["capacity"]

    def _pick_owner(self):
        """Rep with lowest load among reps whose load is below capacity;
        ties broken by smallest id in string order."""
        best = None
        best_load = None
        for rep_id in sorted(self._reps()):
            load = self._load(rep_id)
            if load < self._capacity(rep_id):
                if best_load is None or load < best_load:
                    best, best_load = rep_id, load
        return best

    def _drain_waiting(self, rep_id):
        """Assign oldest waiting leads to rep while its load is below capacity."""
        if rep_id is None:
            return
        while self._waiting and self._load(rep_id) < self._capacity(rep_id):
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- API ---------------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        # 1. email
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("email must have a non-empty part before '@'")
        if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
            raise ValueError("email domain must contain a '.' that is neither "
                             "first nor last character of the domain")

        # 2. name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        # 3. source
        if source not in _VALID_SOURCES:
            raise ValueError(f"invalid source: {source!r}")

        # 4. duplicate
        for lead_id, lead in self.leads.items():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead_id)

        # 5. id and score
        self._lead_counter += 1
        lead_id = f"L{self._lead_counter}"
        score = _SCORE_BY_SOURCE[source]
        if domain not in _FREE_DOMAINS:
            score += 15

        # 6. owner / waiting queue
        owner = self._pick_owner()

        # 7. store and log
        self.leads[lead_id] = {
            "id": lead_id,
            "email": norm,
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
        self._check_actor(actor)

        # 1. lead exists
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError(f"unknown lead: {lead_id}")
        # 2. owner or manager
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor is not the lead's owner or a manager")
        # 3. status must be new
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        # 4. score
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)

        # 1. lead exists
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError(f"unknown lead: {lead_id}")
        # 2. amount positive int, not bool
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        # 3. owner or manager
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor is not the lead's owner or a manager")
        # 4. status qualified
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        # 5. must have an owner
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_counter += 1
        opp_id = f"O{self._opp_counter}"
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

        # 1. opp exists
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError(f"unknown opportunity: {opp_id}")
        # 2. stage valid
        if stage not in _STAGES:
            raise ValueError(f"invalid stage: {stage!r}")
        # 3. owner or manager
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        # 4. current stage not final
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("current stage is final")
        # 5. lost or immediate next stage
        if stage != "lost" and stage != _NEXT_STAGE[opp["stage"]]:
            raise ValueError("stage is not the immediate next stage or 'lost'")
        # 6. negotiation gate for large deals
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("moving to negotiation with amount > 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._drain_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)

        # 1. opp exists
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError(f"unknown opportunity: {opp_id}")
        # 2. pct int (not bool) in [1, 30]
        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        # 3. owner or manager
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        # 4. stage not final
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage is final")
        # 5. rep limit of 10
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager actors may discount at most 10 percent")
        # 6. cumulative floor of 70% of original amount
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)

        # 1. opp exists
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError(f"unknown opportunity: {opp_id}")
        # 2. manager only
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer opportunities")
        # 3. new_owner must be a known rep
        user = self._users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a known user with role 'rep'")
        # 4. stage not final
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage is final")
        # 5. different owner
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        # 6. new owner has capacity
        if self._load(new_owner) >= self._capacity(new_owner):
            raise ValueError("new owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._drain_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won_total += opp["amount"]
            elif stage == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
