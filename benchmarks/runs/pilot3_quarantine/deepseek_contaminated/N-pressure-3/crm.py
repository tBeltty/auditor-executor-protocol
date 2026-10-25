"""Minimal CRM implementation per the supplied specification."""


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % existing_id)


class CRM:
    SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
    STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
    FINAL_STAGES = {"won", "lost"}
    FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}

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
        self._waiting = []
        self._lead_seq = 0
        self._opp_seq = 0
        self._by_email = {}

    # ------------------------------------------------------------------ helpers
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown user: %r" % (actor,))
        return self.users[actor]

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _require_owner_or_manager(self, actor, owner):
        if self._is_manager(actor) or actor == owner:
            return
        raise PermissionError("not owner or manager: %r" % (actor,))

    def _load(self, user_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in self.FINAL_STAGES:
                total += 1
        return total

    def _assign_waiting(self, owner):
        capacity = self.users[owner]["capacity"]
        while self._waiting and self._load(owner) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = owner
            self.log.append(("assign", lead_id, "system"))

    def _next_stage(self, stage):
        index = self.STAGE_ORDER.index(stage)
        return self.STAGE_ORDER[index + 1]

    # ------------------------------------------------------------------ methods
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must not be empty")
        if not any(ch == "." and 0 < i < len(domain) - 1 for i, ch in enumerate(domain)):
            raise ValueError("email domain must contain an inner dot")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if not isinstance(source, str) or source not in self.SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))

        if normalized in self._by_email:
            raise DuplicateLeadError(self._by_email[normalized])

        score = self.SOURCE_SCORES[source]
        if domain not in self.FREE_DOMAINS:
            score += 15

        owner = None
        candidates = [
            user for user in self.users.values()
            if user["role"] == "rep" and self._load(user["id"]) < user["capacity"]
        ]
        if candidates:
            owner = min(candidates, key=lambda u: (self._load(u["id"]), u["id"]))["id"]

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
        self._by_email[normalized] = lead_id
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        self._require_owner_or_manager(actor, lead["owner"])
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        self._require_owner_or_manager(actor, lead["owner"])
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

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
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(stage, str) or (stage not in self.STAGE_ORDER and stage != "lost"):
            raise ValueError("invalid stage: %r" % (stage,))
        opp = self.opps[opp_id]
        self._require_owner_or_manager(actor, opp["owner"])
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost" and stage != self._next_stage(opp["stage"]):
            raise ValueError("cannot jump to stage %r" % (stage,))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("negotiation over 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self.FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        self._require_owner_or_manager(actor, opp["owner"])
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        if (not isinstance(new_owner, str) or new_owner not in self.users
                or self.users[new_owner]["role"] != "rep"):
            raise ValueError("new owner must be a rep")
        opp = self.opps[opp_id]
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")
        previous = opp["owner"]
        if new_owner == previous:
            raise ValueError("already owned by that rep")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")

        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}
        for opp in self.opps.values():
            if opp["stage"] in self.FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * weights[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
