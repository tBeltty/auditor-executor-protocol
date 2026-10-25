"""In-memory CRM: leads, opportunities, assignment, permissions, forecasting."""

SOURCES = ("web", "referral", "event")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
WEBMAIL_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = frozenset({"won", "lost"})
OPEN_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead email is already present."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


def email_ok(email, norm):
    if not isinstance(email, str) or norm is None:
        return False
    parts = norm.split("@")
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local:
        return False
    return any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == ".")


def normalize_email(email):
    if not isinstance(email, str):
        norm = None
    else:
        norm = email.strip().lower()
    if not email_ok(email, norm):
        raise ValueError("invalid email: %r" % (email,))
    return norm


def name_ok(name):
    return isinstance(name, str) and name.strip() != ""


def source_ok(source):
    return isinstance(source, str) and source in SOURCES


def duplicate_of(leads, norm):
    for lead in leads.values():
        if lead["email"] == norm:
            return lead["id"]
    return None


def may_act(user, owner_id):
    return user["role"] == "manager" or user["id"] == owner_id


def score_ok(score):
    return score >= 30


def stage_name_ok(stage):
    return isinstance(stage, str) and stage in STAGE_ORDER + ("lost",)


def transition_ok(current, new):
    if new == "lost":
        return True
    index = STAGE_ORDER.index(current)
    return index + 1 < len(STAGE_ORDER) and STAGE_ORDER[index + 1] == new


def big_deal_needs_manager(stage, amount, user):
    return stage == "negotiation" and amount > 50000 and user["role"] != "manager"


def discount_pct_ok(pct):
    return isinstance(pct, int) and not isinstance(pct, bool) and 1 <= pct <= 30


def non_manager_pct_ok(user, pct):
    return user["role"] == "manager" or pct <= 10


def floor_ok(new_amount, original_amount):
    return new_amount * 100 >= original_amount * 70


def pick_owner(reps, load_of):
    best = None
    best_key = None
    for rep in reps:
        load = load_of(rep["id"])
        if load < rep["capacity"]:
            key = (load, rep["id"])
            if best_key is None or key < best_key:
                best = rep["id"]
                best_key = key
    return best


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
        self.waiting = []
        self._lead_count = 0
        self._opp_count = 0

    # -- internals -------------------------------------------------------
    def _require_user(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))
        return self.users[actor]

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
        reps = [user for user in self.users.values() if user["role"] == "rep"]
        return pick_owner(reps, self._load)

    def _assign_waiting(self, rep_id):
        while self.waiting and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _get_opp(self, opp_id):
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return opp

    def _get_lead(self, lead_id):
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return lead

    # -- leads -----------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_user(actor)
        norm = normalize_email(email)
        if not name_ok(name):
            raise ValueError("name must be a non-empty string")
        if not source_ok(source):
            raise ValueError("invalid source: %r" % (source,))
        existing = duplicate_of(self.leads, norm)
        if existing is not None:
            raise DuplicateLeadError(existing)
        lead_id = "L%d" % (self._lead_count + 1)
        domain = norm.rsplit("@", 1)[1]
        score = SOURCE_SCORES[source]
        if domain not in WEBMAIL_DOMAINS:
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
        self._lead_count += 1
        self.leads[lead_id] = lead
        if owner is None:
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        user = self._require_user(actor)
        lead = self._get_lead(lead_id)
        if not may_act(user, lead["owner"]):
            raise PermissionError("not allowed to qualify %r" % (lead_id,))
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if not score_ok(lead["score"]):
            raise ValueError("lead score is below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        user = self._require_user(actor)
        lead = self._get_lead(lead_id)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not may_act(user, lead["owner"]):
            raise PermissionError("not allowed to convert %r" % (lead_id,))
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        opp_id = "O%d" % (self._opp_count + 1)
        opp = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        self._opp_count += 1
        lead["status"] = "converted"
        self.opps[opp_id] = opp
        self.log.append(("convert", opp_id, actor))
        return opp_id

    # -- opportunities ---------------------------------------------------
    def advance(self, opp_id, stage, actor):
        user = self._require_user(actor)
        opp = self._get_opp(opp_id)
        if not stage_name_ok(stage):
            raise ValueError("invalid stage: %r" % (stage,))
        if not may_act(user, opp["owner"]):
            raise PermissionError("not allowed to advance %r" % (opp_id,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not transition_ok(opp["stage"], stage):
            raise ValueError("illegal transition %s -> %s" % (opp["stage"], stage))
        if big_deal_needs_manager(stage, opp["amount"], user):
            raise PermissionError("deals above 50000 need manager approval")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        user = self._require_user(actor)
        opp = self._get_opp(opp_id)
        if not discount_pct_ok(pct):
            raise ValueError("pct must be an int between 1 and 30")
        if not may_act(user, opp["owner"]):
            raise PermissionError("not allowed to discount %r" % (opp_id,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not non_manager_pct_ok(user, pct):
            raise PermissionError("non-managers may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if not floor_ok(new_amount, opp["original_amount"]):
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        user = self._require_user(actor)
        opp = self._get_opp(opp_id)
        if user["role"] != "manager":
            raise PermissionError("only managers may transfer")
        target = self.users.get(new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner must differ from current owner")
        if self._load(new_owner) >= target["capacity"]:
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
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * OPEN_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
