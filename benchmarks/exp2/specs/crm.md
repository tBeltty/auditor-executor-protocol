# Module: crm.py
Implement `class CRM` and `class DuplicateLeadError(Exception)` in a file named exactly `crm.py`. `DuplicateLeadError` has an attribute `existing_id`.

`CRM(reps)`: `reps` is a list of {"id": str, "role": "rep" or "manager", "capacity": int}. Every method takes the acting user as an id string `actor`.
Attributes: `leads` (dict id -> lead), `opps` (dict id -> opportunity), `log` (list of tuples `(op, entity_id, actor_id)`).
General rules:
- If `actor` is not the id of a known user, raise PermissionError. This is checked first in every method.
- A failed call (any exception) changes nothing and appends nothing to `log`. A successful call appends exactly the log entries named below.
- Load of a rep = number of leads it owns with status "new" or "qualified" + number of opportunities it owns whose stage is not "won" or "lost". Only role "rep" users receive work; managers never own anything.
- Checks run in the order listed for each method; the first failing check decides the exception.

`add_lead(email, name, source, actor) -> str`
1. email must be a str. Normalized email = email.strip().lower(); it must contain exactly one "@", a non-empty part before it, and a domain after it that contains a "." which is neither the first nor the last character of the domain. Otherwise ValueError.
2. name must be a str that is non-empty after strip(), else ValueError.
3. source must be "web", "referral" or "event", else ValueError.
4. If a lead with the same normalized email already exists, raise DuplicateLeadError with existing_id set to that lead's id.
5. id is "L<n>" where n counts successful lead creations starting at 1. score = 10 (web), 30 (referral) or 20 (event), plus 15 if the email domain is not one of gmail.com, yahoo.com, outlook.com.
6. owner = the rep with the lowest load among reps whose load is below their capacity (ties: smallest id in string order). If none qualifies, owner is None and the lead joins a FIFO waiting queue.
7. lead = {"id", "email" (normalized), "name" (stripped), "source", "score", "owner", "status": "new"}. Log ("add_lead", lead_id, actor). Return the id.

`qualify(lead_id, actor)`
1. The lead must exist (ValueError). 2. actor must be the lead's owner or a manager (PermissionError). 3. lead status must be "new" (ValueError). 4. score must be at least 30 (ValueError). Then status becomes "qualified"; log ("qualify", lead_id, actor).

`convert(lead_id, amount, actor) -> str`
1. The lead must exist (ValueError). 2. amount must be a positive int, not a bool (ValueError). 3. actor must be the lead's owner or a manager (PermissionError). 4. status must be "qualified" (ValueError). 5. The lead must have an owner (ValueError).
Then create an opportunity with id "O<n>" (n counts successful conversions from 1): {"id", "lead_id", "owner": lead owner, "amount": amount, "original_amount": amount, "stage": "prospect"}; the lead's status becomes "converted"; log ("convert", opp_id, actor); return the opportunity id.

`advance(opp_id, stage, actor)`
Stage order: prospect -> proposal -> negotiation -> won. From any non-final stage an opportunity may also go to "lost". "won" and "lost" are final.
1. The opportunity must exist (ValueError). 2. stage must be one of prospect, proposal, negotiation, won, lost (ValueError). 3. actor must be the opportunity's owner or a manager (PermissionError). 4. The current stage must not be final (ValueError). 5. The new stage must be "lost" or the immediate next stage in the order (ValueError). 6. Moving to "negotiation" when amount is greater than 50000 requires a manager (PermissionError).
Then set the stage and log ("advance", opp_id, actor). If the new stage is "won" or "lost", the owner's slot is freed: while the owner's load is below its capacity and the waiting queue is not empty, take the oldest waiting lead, set its owner to this rep and log ("assign", lead_id, "system").

`discount(opp_id, pct, actor)`
1. The opportunity must exist (ValueError). 2. pct must be an int (not bool) from 1 to 30 inclusive (ValueError). 3. actor must be the owner or a manager (PermissionError). 4. The stage must not be final (ValueError). 5. A non-manager actor may use at most 10, else PermissionError. 6. new_amount = amount * (100 - pct) // 100 must satisfy new_amount * 100 >= original_amount * 70 (cumulative discount of at most 30 percent), else ValueError.
Then set amount = new_amount; log ("discount", opp_id, actor).

`transfer(opp_id, new_owner, actor)`
1. The opportunity must exist (ValueError). 2. actor must be a manager (PermissionError). 3. new_owner must be the id of a known user with role "rep" (ValueError). 4. The stage must not be final (ValueError). 5. new_owner must differ from the current owner (ValueError). 6. new_owner's load must be below its capacity (ValueError).
Then set the owner and log ("transfer", opp_id, actor). Then free the previous owner's slot exactly as in `advance` (assign waiting leads while its load is below capacity).

`forecast() -> dict` (no actor, no log entry)
Returns {"open": number of opportunities not in a final stage, "weighted": sum over open opportunities of amount * w // 100 with w = 10 (prospect), 30 (proposal), 60 (negotiation), "won": sum of amount over opportunities with stage "won"}.
