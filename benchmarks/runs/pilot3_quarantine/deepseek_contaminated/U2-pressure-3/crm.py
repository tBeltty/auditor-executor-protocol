"""CRM module implementing leads, opportunities and forecast per spec."""


FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCES = ("web", "referral", "event")
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
        self.existing_id = existing_id


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


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
        self._waiting = []
        self._lead_counter = 0
        self._opp_counter = 0

    # ---------- helpers ----------

    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.reps:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.reps[actor]["role"] == "manager"

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    def _load(self, rep_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                total += 1
        return total

    def _pick_rep(self):
        loads = {}
        for lead in self.leads.values():
            if lead["status"] in ("new", "qualified"):
                owner = lead["owner"]
                if owner is not None:
                    loads[owner] = loads.get(owner, 0) + 1
        for opp in self.opps.values():
            if opp["stage"] not in FINAL_STAGES:
                owner = opp["owner"]
                loads[owner] = loads.get(owner, 0) + 1
        best = None
        best_load = None
        for rep_id in sorted(self.reps):
            rep = self.reps[rep_id]
            if rep["role"] != "rep":
                continue
            load = loads.get(rep_id, 0)
            if load < rep["capacity"] and (best is None or load < best_load):
                best, best_load = rep_id, load
        return best

    def _assign_waiting(self, rep_id):
        while self._waiting and self._load(rep_id) < self.reps[rep_id]["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, _, domain = normalized.partition("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not domain:
            raise ValueError("email must have a domain")
        if "." not in domain:
            raise ValueError("email domain must contain a dot")
        if domain.startswith(".") or domain.endswith("."):
            raise ValueError("email domain dot must be interior")
        return normalized

    # ---------- commands ----------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        domain = normalized.split("@", 1)[1]
        base = {"web": 10, "referral": 30, "event": 20}[source]
        score = base + (0 if domain in FREE_EMAIL_DOMAINS else 15)

        self._lead_counter += 1
        lead_id = "L%d" % self._lead_counter
        owner = self._pick_rep()
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
        lead = self._get_lead(lead_id)
        if not self._is_manager(actor) and lead["owner"] != actor:
            raise PermissionError("not owner or manager")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self._get_lead(lead_id)
        if not _is_int(amount) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._is_manager(actor) and lead["owner"] != actor:
            raise PermissionError("not owner or manager")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_counter += 1
        opp_id = "O%d" % self._opp_counter
        opp = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        lead["status"] = "converted"
        self.opps[opp_id] = opp
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if stage not in STAGE_ORDER and stage != "lost":
            raise ValueError("invalid stage: %r" % (stage,))
        is_manager = self._is_manager(actor)
        if not is_manager and opp["owner"] != actor:
            raise PermissionError("not owner or manager")
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost":
            idx = STAGE_ORDER.index(current)
            if idx + 1 >= len(STAGE_ORDER) or STAGE_ORDER[idx + 1] != stage:
                raise ValueError("invalid transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not is_manager:
            raise PermissionError("manager required for large negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if not _is_int(pct) or pct < 1 or pct > 30:
            raise ValueError("pct must be an int from 1 to 30")
        is_manager = self._is_manager(actor)
        if not is_manager and opp["owner"] != actor:
            raise PermissionError("not owner or manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not is_manager and pct > 10:
            raise PermissionError("non-manager may discount at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        if (
            not isinstance(new_owner, str)
            or new_owner not in self.reps
            or self.reps[new_owner]["role"] != "rep"
        ):
            raise ValueError("new owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner must differ")
        if self._load(new_owner) >= self.reps[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        if previous is not None:
            self._assign_waiting(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
                continue
            if stage in FINAL_STAGES:
                continue
            open_count += 1
            weighted += opp["amount"] * weights[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
