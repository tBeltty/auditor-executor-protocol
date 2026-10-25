"""crm.py — CRM with capacity-based lead routing (specs/crm.md)."""

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s.]+\.[^@\s]+$")


class DuplicateLeadError(Exception):
    """Raised when adding a lead whose normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__(f"duplicate lead for email, existing id {existing_id}")
        self.existing_id = existing_id


NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation",
              "negotiation": "won"}
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
ACTIVE_LEAD_STATUSES = ("new", "qualified")
STAGE_WEIGHT = {"prospect": 10, "proposal": 30, "negotiation": 60}
SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
VALID_SOURCES = ("web", "referral", "event")


class CRM:
    def __init__(self, reps):
        self.leads = {}
        self.opps = {}
        self.log = []
        self._users = {}
        self._waiting = []          # FIFO of lead ids with no owner
        self._lead_count = 0
        self._opp_count = 0
        for user in reps:
            self._users[user["id"]] = dict(user)

    # ------------------------------------------------------------------ core

    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError(f"unknown actor {actor!r}")

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ACTIVE_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        """Lowest-load rep below capacity; ties broken by smallest id string."""
        best = None
        best_key = None
        for uid, user in self._users.items():
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= user["capacity"]:
                continue
            key = (load, uid)
            if best_key is None or key < best_key:
                best, best_key = uid, key
        return best

    def _fill_slot(self, rep_id):
        """Assign oldest waiting leads while the rep is below capacity."""
        capacity = self._users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------- API

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = norm.split("@", 1)
        if not local:
            raise ValueError("email local part must be non-empty")
        if "." not in domain[1:-1]:
            raise ValueError("email domain must contain a '.' that is neither "
                             "the first nor the last character of the domain")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in VALID_SOURCES:
            raise ValueError(f"invalid source {source!r}")
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])
        self._lead_count += 1
        lead_id = f"L{self._lead_count}"
        score = SOURCE_SCORE[source]
        if domain not in FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
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
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError(f"unknown lead {lead_id!r}")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor must be the lead owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError(f"unknown lead {lead_id!r}")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor must be the lead owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead must be qualified to convert")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_count += 1
        opp_id = f"O{self._opp_count}"
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
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError(f"unknown opportunity {opp_id!r}")
        if stage not in STAGES:
            raise ValueError(f"invalid stage {stage!r}")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor must be the opp owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        if stage != "lost" and NEXT_STAGE[opp["stage"]] != stage:
            raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError(
                    "moving to negotiation with amount > 50000 requires a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._fill_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError(f"unknown opportunity {opp_id!r}")
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor must be the opp owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError(f"unknown opportunity {opp_id!r}")
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        user = self._users.get(new_owner) if isinstance(new_owner, str) else None
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is already the owner")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new_owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill_slot(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHT[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
