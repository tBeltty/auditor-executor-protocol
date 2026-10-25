"""In-memory CRM implementing the contract in /tmp/aep-lab/specs/crm.md."""


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead email, existing lead %s" % (existing_id,))
        self.existing_id = existing_id


FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
SOURCE_BONUS = 15
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
VALID_STAGES = STAGE_ORDER + ("lost",)
BIG_DEAL_AMOUNT = 50000
REP_DISCOUNT_LIMIT = 10
MAX_DISCOUNT = 30


def normalize_email(email):
    return email.strip().lower()


def email_is_valid(normalized):
    parts = normalized.split("@")
    if len(parts) != 2 or parts[0] == "":
        return False
    domain = parts[1]
    # Spec-literal: the domain must contain a "." that is neither its first
    # nor its last character.  A leading dot is allowed as long as some other
    # dot sits inside the domain (".example.com" qualifies).
    for index, char in enumerate(domain):
        if char == "." and index != 0 and index != len(domain) - 1:
            return True
    return False


def name_is_valid(name):
    return isinstance(name, str) and name.strip() != ""


def source_is_valid(source):
    return isinstance(source, str) and source in SOURCE_SCORES


class CRM:
    def __init__(self, reps):
        self.users = {}
        self.rep_ids = []
        for rep in reps:
            entry = dict(rep)
            self.users[entry["id"]] = entry
            if entry["role"] == "rep":
                self.rep_ids.append(entry["id"])
        self.rep_ids.sort()
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ utils
    def _require_actor(self, actor):
        # An actor that is not a string is not the id of a known user; the
        # spec requires PermissionError (not TypeError) for any such actor.
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _may_manage(self, opp, actor):
        return actor == opp["owner"] or self._is_manager(actor)

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _choose_owner(self):
        best_id = None
        best_load = None
        for rep_id in self.rep_ids:
            rep = self.users[rep_id]
            if self._load(rep_id) >= rep["capacity"]:
                continue
            load = self._load(rep_id)
            if best_id is None or load < best_load:
                best_id = rep_id
                best_load = load
        return best_id

    def _free_slot(self, rep_id):
        if rep_id is None or rep_id not in self.users:
            return
        capacity = self.users[rep_id]["capacity"]
        while self.waiting and self._load(rep_id) < capacity:
            lead_id = self.waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------ leads
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = normalize_email(email)
        if not email_is_valid(normalized):
            raise ValueError("invalid email: %r" % (email,))
        if not name_is_valid(name):
            raise ValueError("name must be a non-empty string")
        if not source_is_valid(source):
            raise ValueError("invalid source: %r" % (source,))
        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])
        domain = normalized.split("@")[-1]
        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += SOURCE_BONUS
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        owner = self._choose_owner()
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
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead status is %r" % (lead["status"],))
        if lead["score"] < 30:
            raise ValueError("lead score %d is below the qualification threshold" % lead["score"])
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead status is %r" % (lead["status"],))
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

    # ---------------------------------------------------------- opportunities
    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if not self._may_manage(opp, actor):
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already %r" % (opp["stage"],))
        if stage != "lost":
            current_index = STAGE_ORDER.index(opp["stage"])
            if current_index + 1 >= len(STAGE_ORDER):
                raise ValueError("no stage follows %r" % (opp["stage"],))
            if stage != STAGE_ORDER[current_index + 1]:
                raise ValueError("illegal transition %r -> %r" % (opp["stage"], stage))
        if (
            stage == "negotiation"
            and opp["amount"] > BIG_DEAL_AMOUNT
            and not self._is_manager(actor)
        ):
            raise PermissionError("deals above 50000 need a manager to reach negotiation")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int):
            raise ValueError("pct must be an int")
        if pct < 1 or pct > MAX_DISCOUNT:
            raise ValueError("pct must be between 1 and %d" % MAX_DISCOUNT)
        if not self._may_manage(opp, actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already %r" % (opp["stage"],))
        if pct > REP_DISCOUNT_LIMIT and not self._is_manager(actor):
            raise PermissionError("reps may discount at most %d percent" % REP_DISCOUNT_LIMIT)
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * (100 - MAX_DISCOUNT):
            raise ValueError("cumulative discount would exceed %d percent" % MAX_DISCOUNT)
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer an opportunity")
        if (
            not isinstance(new_owner, str)
            or new_owner not in self.users
            or self.users[new_owner]["role"] != "rep"
        ):
            raise ValueError("new owner must be a rep: %r" % (new_owner,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already %r" % (opp["stage"],))
        if new_owner == opp["owner"]:
            raise ValueError("new owner is the current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    # ---------------------------------------------------------------- reports
    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}
        for opp in self.opps.values():
            if opp["stage"] == "won":
                won += opp["amount"]
            elif opp["stage"] in FINAL_STAGES:
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * weights[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
