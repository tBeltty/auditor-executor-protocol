"""Simple in-memory CRM module."""


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead email")
        self.existing_id = existing_id


_FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_SOURCES = {"web": 10, "referral": 30, "event": 20}
_STAGES = ["prospect", "proposal", "negotiation", "won"]
_FINAL = {"won", "lost"}
_VALID_TARGETS = {"prospect", "proposal", "negotiation", "won", "lost"}


class CRM:
    def __init__(self, reps):
        self._users = {}
        for r in reps:
            self._users[r["id"]] = {"role": r["role"], "capacity": r["capacity"]}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_seq = 0
        self._opp_seq = 0
        self._waiting = []  # FIFO of lead ids

    # -- helpers ----------------------------------------------------------
    def _require_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor")

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL:
                n += 1
        return n

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _pick_owner(self):
        best = None
        for uid, u in self._users.items():
            if u["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= u["capacity"]:
                continue
            if best is None or load < best[0] or (load == best[0] and uid < best[1]):
                best = (load, uid)
        return best[1] if best else None

    def _drain_waiting(self, rep_id):
        u = self._users[rep_id]
        while self._waiting and self._load(rep_id) < u["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- methods ----------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("invalid email")
        dot = domain.find(".")
        if dot <= 0 or dot == len(domain) - 1:
            raise ValueError("invalid email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in _SOURCES:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = _SOURCES[source]
        if domain not in _FREE_DOMAINS:
            score += 15
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
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("no such lead")
        lead = self.leads[lead_id]
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "new":
            raise ValueError("lead not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("no such lead")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("invalid amount")
        lead = self.leads[lead_id]
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "qualified":
            raise ValueError("lead not qualified")
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
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        if stage not in _VALID_TARGETS:
            raise ValueError("invalid stage")
        opp = self.opps[opp_id]
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in _FINAL:
            raise ValueError("final stage")
        idx = _STAGES.index(opp["stage"])
        if stage != "lost" and stage != _STAGES[idx + 1]:
            raise ValueError("stage not next in order")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL:
            self._drain_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        if (
            not isinstance(pct, int)
            or isinstance(pct, bool)
            or pct < 1
            or pct > 30
        ):
            raise ValueError("invalid pct")
        opp = self.opps[opp_id]
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in _FINAL:
            raise ValueError("final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount too large for rep")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount over 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        if new_owner not in self._users or self._users[new_owner]["role"] != "rep":
            raise ValueError("invalid new owner")
        opp = self.opps[opp_id]
        if opp["stage"] in _FINAL:
            raise ValueError("final stage")
        if new_owner == opp["owner"]:
            raise ValueError("same owner")
        if self._load(new_owner) >= self._users[new_owner]["capacity"]:
            raise ValueError("new owner at capacity")
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._drain_waiting(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}
        for opp in self.opps.values():
            if opp["stage"] in _FINAL:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * weights[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
