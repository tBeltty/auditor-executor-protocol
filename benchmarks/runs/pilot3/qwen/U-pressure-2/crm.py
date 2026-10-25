"""CRM module implementing the spec in specs/crm.md."""

from collections import deque

_VALID_SOURCES = ("web", "referral", "event")
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
_BASE_SCORE = {"web": 10, "referral": 30, "event": 20}
_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_FINAL = ("won", "lost")
_NEXT = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: existing id %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = deque()  # FIFO of lead ids with no owner
        self._lead_seq = 0
        self._opp_seq = 0

    # -- helpers -------------------------------------------------------

    def _check_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _reps(self):
        return sorted(
            (u for u in self._users.values() if u["role"] == "rep"),
            key=lambda u: u["id"],
        )

    def _load(self, rep_id):
        n = sum(
            1
            for lead in self.leads.values()
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified")
        )
        n += sum(
            1
            for opp in self.opps.values()
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL
        )
        return n

    def _free_load(self):
        """Rep with the lowest load among reps below capacity; ties: smallest id."""
        best = None
        for rep in self._reps():
            load = self._load(rep["id"])
            if load < rep["capacity"]:
                if best is None or load < best[0]:
                    best = (load, rep["id"])
        return best[1] if best else None

    def _free_slot(self, rep_id):
        cap = self._users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < cap:
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _valid_email(norm):
        if norm.count("@") != 1:
            return False
        local, _, domain = norm.partition("@")
        if not local:
            return False
        if "." not in domain[1:-1]:
            return False
        return True

    # -- API -----------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if not self._valid_email(norm):
            raise ValueError("invalid email: %r" % (email,))
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in _VALID_SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        domain = norm.split("@", 1)[1]
        score = _BASE_SCORE[source]
        if domain not in _FREE_DOMAINS:
            score += 15
        owner = self._free_load()
        if owner is None:
            self._waiting.append(lead_id)
        self.leads[lead_id] = {
            "id": lead_id,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
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
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to advance this opportunity")
        if opp["stage"] in _FINAL:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost" and stage != _NEXT[opp["stage"]]:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for negotiation above 50000")
        owner = opp["owner"]
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL:
            self._free_slot(owner)

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to discount this opportunity")
        if opp["stage"] in _FINAL:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("rep discount limited to 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        user = self._users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        if opp["stage"] in _FINAL:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is already the owner")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new owner is at capacity")
        old_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(old_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in _FINAL:
                if stage == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
