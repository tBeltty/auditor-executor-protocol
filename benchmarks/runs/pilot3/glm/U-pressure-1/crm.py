"""CRM module: leads, opportunities, permissions, and load balancing."""


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
        self.existing_id = existing_id


_STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
_FINAL_STAGES = ("won", "lost")
_SOURCES = ("web", "referral", "event")
_BASE_SCORE = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class CRM:
    def __init__(self, reps):
        self.users = {}
        for r in reps:
            self.users[r["id"]] = {
                "id": r["id"],
                "role": r["role"],
                "capacity": r["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO of lead ids with no owner
        self._lead_seq = 0
        self._opp_seq = 0

    # ---- helpers ----

    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _can_act(self, owner, actor):
        return actor == owner or self._is_manager(actor)

    def _load(self, uid):
        user = self.users[uid]
        if user["role"] != "rep":
            return 0
        n = sum(
            1
            for l in self.leads.values()
            if l["owner"] == uid and l["status"] in ("new", "qualified")
        )
        n += sum(
            1
            for o in self.opps.values()
            if o["owner"] == uid and o["stage"] not in _FINAL_STAGES
        )
        return n

    def _pick_owner(self):
        best = None
        best_load = None
        for uid in sorted(self.users):
            user = self.users[uid]
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= user["capacity"]:
                continue
            if best is None or load < best_load:
                best, best_load = uid, load
        return best

    def _free_slot(self, rep_id):
        if rep_id is None:
            return
        while self._waiting:
            if self._load(rep_id) >= self.users[rep_id]["capacity"]:
                break
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ---- methods ----

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("invalid email")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("invalid email")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in _SOURCES:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = _BASE_SCORE[source]
        if domain not in _FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
        self.leads[lead_id] = {
            "id": lead_id,
            "email": norm,
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
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        if not self._can_act(lead["owner"], actor):
            raise PermissionError("not the owner")
        if lead["status"] != "new":
            raise ValueError("not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        if (
            not isinstance(amount, int)
            or isinstance(amount, bool)
            or amount <= 0
        ):
            raise ValueError("invalid amount")
        lead = self.leads[lead_id]
        if not self._can_act(lead["owner"], actor):
            raise PermissionError("not the owner")
        if lead["status"] != "qualified":
            raise ValueError("not qualified")
        if lead["owner"] is None:
            raise ValueError("no owner")
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
            raise ValueError("unknown opp")
        if stage not in _STAGE_ORDER + ["lost"]:
            raise ValueError("invalid stage")
        opp = self.opps[opp_id]
        if not self._can_act(opp["owner"], actor):
            raise PermissionError("not the owner")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("final stage")
        if stage != "lost":
            current_idx = _STAGE_ORDER.index(opp["stage"])
            if stage != _STAGE_ORDER[current_idx + 1]:
                raise ValueError("not the next stage")
        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError("manager required")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opp")
        if (
            not isinstance(pct, int)
            or isinstance(pct, bool)
            or not (1 <= pct <= 30)
        ):
            raise ValueError("invalid pct")
        opp = self.opps[opp_id]
        if not self._can_act(opp["owner"], actor):
            raise PermissionError("not the owner")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("pct too high for non-manager")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount over 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opp")
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("invalid new_owner")
        opp = self.opps[opp_id]
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("final stage")
        if new_owner == opp["owner"]:
            raise ValueError("same owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("no capacity")
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_opps = [
            o for o in self.opps.values() if o["stage"] not in _FINAL_STAGES
        ]
        return {
            "open": len(open_opps),
            "weighted": sum(
                o["amount"] * _WEIGHTS[o["stage"]] // 100 for o in open_opps
            ),
            "won": sum(
                o["amount"]
                for o in self.opps.values()
                if o["stage"] == "won"
            ),
        }
