"""CRM module: lead routing, qualification, conversion, pipeline management."""

FREE_MAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
VALID_SOURCES = ("web", "referral", "event")
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
SCORE_BY_SOURCE = {"web": 10, "referral": 30, "event": 20}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead for existing id %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {}
        self.rep_ids = []
        for rep in reps:
            self.users[rep["id"]] = {"role": rep["role"], "capacity": rep["capacity"]}
            if rep["role"] == "rep":
                self.rep_ids.append(rep["id"])
        self.leads = {}
        self.opps = {}
        self.log = []
        self._queue = []  # FIFO of lead ids waiting for an owner
        self._lead_seq = 0
        self._opp_seq = 0

    # -- helpers -----------------------------------------------------------

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
        best_load = None
        for rid in sorted(self.rep_ids):
            capacity = self.users[rid]["capacity"]
            if capacity <= 0:
                continue
            load = self._load(rid)
            if load < capacity and (best is None or load < best_load):
                best, best_load = rid, load
        return best

    def _free_slot(self, rep_id):
        """Assign oldest waiting leads to rep while load < capacity."""
        if rep_id is None or rep_id not in self.users or rep_id not in self.rep_ids:
            return
        while self._queue and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self._queue[0]
            lead = self.leads[lead_id]
            if lead["owner"] is not None:
                self._queue.pop(0)
                continue
            self._queue.pop(0)
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- API ---------------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if not domain or "." not in domain[1:-1]:
            raise ValueError("invalid email domain")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in VALID_SOURCES:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        score = SCORE_BY_SOURCE[source]
        if domain not in FREE_MAIL_DOMAINS:
            score += 15
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
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
            self._queue.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor cannot qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor cannot convert this lead")
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
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        if stage not in STAGES:
            raise ValueError("invalid stage")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor cannot advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost" and STAGE_ORDER[STAGE_ORDER.index(opp["stage"]) + 1] != stage:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for negotiation above 50000")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor cannot discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("rep discount over 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new owner must be a rep")
        opp = self.opps[opp_id]
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is the current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
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
