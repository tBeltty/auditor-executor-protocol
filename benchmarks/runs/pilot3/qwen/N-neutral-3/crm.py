"""crm.py — Capacity Routing Machine.

Implements the CRM contract exactly as specified in specs/crm.md.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

VALID_SOURCES = ("web", "referral", "event")
BASE_SCORE = {"web": 10, "referral": 30, "event": 20}
FREE_MAILBOX_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation",
              "negotiation": "won"}
FINAL_STAGES = ("won", "lost")
STAGE_WEIGHT = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id: str) -> None:
        super().__init__(f"duplicate lead: existing_id={existing_id}")
        self.existing_id = existing_id


def _normalize_email(email: str) -> str:
    """Normalize and validate an email string; ValueError if malformed."""
    if not isinstance(email, str):
        raise ValueError("email must be a str")
    norm = email.strip().lower()
    if norm.count("@") != 1:
        raise ValueError("email must contain exactly one '@'")
    local, domain = norm.split("@", 1)
    if not local:
        raise ValueError("email must have a non-empty part before '@'")
    if len(domain) < 3 or "." not in domain[1:-1]:
        raise ValueError("email domain must contain a '.' that is neither "
                         "the first nor the last character of the domain")
    return norm


class CRM:
    """CRM with capacity-based lead routing, as specified in specs/crm.md."""

    def __init__(self, reps: List[Dict[str, Any]]) -> None:
        self.leads: Dict[str, Dict[str, Any]] = {}
        self.opps: Dict[str, Dict[str, Any]] = {}
        self.log: List[tuple] = []
        self.users: Dict[str, Dict[str, Any]] = {}
        self.rep_ids: List[str] = []
        self.manager_ids: List[str] = []
        self._waiting: List[str] = []  # FIFO of lead ids with owner None
        self._lead_n = 0
        self._opp_n = 0
        for user in reps:
            uid = user["id"]
            self.users[uid] = user
            if user["role"] == "manager":
                self.manager_ids.append(uid)
            else:
                self.rep_ids.append(uid)

    # -- helpers -----------------------------------------------------------

    def _require_actor(self, actor: str) -> None:
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError(f"unknown actor {actor!r}")

    def _is_manager(self, actor: str) -> bool:
        return self.users.get(actor, {}).get("role") == "manager"

    def _load(self, rep_id: str) -> int:
        lead_count = sum(
            1
            for lead in self.leads.values()
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified")
        )
        open_count = sum(
            1
            for opp in self.opps.values()
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES
        )
        return lead_count + open_count

    def _pick_rep(self) -> Optional[str]:
        """Lowest-load rep below capacity; ties broken by smallest id string."""
        best: Optional[str] = None
        best_load = 0
        for rid in sorted(self.rep_ids):
            load = self._load(rid)
            if load < self.users[rid]["capacity"]:
                if best is None or load < best_load:
                    best, best_load = rid, load
        return best

    def _free_slots(self, rep_id: str) -> None:
        """Fill the waiting queue into a rep's freed capacity (FIFO)."""
        while (
            self._waiting
            and self._load(rep_id) < self.users[rep_id]["capacity"]
        ):
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- API ---------------------------------------------------------------

    def add_lead(self, email: str, name: str, source: str, actor: str) -> str:
        self._require_actor(actor)
        norm = _normalize_email(email)  # 1: str + shape checks -> ValueError
        if not isinstance(name, str) or not name.strip():  # 2
            raise ValueError("name must be a non-empty str")
        if source not in VALID_SOURCES:  # 3
            raise ValueError(f"invalid source {source!r}")
        for lead in self.leads.values():  # 4
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])
        self._lead_n += 1  # 5
        lead_id = f"L{self._lead_n}"
        domain = norm.split("@", 1)[1]
        score = BASE_SCORE[source] + (0 if domain in FREE_MAILBOX_DOMAINS else 15)
        owner = self._pick_rep()  # 6
        lead = {  # 7
            "id": lead_id,
            "email": norm,
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

    def qualify(self, lead_id: str, actor: str) -> None:
        self._require_actor(actor)
        if lead_id not in self.leads:  # 1
            raise ValueError(f"no such lead {lead_id!r}")
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):  # 2
            raise PermissionError("actor must be the lead's owner or a manager")
        if lead["status"] != "new":  # 3
            raise ValueError("lead is not new")
        if lead["score"] < 30:  # 4
            raise ValueError("lead score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id: str, amount: int, actor: str) -> str:
        self._require_actor(actor)
        if lead_id not in self.leads:  # 1
            raise ValueError(f"no such lead {lead_id!r}")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")  # 2
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):  # 3
            raise PermissionError("actor must be the lead's owner or a manager")
        if lead["status"] != "qualified":  # 4
            raise ValueError("lead must be qualified to convert")
        if lead["owner"] is None:  # 5
            raise ValueError("lead has no owner")
        self._opp_n += 1
        opp_id = f"O{self._opp_n}"
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

    def advance(self, opp_id: str, stage: str, actor: str) -> None:
        self._require_actor(actor)
        if opp_id not in self.opps:  # 1
            raise ValueError(f"no such opportunity {opp_id!r}")
        if stage not in STAGES:  # 2
            raise ValueError(f"invalid stage {stage!r}")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):  # 3
            raise PermissionError("actor must be the opp's owner or a manager")
        if opp["stage"] in FINAL_STAGES:  # 4
            raise ValueError("opportunity is already in a final stage")
        if stage != "lost" and NEXT_STAGE.get(opp["stage"]) != stage:  # 5
            raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000:  # 6
            if not self._is_manager(actor):
                raise PermissionError(
                    "manager approval required for negotiation over 50000"
                )
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slots(opp["owner"])

    def discount(self, opp_id: str, pct: int, actor: str) -> None:
        self._require_actor(actor)
        if opp_id not in self.opps:  # 1
            raise ValueError(f"no such opportunity {opp_id!r}")
        if (
            isinstance(pct, bool)
            or not isinstance(pct, int)
            or not 1 <= pct <= 30
        ):  # 2
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):  # 3
            raise PermissionError("actor must be the opp's owner or a manager")
        if opp["stage"] in FINAL_STAGES:  # 4
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:  # 5
            raise PermissionError("rep may not discount more than 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100  # 6
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id: str, new_owner: str, actor: str) -> None:
        self._require_actor(actor)
        if opp_id not in self.opps:  # 1
            raise ValueError(f"no such opportunity {opp_id!r}")
        if not self._is_manager(actor):  # 2
            raise PermissionError("only managers may transfer")
        user = self.users.get(new_owner) if isinstance(new_owner, str) else None  # 3
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in FINAL_STAGES:  # 4
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:  # 5
            raise ValueError("new_owner is already the owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:  # 6
            raise ValueError("new_owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slots(previous_owner)

    def forecast(self) -> Dict[str, int]:
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won_total += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHT[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
