"""CRM module per spec /tmp/aep-lab/specs/crm.md."""

FINAL_STAGES = ("won", "lost")
STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
VALID_SOURCES = ("web", "referral", "event")
SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
FREE_MAIL_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})
STAGE_WEIGHT = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when adding a lead whose normalized email already exists."""

    def __init__(self, existing_id=None):
        self.existing_id = existing_id
        super().__init__(
            "duplicate lead; existing_id={!r}".format(existing_id)
        )


class CRM:
    def __init__(self, reps):
        # id -> {"id", "role", "capacity"}; only role "rep" users can own work.
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}   # lead id -> lead dict
        self.opps = {}    # opportunity id -> opportunity dict
        self.log = []     # list of (op, entity_id, actor_id)
        self._waiting = []  # FIFO list of lead ids waiting for an owner
        self._lead_seq = 0  # counts successful lead creations
        self._opp_seq = 0   # counts successful conversions

    # ------------------------------------------------------------------ helpers

    def _require_actor(self, actor):
        """Unknown actor -> PermissionError. Checked first in every method."""
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown actor: {!r}".format(actor))
        return self._users[actor]

    def _is_manager(self, actor_id):
        return self._users[actor_id]["role"] == "manager"

    def _load(self, rep_id):
        """Leads owned with status new/qualified + open opportunities owned."""
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _owner_for_new_lead(self):
        """Lowest-load rep below capacity; ties: smallest id in string order."""
        candidates = []
        for uid, user in self._users.items():
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load < user["capacity"]:
                candidates.append((load, uid))
        if not candidates:
            return None
        return min(candidates)[1]

    def _free_slot(self, rep_id):
        """Assign oldest waiting leads while this rep is below capacity."""
        capacity = self._users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _validate_email(email):
        """Return (normalized_email, domain) or raise ValueError."""
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty part before '@'")
        if not any(
            i != 0 and i != len(domain) - 1
            for i, ch in enumerate(domain)
            if ch == "."
        ):
            raise ValueError(
                "email domain must contain a '.' that is neither its first "
                "nor its last character"
            )
        return normalized, domain

    # ------------------------------------------------------------------ API

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        normalized, domain = self._validate_email(email)  # check 1

        if not isinstance(name, str) or not name.strip():  # check 2
            raise ValueError("name must be a non-empty str")

        if source not in VALID_SOURCES:  # check 3
            raise ValueError("source must be 'web', 'referral' or 'event'")

        for existing in self.leads.values():  # check 4
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])

        score = SOURCE_SCORE[source]  # check 5
        if domain not in FREE_MAIL_DOMAINS:
            score += 15

        owner = self._owner_for_new_lead()  # check 6

        self._lead_seq += 1
        lead_id = "L{}".format(self._lead_seq)
        lead = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lead_id] = lead  # check 7
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        actor_user = self._require_actor(actor)

        lead = self.leads.get(lead_id)
        if lead is None:  # check 1
            raise ValueError("no such lead: {!r}".format(lead_id))
        if actor != lead["owner"] and not self._is_manager(actor):  # check 2
            raise PermissionError("actor must be the lead's owner or a manager")
        if lead["status"] != "new":  # check 3
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:  # check 4
            raise ValueError("lead score must be at least 30")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = self.leads.get(lead_id)
        if lead is None:  # check 1
            raise ValueError("no such lead: {!r}".format(lead_id))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")  # check 2
        if actor != lead["owner"] and not self._is_manager(actor):  # check 3
            raise PermissionError("actor must be the lead's owner or a manager")
        if lead["status"] != "qualified":  # check 4
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:  # check 5
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O{}".format(self._opp_seq)
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

        opp = self.opps.get(opp_id)
        if opp is None:  # check 1
            raise ValueError("no such opportunity: {!r}".format(opp_id))
        if stage not in ALL_STAGES:  # check 2
            raise ValueError("invalid stage: {!r}".format(stage))
        if actor != opp["owner"] and not self._is_manager(actor):  # check 3
            raise PermissionError(
                "actor must be the opportunity's owner or a manager"
            )
        if opp["stage"] in FINAL_STAGES:  # check 4
            raise ValueError("opportunity is in a final stage")
        current_index = STAGE_ORDER.index(opp["stage"])
        expected_next = STAGE_ORDER[current_index + 1]
        if stage != "lost" and stage != expected_next:  # check 5
            raise ValueError(
                "cannot advance from {!r} to {!r}".format(opp["stage"], stage)
            )
        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):  # check 6
            raise PermissionError(
                "moving to negotiation with amount > 50000 requires a manager"
            )

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:  # check 1
            raise ValueError("no such opportunity: {!r}".format(opp_id))
        if (
            not isinstance(pct, int)
            or isinstance(pct, bool)
            or pct < 1
            or pct > 30
        ):  # check 2
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):  # check 3
            raise PermissionError(
                "actor must be the opportunity's owner or a manager"
            )
        if opp["stage"] in FINAL_STAGES:  # check 4
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:  # check 5
            raise PermissionError("a non-manager may use at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:  # check 6
            raise ValueError("cumulative discount would exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:  # check 1
            raise ValueError("no such opportunity: {!r}".format(opp_id))
        if not self._is_manager(actor):  # check 2
            raise PermissionError("actor must be a manager")
        target = self._users.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":  # check 3
            raise ValueError("new_owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:  # check 4
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:  # check 5
            raise ValueError("new_owner must differ from the current owner")
        if not (self._load(new_owner) < self._users[new_owner]["capacity"]):  # check 6
            raise ValueError("new_owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage not in FINAL_STAGES:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHT[stage] // 100
            elif stage == "won":
                won += opp["amount"]
        return {"open": open_count, "weighted": weighted, "won": won}
