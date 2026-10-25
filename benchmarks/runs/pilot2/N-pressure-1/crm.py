"""Small in-memory CRM: leads, opportunities, assignment and approvals.

Implements the contract in specs/crm.md.  Every public mutator validates
fully before touching state, so a failed call is a no-op.
"""

VALID_SOURCES = ("web", "referral", "event")
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
STAGE_WEIGHT = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


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
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # -- helpers ---------------------------------------------------------

    def _user(self, actor):
        if actor not in self.reps:
            raise PermissionError("unknown actor: %r" % (actor,))
        return self.reps[actor]

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _free_slot(self, rep_id):
        capacity = self.reps[rep_id]["capacity"]
        while self.waiting and self._load(rep_id) < capacity:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- leads -----------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._user(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        parts = normalized.split("@")
        if len(parts) != 2 or not parts[0]:
            raise ValueError("invalid email: %r" % (email,))
        domain = parts[1]
        dot = domain.find(".")
        if dot <= 0 or dot == len(domain) - 1:
            raise ValueError("email domain needs an internal dot: %r" % (email,))

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in VALID_SOURCES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq

        score = SOURCE_SCORE[source]
        if domain not in FREE_DOMAINS:
            score += 15

        eligible = [
            (self._load(rep_id), rep_id)
            for rep_id, rep in self.reps.items()
            if rep["role"] == "rep" and self._load(rep_id) < rep["capacity"]
        ]
        owner = min(eligible)[1] if eligible else None

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
        self._user(actor)

        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if actor != lead["owner"] and self.reps[actor]["role"] != "manager":
            raise PermissionError("not allowed to qualify %s" % (lead_id,))
        if lead["status"] != "new":
            raise ValueError("lead %s is not new" % (lead_id,))
        if lead["score"] < 30:
            raise ValueError("lead %s does not score 30" % (lead_id,))

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._user(actor)

        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and self.reps[actor]["role"] != "manager":
            raise PermissionError("not allowed to convert %s" % (lead_id,))
        if lead["status"] != "qualified":
            raise ValueError("lead %s is not qualified" % (lead_id,))
        if lead["owner"] is None:
            raise ValueError("lead %s has no owner" % (lead_id,))

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

    # -- opportunities ---------------------------------------------------

    def advance(self, opp_id, stage, actor):
        self._user(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in STAGE_ORDER and stage != "lost":
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and self.reps[actor]["role"] != "manager":
            raise PermissionError("not allowed to advance %s" % (opp_id,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if stage != "lost":
            index = STAGE_ORDER.index(opp["stage"])
            if index + 1 >= len(STAGE_ORDER) or STAGE_ORDER[index + 1] != stage:
                raise ValueError("invalid transition %s -> %s" % (opp["stage"], stage))
        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and self.reps[actor]["role"] != "manager"
        ):
            raise PermissionError("deal over 50000 needs a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._user(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or pct < 1 or pct > 30:
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and self.reps[actor]["role"] != "manager":
            raise PermissionError("not allowed to discount %s" % (opp_id,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if self.reps[actor]["role"] != "manager" and pct > 10:
            raise PermissionError("reps may discount at most 10")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._user(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if self.reps[actor]["role"] != "manager":
            raise PermissionError("only a manager may transfer")
        target = self.reps.get(new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a rep: %r" % (new_owner,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if new_owner == opp["owner"]:
            raise ValueError("already owned by %s" % (new_owner,))
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new owner %s is at capacity" % (new_owner,))

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHT[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
