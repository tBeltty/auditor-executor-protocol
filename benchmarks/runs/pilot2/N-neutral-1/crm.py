"""A tiny in-memory CRM.

Implements the contract in specs/crm.md: lead intake with duplicate detection and
round-robin assignment, qualification, conversion, stage advancement with a
waiting queue, discounts with a cumulative floor, transfers, and forecasting.

Guard lines carry ``# @g:<tag>`` markers. They are inert comments; the negative
control helper uses them to disable exactly one guard at a time.
"""

FREEMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCES = ("web", "referral", "event")
STAGE_SEQUENCE = ("prospect", "proposal", "negotiation", "won")
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
QUALIFY_THRESHOLD = 30
BIG_DEAL_AMOUNT = 50000
MAX_REP_DISCOUNT = 10
MAX_DISCOUNT = 30
CUMULATIVE_FLOOR = 70


class DuplicateLeadError(Exception):
    """A lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead email, existing id %s" % (existing_id,))
        self.existing_id = existing_id


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
        self._lead_counter = 0
        self._opp_counter = 0

    # ------------------------------------------------------------------ helpers

    def _check_actor(self, actor):
        if actor not in self.users:  # @g:actor_known
            raise PermissionError("unknown actor: %r" % (actor,))
        return self.users[actor]

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _may(self, owner_id, actor):
        """True when actor is the owner or any manager."""
        if actor == owner_id:  # @g:perm_owner
            return True
        return self.users[actor]["role"] == "manager"  # @g:perm_manager

    def _load(self, user_id):
        count = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                count += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                count += 1
        return count

    def _pick_rep(self):
        """Lowest-load rep below capacity; ties broken by smallest id string."""
        best = None
        for user_id in sorted(self.users):
            user = self.users[user_id]
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load < user["capacity"]:  # @g:assign_capacity
                if best is None or load < best[0]:  # @g:assign_tie
                    best = (load, user_id)
        return None if best is None else best[1]

    def _drain(self, owner_id):
        """Hand FIFO waiting leads to owner_id while it has free capacity."""
        while True:
            capacity = self.users[owner_id]["capacity"]
            if self._load(owner_id) >= capacity:  # @g:drain_capacity
                break
            if not self.waiting:  # @g:drain_empty
                break
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = owner_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _next_stage(stage):
        index = STAGE_SEQUENCE.index(stage)
        if index + 1 >= len(STAGE_SEQUENCE):
            return None
        return STAGE_SEQUENCE[index + 1]

    @staticmethod
    def _validate_email(email):
        if not isinstance(email, str):  # @g:email_str
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:  # @g:email_at
            raise ValueError("email must contain exactly one @")
        local_part, _, domain = normalized.partition("@")
        if local_part == "":  # @g:email_local
            raise ValueError("email must have a non-empty local part")
        if "." not in domain[1:-1]:  # @g:email_dot
            raise ValueError("email domain must contain an inner dot")
        return normalized, domain

    # ------------------------------------------------------------------- intake

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized, domain = self._validate_email(email)
        if not isinstance(name, str) or not name.strip():  # @g:name_str
            raise ValueError("name must be a non-empty str")
        if source not in SOURCES:  # @g:source_valid
            raise ValueError("unknown source: %r" % (source,))
        for existing in self.leads.values():
            if existing["email"] == normalized:  # @g:dup
                raise DuplicateLeadError(existing["id"])

        score = SOURCE_SCORES[source]
        if domain not in FREEMAIL_DOMAINS:  # @g:score_freemail
            score += 15

        owner = self._pick_rep()

        self._lead_counter += 1
        lead_id = "L%d" % self._lead_counter
        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        if owner is None:  # @g:queue_push
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:  # @g:qualify_exists
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not self._may(lead["owner"], actor):  # @g:qualify_perm
            raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
        if lead["status"] != "new":  # @g:qualify_status
            raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
        if lead["score"] < QUALIFY_THRESHOLD:  # @g:qualify_score
            raise ValueError("lead %s scores %d" % (lead_id, lead["score"]))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:  # @g:convert_exists
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:  # @g:convert_amount
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if not self._may(lead["owner"], actor):  # @g:convert_perm
            raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
        if lead["status"] != "qualified":  # @g:convert_status
            raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
        if lead["owner"] is None:  # @g:convert_owner
            raise ValueError("lead %s has no owner" % (lead_id,))

        self._opp_counter += 1
        opp_id = "O%d" % self._opp_counter
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
        if opp_id not in self.opps:  # @g:advance_exists
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if stage not in STAGES:  # @g:advance_stage_valid
            raise ValueError("unknown stage: %r" % (stage,))
        if not self._may(opp["owner"], actor):  # @g:advance_perm
            raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
        if opp["stage"] in FINAL_STAGES:  # @g:advance_final
            raise ValueError("opportunity %s is %s" % (opp_id, opp["stage"]))
        if stage != "lost" and stage != self._next_stage(opp["stage"]):  # @g:advance_order
            raise ValueError("cannot move %s from %s to %s" % (opp_id, opp["stage"], stage))
        if stage == "negotiation" and opp["amount"] > BIG_DEAL_AMOUNT and not self._is_manager(actor):  # @g:advance_bigdeal
            raise PermissionError("opportunity %s needs a manager to negotiate" % (opp_id,))
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._drain(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:  # @g:discount_exists
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= MAX_DISCOUNT):  # @g:discount_pct
            raise ValueError("pct must be an int between 1 and %d" % MAX_DISCOUNT)
        opp = self.opps[opp_id]
        if not self._may(opp["owner"], actor):  # @g:discount_perm
            raise PermissionError("actor %r may not discount %s" % (actor, opp_id))
        if opp["stage"] in FINAL_STAGES:  # @g:discount_final
            raise ValueError("opportunity %s is %s" % (opp_id, opp["stage"]))
        if pct > MAX_REP_DISCOUNT and not self._is_manager(actor):  # @g:discount_rep_limit
            raise PermissionError("only a manager may discount more than %d" % MAX_REP_DISCOUNT)
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * CUMULATIVE_FLOOR:  # @g:discount_floor
            raise ValueError("cumulative discount would exceed %d percent" % (100 - CUMULATIVE_FLOOR))
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:  # @g:transfer_exists
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if not self._is_manager(actor):  # @g:transfer_manager
            raise PermissionError("only a manager may transfer")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":  # @g:transfer_target
            raise ValueError("transfer target must be a known rep: %r" % (new_owner,))
        if opp["stage"] in FINAL_STAGES:  # @g:transfer_final
            raise ValueError("opportunity %s is %s" % (opp_id, opp["stage"]))
        if new_owner == opp["owner"]:  # @g:transfer_same
            raise ValueError("opportunity %s already belongs to %s" % (opp_id, new_owner))
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:  # @g:transfer_capacity
            raise ValueError("rep %s is at capacity" % (new_owner,))
        previous = opp["owner"]
        opp["owner"] = new_owner
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
                continue
            open_count += 1
            weighted += opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
