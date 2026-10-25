"""crm.py -- in-memory CRM implemented from specs/crm.md.

Every mutating method validates first and mutates last, so a call that raises
leaves the CRM exactly as it was and appends nothing to ``log``.
"""

FREE_EMAIL_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})
SOURCES = ("web", "referral", "event")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
STAGES = frozenset(STAGE_ORDER) | {"lost"}
FINAL_STAGES = frozenset({"won", "lost"})
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead; existing id: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self._users = {}
        self._rep_ids = []
        for rep in reps:
            self._users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
            if rep["role"] == "rep":
                self._rep_ids.append(rep["id"])
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # -- internals ---------------------------------------------------------
    def _user(self, actor):
        if not isinstance(actor, str) or actor not in self._users: raise PermissionError("unknown actor: %r" % (actor,))  # GC-PERM-ACTOR
        return self._users[actor]

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _require_owner_or_manager(self, actor, owner_id):
        if actor != owner_id and not self._is_manager(actor): raise PermissionError("actor %r may not act on owner %r" % (actor, owner_id))  # GC-PERM-OWNER

    def load(self, rep_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                total += 1
        return total

    def _free_slot(self, rep_id):
        while self.waiting and rep_id is not None and self.load(rep_id) < self._users[rep_id]["capacity"]:  # GC-FREE-CAP
            lead_id = self.waiting.pop(0)  # GC-WAIT-FIFO
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- leads -------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._user(actor)
        if not isinstance(email, str): raise ValueError("email must be a string")  # GC-EMAIL-TYPE
        normalized = email.strip().lower()
        local, sep, domain = normalized.partition("@")
        if sep != "@" or normalized.count("@") != 1 or not local: raise ValueError("invalid email: %r" % (email,))  # GC-EMAIL-LOCAL
        if "." not in domain[1:-1]: raise ValueError("invalid email domain: %r" % (email,))  # GC-EMAIL-DOMAIN
        if not isinstance(name, str) or not name.strip(): raise ValueError("name must be a non-empty string")  # GC-NAME
        if source not in SOURCES: raise ValueError("invalid source: %r" % (source,))  # GC-SOURCE
        for existing in self.leads.values():
            if existing["email"] == normalized: raise DuplicateLeadError(existing["id"])  # GC-DUP

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        candidates = [self._users[rid] for rid in self._rep_ids if self.load(rid) < self._users[rid]["capacity"]]  # GC-ASSIGN-CAP
        if candidates:
            owner = min(candidates, key=lambda u: (self.load(u["id"]), u["id"]))["id"]  # GC-ASSIGN-TIE
        else:
            owner = None

        self._lead_seq += 1  # GC-SEQ
        lead_id = "L%d" % self._lead_seq
        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        if owner is None: self.waiting.append(lead_id)  # GC-WAIT
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._user(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        self._require_owner_or_manager(actor, lead["owner"])
        if lead["status"] != "new":
            raise ValueError("lead %r is not new" % (lead_id,))
        if lead["score"] < 30: raise ValueError("score %d is below 30" % (lead["score"],))  # GC-QUAL-SCORE
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # -- opportunities -----------------------------------------------------
    def convert(self, lead_id, amount, actor):
        self._user(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0: raise ValueError("amount must be a positive int")  # GC-AMOUNT
        self._require_owner_or_manager(actor, lead["owner"])
        if lead["status"] != "qualified":
            raise ValueError("lead %r is not qualified" % (lead_id,))
        if lead["owner"] is None:
            raise ValueError("lead %r has no owner" % (lead_id,))

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
        self._user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in STAGES:
            raise ValueError("unknown stage: %r" % (stage,))
        self._require_owner_or_manager(actor, opp["owner"])
        if opp["stage"] in FINAL_STAGES: raise ValueError("opportunity %r is final" % (opp_id,))  # GC-STAGE-FINAL
        position = STAGE_ORDER.index(opp["stage"])
        following = STAGE_ORDER[position + 1] if position + 1 < len(STAGE_ORDER) else None
        if stage != "lost" and stage != following: raise ValueError("illegal transition %r -> %r" % (opp["stage"], stage))  # GC-STAGE-NEXT
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor): raise PermissionError("negotiation over 50000 needs a manager")  # GC-BIGDEAL

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or pct < 1 or pct > 30: raise ValueError("pct must be an int from 1 to 30")  # GC-DISC-RANGE
        self._require_owner_or_manager(actor, opp["owner"])
        if opp["stage"] in FINAL_STAGES: raise ValueError("opportunity %r is final" % (opp_id,))  # GC-DISC-FINAL
        if pct > 10 and not self._is_manager(actor): raise PermissionError("discount over 10 percent needs a manager")  # GC-DISC-REP

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70: raise ValueError("cumulative discount would exceed 30 percent")  # GC-DISC-FLOOR
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor): raise PermissionError("only a manager may transfer")  # GC-TRANSFER-MGR
        target = self._users.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep": raise ValueError("new owner must be a rep: %r" % (new_owner,))  # GC-TRANSFER-ROLE
        if opp["stage"] in FINAL_STAGES: raise ValueError("opportunity %r is final" % (opp_id,))  # GC-TRANSFER-FINAL
        if new_owner == opp["owner"]: raise ValueError("opportunity already owned by %r" % (new_owner,))  # GC-TRANSFER-SAME
        if self.load(new_owner) >= target["capacity"]: raise ValueError("rep %r is at capacity" % (new_owner,))  # GC-TRANSFER-CAP

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    # -- reporting ---------------------------------------------------------
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
