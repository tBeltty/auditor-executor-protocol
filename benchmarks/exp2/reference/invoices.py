def get_invoice(user, invoice_id, store):
    if not user.get("authenticated"):
        raise PermissionError("401 Unauthorized")
    inv = store[invoice_id]
    if inv["tenant"] != user["tenant"]:
        raise PermissionError("403 Forbidden: cross-tenant")
    role = user.get("role")
    if role == "admin" or role == "viewer":
        return dict(inv)
    if role == "member":
        if inv["owner_id"] == user["id"]:
            return dict(inv)
        raise PermissionError("403 Forbidden: not owner")
    raise PermissionError("403 Forbidden: unknown role")
