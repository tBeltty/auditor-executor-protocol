"""CRM lead/opportunity pipeline implementing the crm.md spec."""

from collections import deque

STAGES = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = ("won", "lost")
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % existing_id)


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

    # -- helpers ---------------------------------------------------------
    def _known(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _check_access(self, owner, actor, action):
        """Allow the record's owner or any manager; caller has already run _known."""
        if actor != owner and not self._is_manager(actor):
            raise PermissionError("not allowed to %s" % action)

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        best = None
        best_load = None
        for user in self.users.values():
            if user["role"] != "rep":
                continue
            load = self._load(user["id"])
            if load >= user["capacity"]:
                continue
            if (best is None or load < best_load
                    or (load == best_load and user["id"] < best)):
                best = user["id"]
                best_load = load
        return best

    def _assign_waiting(self, rep_id):
        while self.waiting and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self.waiting.popleft()
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- methods ---------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._known(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("email needs a local part")
        if not any(domain[i] == "." for i in range(1, len(domain) - 1)):
            raise ValueError("email domain needs a dot")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SOURCE_SCORES[source]
        if domain not in FREE_DOMAINS:
            score += 15

        owner = self._pick_owner()
        lead = {
            "id": lead_id,
            "email": norm,
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
        self._known(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        self._check_access(lead["owner"], actor, "qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._known(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        self._check_access(lead["owner"], actor, "convert this lead")
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
        self._known(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in STAGES and stage != "lost":
            raise ValueError("invalid stage: %r" % (stage,))
        self._check_access(opp["owner"], actor, "advance this opportunity")
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost" and stage != STAGES[STAGES.index(current) + 1]:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("large deal needs a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._known(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int in 1..30")
        self._check_access(opp["owner"], actor, "discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._known(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        user = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if user is None or user["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned by that rep")
        if self._load(new_owner) >= user["capacity"]:
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
            if opp["stage"] == "won":
                won += opp["amount"]
            elif opp["stage"] == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
