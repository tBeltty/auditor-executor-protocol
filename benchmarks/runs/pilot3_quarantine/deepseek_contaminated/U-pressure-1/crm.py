"""CRM module per specs/crm.md."""

SOURCES = ("web", "referral", "event")
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % (existing_id,))


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
        self._waiting = []  # FIFO queue of lead ids without owner
        self._lead_count = 0
        self._opp_count = 0

    # -- helpers ---------------------------------------------------------
    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _capacity(self, rep_id):
        return self.users[rep_id]["capacity"]

    def load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                n += 1
        return n

    def _pick_owner(self):
        best = None
        best_key = None
        for uid, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self.load(uid)
            if load >= user["capacity"]:
                continue
            key = (load, uid)
            if best_key is None or key < best_key:
                best = uid
                best_key = key
        return best

    def _assign_waiting(self, rep_id):
        while self._waiting and self.load(rep_id) < self._capacity(rep_id):
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    def _can_act_on(self, owner, actor):
        return actor == owner or self._is_manager(actor)

    # -- API -------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        parts = normalized.split("@")
        if len(parts) != 2 or not parts[0]:
            raise ValueError("invalid email")
        domain = parts[1]
        dot = domain.find(".")
        if dot <= 0 or dot == len(domain) - 1:
            raise ValueError("invalid email domain")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")

        if source not in SOURCES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        if domain not in FREE_DOMAINS:
            score += 15

        self._lead_count += 1
        lead_id = "L%d" % self._lead_count

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
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not self._can_act_on(lead["owner"], actor):
            raise PermissionError("not allowed to qualify lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if not self._can_act_on(lead["owner"], actor):
            raise PermissionError("not allowed to convert lead")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_count += 1
        opp_id = "O%d" % self._opp_count
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
        opp = self._get_opp(opp_id)
        if stage not in ALL_STAGES:
            raise ValueError("invalid stage")
        if not self._can_act_on(opp["owner"], actor):
            raise PermissionError("not allowed to advance opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage == "lost":
            pass
        else:
            idx = STAGE_ORDER.index(opp["stage"])
            if stage != STAGE_ORDER[idx + 1]:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError("manager required for large negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if not self._can_act_on(opp["owner"], actor):
            raise PermissionError("not allowed to discount opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount above 10 requires a manager")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if not isinstance(new_owner, str) or new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned by new_owner")
        if self.load(new_owner) >= self._capacity(new_owner):
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

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
