"""Small CRM domain module.

Implements ``CRM`` and ``DuplicateLeadError`` exactly as described by the
module specification.
"""

FREEMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = {"won", "lost"}
VALID_STAGES = {"prospect", "proposal", "negotiation", "won", "lost"}

STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead email: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    """A tiny lead/opportunity pipeline."""

    def __init__(self, reps):
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO queue of unowned lead ids
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        """Raise PermissionError unless ``actor`` is a known user id."""
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str):
            return None
        return self.leads.get(lead_id)

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str):
            return None
        return self.opps.get(opp_id)

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        """Number of active leads plus open opportunities owned by a rep."""
        if rep_id is None:
            return 0
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        """Rep with the lowest load below capacity; ties by smallest id."""
        best = None
        best_key = None
        for user in self._users.values():
            if user["role"] != "rep":
                continue
            load = self._load(user["id"])
            if load >= user["capacity"]:
                continue
            key = (load, user["id"])
            if best_key is None or key < best_key:
                best = user["id"]
                best_key = key
        return best

    def _release_slot(self, rep_id):
        """Assign waiting leads to ``rep_id`` while it has spare capacity."""
        if rep_id is None or rep_id not in self._users:
            return
        capacity = self._users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, _, domain = normalized.partition("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not domain:
            raise ValueError("email must have a domain")
        if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
            raise ValueError("email domain must contain an inner '.'")
        return normalized

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = self._normalize_email(email)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_count += 1
        lead_id = "L%d" % self._lead_count

        domain = normalized.partition("@")[2]
        score = SOURCE_SCORES[source]
        if domain not in FREEMAIL_DOMAINS:
            score += 15

        owner = self._pick_owner()
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
        self._require_actor(actor)

        lead = self._get_lead(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))

        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")

        if lead["status"] != "new":
            raise ValueError("lead is not new")

        if lead["score"] < 30:
            raise ValueError("lead score is too low")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = self._get_lead(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))

        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")

        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not convert this lead")

        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")

        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_count += 1
        opp_id = "O%d" % self._opp_count
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

        opp = self._get_opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))

        if not isinstance(stage, str) or stage not in VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))

        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not advance this opportunity")

        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if stage != "lost":
            index = STAGE_ORDER.index(current)
            if index + 1 >= len(STAGE_ORDER) or STAGE_ORDER[index + 1] != stage:
                raise ValueError("invalid stage transition")

        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError("large negotiations require a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))

        if stage in FINAL_STAGES:
            self._release_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self._get_opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))

        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")

        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not discount this opportunity")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("only managers may discount above 10")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = self._get_opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))

        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")

        if (
            not isinstance(new_owner, str)
            or new_owner not in self._users
            or self._users[new_owner]["role"] != "rep"
        ):
            raise ValueError("new_owner must be a rep id")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if new_owner == opp["owner"]:
            raise ValueError("opportunity already owned by new_owner")

        if self._load(new_owner) >= self._users[new_owner]["capacity"]:
            raise ValueError("new_owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._release_slot(previous_owner)

    def forecast(self):
        open_opps = [
            opp for opp in self.opps.values() if opp["stage"] not in FINAL_STAGES
        ]
        weighted = sum(
            opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100 for opp in open_opps
        )
        won = sum(
            opp["amount"]
            for opp in self.opps.values()
            if opp["stage"] == "won"
        )
        return {"open": len(open_opps), "weighted": weighted, "won": won}
