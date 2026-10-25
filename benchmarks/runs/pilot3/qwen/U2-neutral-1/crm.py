"""CRM module per spec /tmp/aep-lab/specs/crm.md (stdlib only)."""

from collections import deque

VALID_SOURCES = ("web", "referral", "event")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
CONSUMER_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")

STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
# The only legal forward moves; "lost" is reachable from any non-final stage.
NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
FINAL_STAGES = ("won", "lost")
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


def _normalize_email(email):
    """Return the normalized email or None if invalid per spec rule 1."""
    if not isinstance(email, str):
        return None
    norm = email.strip().lower()
    if norm.count("@") != 1:
        return None
    local, domain = norm.split("@")
    if not local:
        return None
    if "." not in domain:
        return None
    # The domain must contain a "." that is neither its first nor last char.
    if not any(i not in (0, len(domain) - 1) for i, ch in enumerate(domain) if ch == "."):
        return None
    return norm


class CRM:
    def __init__(self, reps):
        # reps: list of {"id": str, "role": "rep"|"manager", "capacity": int}
        self._users = {r["id"]: {"role": r["role"], "capacity": r["capacity"]} for r in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_seq = 0
        self._opp_seq = 0
        self._queue = deque()  # FIFO of lead ids waiting for an owner

    # ---- helpers -------------------------------------------------------

    def _check_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

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
        """Lowest-load rep under capacity; ties broken by smallest id (string order)."""
        best = None
        for uid, user in self._users.items():
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load < user["capacity"] and (best is None or (load, uid) < best):
                best = (load, uid)
        return best[1] if best else None

    def _fill_waiting(self, rep_id):
        """Assign oldest waiting leads while rep's load is below capacity."""
        user = self._users.get(rep_id)
        if user is None or user["role"] != "rep":
            return
        while self._queue and self._load(rep_id) < user["capacity"]:
            lead_id = self._queue.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ---- API -----------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        norm = _normalize_email(email)
        if norm is None:
            raise ValueError("invalid email: %r" % (email,))

        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name: %r" % (name,))

        if source not in VALID_SOURCES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])

        domain = norm.split("@", 1)[1]
        score = SOURCE_SCORES[source]
        if domain not in CONSUMER_DOMAINS:
            score += 15

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
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
        if owner is None:
            self._queue.append(lead_id)
        self.leads[lead_id] = lead
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)

        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))

        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("actor may not qualify this lead")

        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")

        if lead["score"] < 30:
            raise ValueError("lead score too low to qualify")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)

        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))

        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")

        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("actor may not convert this lead")

        if lead["status"] != "qualified":
            raise ValueError("lead must be qualified")

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

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))

        if stage not in STAGES:
            raise ValueError("invalid stage: %r" % (stage,))

        if not (actor == opp["owner"] or self._is_manager(actor)):
            raise PermissionError("actor may not advance this opportunity")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")

        if stage != "lost" and stage != NEXT_STAGE[opp["stage"]]:
            raise ValueError("invalid stage transition")

        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager approval required for large negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))

        if stage in FINAL_STAGES:
            self._fill_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))

        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")

        if not (actor == opp["owner"] or self._is_manager(actor)):
            raise PermissionError("actor may not discount this opportunity")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")

        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("rep may discount at most 10 percent")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))

        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")

        target = self._users.get(new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a known rep")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")

        if new_owner == opp["owner"]:
            raise ValueError("new owner must differ from current owner")

        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))

        self._fill_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in FINAL_STAGES:
                if stage == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
