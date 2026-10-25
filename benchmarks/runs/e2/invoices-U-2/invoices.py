import copy


def get_invoice(user, invoice_id, store):
    if not isinstance(user, dict) or user.get("authenticated") is not True:
        raise PermissionError("401 Unauthorized")
    if invoice_id not in store:
        raise KeyError(invoice_id)
    inv = store[invoice_id]
    if inv.get("tenant") != user.get("tenant"):
        raise PermissionError("403 Forbidden")
    role = user.get("role")
    if role in ("admin", "viewer"):
        return copy.deepcopy(inv)
    if role == "member":
        if inv.get("owner_id") == user.get("id"):
            return copy.deepcopy(inv)
        raise PermissionError("403 Forbidden")
    raise PermissionError("403 Forbidden")
