# Module: ledger.py
Implement `transfer(accounts: dict, actor: str, src: str, dst: str, amount: int) -> None` in a file named exactly `ledger.py`.
- `accounts` maps account_id -> {"owner": str, "balance": int}; transfer mutates it in place.
Rules:
1. amount must be a positive int; bool, float, zero, negative -> ValueError.
2. src or dst not in accounts -> KeyError.
3. src == dst -> ValueError.
4. actor must own src, otherwise PermissionError.
5. If src balance < amount -> ValueError (an exact-balance transfer is allowed).
6. Atomic: if any rule fails, `accounts` must be left completely unchanged.
7. On success, debit src and credit dst by amount.
