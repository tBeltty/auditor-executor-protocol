"""A small CRM module with leads, opportunities and a rep waiting queue."""

from collections import deque

FINAL_STAGES = ("won", "lost")
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
SOURCES = ("web", "referral", "event")
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
BASE_SCORE = {"web": 10, "referral": 30, "event": 20}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % existing_id)


class CRM:
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
        self._lead_n = 0
        self._opp_n = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.reps:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.reps[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _can_own(self, rep_id):
        rep = self.reps[rep_id]
        if rep["role"] != "rep":
            return False
        return self._load(rep_id) < rep["capacity"]

    def _pick_owner(self):
        candidates = [rid for rid in self.reps if self._can_own(rid)]
        if not candidates:
            return None
        return min(candidates, key=lambda rid: (self._load(rid), rid))

    def _fill_slots(self, rep_id):
        while self._can_own(rep_id) and self.waiting:
            lead_id = self.waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _valid_email(self, email):
        if not isinstance(email, str):
            return None
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            return None
        local, domain = normalized.split("@")
        if not local or not domain:
            return None
        if "." not in domain:
            return None
        positions = [i for i, ch in enumerate(domain) if ch == "."]
        if not any(0 < i < len(domain) - 1 for i in positions):
            return None
        return normalized

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized = self._valid_email(email)
        if normalized is None:
            raise ValueError("invalid email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in SOURCES:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        domain = normalized.split("@")[1]
        score = BASE_SCORE[source] + (0 if domain in FREE_DOMAINS else 15)
        self._lead_n += 1
        lead_id = "L%d" % self._lead_n
        owner = self._pick_owner()
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
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("invalid amount")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_n += 1
        opp_id = "O%d" % self._opp_n
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
        if stage not in STAGE_ORDER and stage != "lost":
            raise ValueError("invalid stage")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost":
            current = STAGE_ORDER.index(opp["stage"])
            if stage != STAGE_ORDER[current + 1]:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for large negotiation")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._fill_slots(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("invalid pct")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount too large for rep")
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
            raise PermissionError("manager required")
        if new_owner not in self.reps or self.reps[new_owner]["role"] != "rep":
            raise ValueError("new owner is not a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is current owner")
        if not self._can_own(new_owner):
            raise ValueError("new owner is at capacity")
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill_slots(previous)

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
            weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
