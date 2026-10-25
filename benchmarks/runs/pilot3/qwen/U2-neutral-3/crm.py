"""crm.py — CRM with capacity-based lead routing (specs/crm.md).

Public surface: ``CRM`` and ``DuplicateLeadError``.  ``CRM.leads``,
``CRM.opps`` and ``CRM.log`` are the attributes named by the spec; user
records and the waiting queue are internal state.

Two spec sentences are easy to misread, so the intended reading is pinned
here and in the tests:

* "a domain ... that contains a '.' which is neither the first nor the last
  character of the domain" is *existential*: the domain is acceptable as soon
  as at least one dot sits in its interior.  ".leading-dot.com" therefore
  validates (the dot before "com" is interior), while ".", ".b" and "b." do
  not (their only dots are boundary dots).
* "A failed call (any exception) changes nothing and appends nothing to
  log" means every ID counter is bumped only after the last check that can
  fail, so a rejected call never consumes an ID.
"""

from collections import deque

NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation",
              "negotiation": "won"}
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
ACTIVE_LEAD_STATUSES = ("new", "qualified")
STAGE_WEIGHT = {"prospect": 10, "proposal": 30, "negotiation": 60}
SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
VALID_SOURCES = ("web", "referral", "event")


class DuplicateLeadError(Exception):
    """Raised when adding a lead whose normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__(f"duplicate lead for email, existing id {existing_id}")
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.leads = {}
        self.opps = {}
        self.log = []
        self._users = {}
        self._waiting = deque()       # FIFO of lead ids with no owner
        self._lead_count = 0
        self._opp_count = 0
        for user in reps:
            # Copy so later mutation of the caller's dicts cannot change the
            # CRM's routing rules mid-session.
            self._users[user["id"]] = dict(user)

    # ------------------------------------------------------------------ core

    def _check_actor(self, actor):
        # Every method starts here: an unknown actor is never even told
        # whether its arguments were valid.
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError(f"unknown actor {actor!r}")

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _lookup(self, store, kind, entity_id):
        """Return the entity or raise ValueError; never TypeError on a bad id.

        Keys are always strings, so a non-str id cannot exist.  Checking the
        type first keeps "the lead/opportunity must exist (ValueError)" true
        for unhashable ids such as ``["L1"]``.
        """
        entity = store.get(entity_id) if isinstance(entity_id, str) else None
        if entity is None:
            raise ValueError(f"unknown {kind} {entity_id!r}")
        return entity

    def _load(self, rep_id):
        """Leads (new/qualified) plus open opportunities owned by ``rep_id``."""
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ACTIVE_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _loads(self):
        """Load of every rep in one pass (routing needs all of them at once)."""
        loads = {uid: 0 for uid, user in self._users.items()
                 if user["role"] == "rep"}
        for lead in self.leads.values():
            if lead["status"] in ACTIVE_LEAD_STATUSES and lead["owner"] in loads:
                loads[lead["owner"]] += 1
        for opp in self.opps.values():
            if opp["stage"] not in FINAL_STAGES and opp["owner"] in loads:
                loads[opp["owner"]] += 1
        return loads

    def _pick_owner(self):
        """Lowest-load rep below capacity; ties broken by smallest id string."""
        best = None
        best_key = None
        for uid, load in self._loads().items():
            if load >= self._users[uid]["capacity"]:
                continue
            key = (load, uid)
            if best_key is None or key < best_key:
                best, best_key = uid, key
        return best

    def _fill_slot(self, rep_id):
        """Assign oldest waiting leads while the rep is below capacity."""
        capacity = self._users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _valid_email(email):
        """True for a normalized email satisfying the spec's three clauses."""
        if email.count("@") != 1:
            return False
        local, domain = email.split("@", 1)
        return bool(local) and "." in domain[1:-1]

    # ------------------------------------------------------------------- API

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if not self._valid_email(norm):
            raise ValueError(f"invalid email {email!r}")
        domain = norm.split("@", 1)[1]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in VALID_SOURCES:
            raise ValueError(f"invalid source {source!r}")
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])
        # Past the last failure point: safe to consume an id.
        self._lead_count += 1
        lead_id = f"L{self._lead_count}"
        score = SOURCE_SCORE[source]
        if domain not in FREE_DOMAINS:
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
        self._check_actor(actor)
        lead = self._lookup(self.leads, "lead", lead_id)
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor must be the lead owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self._lookup(self.leads, "lead", lead_id)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor must be the lead owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead must be qualified to convert")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_count += 1
        opp_id = f"O{self._opp_count}"
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
        opp = self._lookup(self.opps, "opportunity", opp_id)
        if stage not in STAGES:
            raise ValueError(f"invalid stage {stage!r}")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor must be the opp owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        if stage != "lost" and NEXT_STAGE[opp["stage"]] != stage:
            raise ValueError("illegal stage transition")
        if (stage == "negotiation" and opp["amount"] > 50000
                and not self._is_manager(actor)):
            raise PermissionError(
                "moving to negotiation with amount > 50000 requires a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._fill_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self._lookup(self.opps, "opportunity", opp_id)
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError(f"pct must be an int from 1 to 30, got {pct!r}")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor must be the opp owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        # Cumulative discount may never take the deal below 70% of the
        # original amount; the floor is checked on the already-floored value.
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self._lookup(self.opps, "opportunity", opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        user = self._users.get(new_owner) if isinstance(new_owner, str) else None
        if user is None or user["role"] != "rep":
            raise ValueError(f"new_owner must be a known rep, got {new_owner!r}")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is already the owner")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new_owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        # Spec requires freeing the previous owner's slot here.  Note that
        # with capacities fixed at construction this can never assign: a
        # non-empty queue implies every rep is at capacity, which would have
        # failed check 6 above.  Kept because the spec demands it, and it is
        # covered white-box in test_crm_flow.
        self._fill_slot(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHT[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
