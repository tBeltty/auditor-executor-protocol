"""CRM module implementing the leads/opportunities pipeline described in crm.md."""

from collections import deque

FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCES = ("web", "referral", "event")
SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
ORDER = ("prospect", "proposal", "negotiation", "won")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self._users = {r["id"]: r for r in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = deque()          # FIFO of lead ids without an owner
        self._by_email = {}              # normalized email -> lead id
        self._loads = {user_id: 0 for user_id in self._users}
        self._lead_seq = 0
        self._opp_seq = 0

    # -- helpers ---------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError(actor)

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _lead(self, lead_id):
        # Unhashable / non-string ids are simply "unknown" rather than TypeError.
        return self.leads.get(lead_id) if isinstance(lead_id, str) else None

    def _opp(self, opp_id):
        return self.opps.get(opp_id) if isinstance(opp_id, str) else None

    def _load(self, rep_id):
        return self._loads.get(rep_id, 0)

    def _can_own(self, rep_id):
        user = self._users[rep_id]
        return user["role"] == "rep" and self._load(rep_id) < user["capacity"]

    def _pick_owner(self):
        best = None
        best_load = None
        for rep_id in sorted(self._users):
            if not self._can_own(rep_id):
                continue
            load = self._load(rep_id)
            if best is None or load < best_load:
                best, best_load = rep_id, load
        return best

    def _drain(self, rep_id):
        while self._can_own(rep_id) and self._waiting:
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self._loads[rep_id] += 1
            self.log.append(("assign", lead_id, "system"))

    # -- public API ------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a local part")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("email domain is invalid")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in SOURCES:
            raise ValueError("invalid source")
        existing = self._by_email.get(normalized)
        if existing is not None:
            raise DuplicateLeadError(existing)

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SOURCE_SCORE[source]
        if domain not in FREE_DOMAINS:
            score += 15

        owner = self._pick_owner()
        if owner is None:
            self._waiting.append(lead_id)
        else:
            self._loads[owner] += 1

        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self._by_email[normalized] = lead_id
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self._lead(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if not self._is_manager(actor) and lead["owner"] != actor:
            raise PermissionError(actor)
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        # "new" and "qualified" both count towards load, so the load is unchanged.
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._lead(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._is_manager(actor) and lead["owner"] != actor:
            raise PermissionError(actor)
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
        # The lead leaves the open-lead count while the new prospect enters the
        # open-opportunity count for the same owner: the load does not change.
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
        opp = self._opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if stage not in STAGES:
            raise ValueError("invalid stage")
        if not self._is_manager(actor) and opp["owner"] != actor:
            raise PermissionError(actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost" and stage != ORDER[ORDER.index(opp["stage"]) + 1]:
            raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for large negotiation")

        opp["stage"] = stage
        if stage in FINAL_STAGES:
            self._loads[opp["owner"]] -= 1
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._drain(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if not self._is_manager(actor) and opp["owner"] != actor:
            raise PermissionError(actor)
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
        self._require_actor(actor)
        opp = self._opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if not isinstance(new_owner, str) or new_owner not in self._users or self._users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned by new_owner")
        if not self._can_own(new_owner):
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self._loads[previous] -= 1
        self._loads[new_owner] += 1
        self.log.append(("transfer", opp_id, actor))
        self._drain(previous)

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
                weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
