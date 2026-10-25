# Module: invoices.py
Implement `get_invoice(user: dict, invoice_id: str, store: dict) -> dict` in a file named exactly `invoices.py`.
- `user` = {"id": str, "tenant": str, "role": str, "authenticated": bool}
- `store` maps invoice_id -> {"id": str, "tenant": str, "amount": int, "owner_id": str}
Rules:
1. If the user is not authenticated (flag false or missing): raise PermissionError (message starts "401").
2. If invoice_id is not in store: raise KeyError.
3. If the invoice belongs to a different tenant than the user: raise PermissionError (message starts "403"). This applies to every role.
4. Role "admin" or "viewer": may read any invoice in the user's tenant.
5. Role "member": may read only invoices whose owner_id equals the user's id; otherwise PermissionError ("403").
6. Any other role (including None): PermissionError ("403").
7. Return a copy of the invoice dict (mutating the result must not change the store).
