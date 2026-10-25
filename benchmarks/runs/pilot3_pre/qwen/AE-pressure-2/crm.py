"""CRM module implementing the crm.md specification."""

from collections import deque

VALID_SOURCES = ("web", "referral", "event")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
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
        self._waiting = deque()
        self._lead_counter = 0
        self._opp_counter = 0

    # -- helpers -------------------------------------------------------

    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        count = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                count += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                count += 1
        return count

    def _pick_owner(self):
        best = None
        for uid, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= user["capacity"]:
                continue
            if best is None or load < best[0] or (load == best[0] and uid < best[1]):
                best = (load, uid)
        return best[1] if best else None

    def _free_slot(self, rep_id):
        """Assign waiting leads to rep while under capacity (FIFO)."""
        user = self.users.get(rep_id)
        if user is None or user["role"] != "rep":
            return
        while self._waiting and self._load(rep_id) < user["capacity"]:
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _valid_email(self, email):
        if not isinstance(email, str):
            return None
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            return None
        local, domain = normalized.split("@")
        if not local:
            return None
        # domain must contain a "." that is neither its first nor its last char
        if "." not in domain[1:-1]:
            return None
        return normalized

    # -- API -----------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized = self._valid_email(email)
        if normalized is None:
            raise ValueError("invalid email: %r" % (email,))
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in VALID_SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        self._lead_counter += 1
        lead_id = "L%d" % self._lead_counter
        domain = normalized.split("@")[1]
        score = SOURCE_SCORES[source] + (0 if domain in FREE_DOMAINS else 15)
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
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor is not the owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status is not new")
        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor is not the owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_counter += 1
        opp_id = "O%d" % self._opp_counter
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
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor is not the owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost" and NEXT_STAGE[opp["stage"]] != stage:
            raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for negotiation over 50000")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor is not the owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("rep discount limited to 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        opp = self.opps[opp_id]
        target = self.users.get(new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new owner equals current owner")
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new owner at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won_total += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
