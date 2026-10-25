import copy


def get_invoice(user, invoice_id, store):
    if not user.get("authenticated"):
        raise PermissionError("401 unauthenticated")
    if invoice_id not in store:
        raise KeyError(invoice_id)
    inv = store[invoice_id]
    if inv.get("tenant") != user.get("tenant"):
        raise PermissionError("403 forbidden")
    role = user.get("role")
    if role in ("admin", "viewer"):
        pass
    elif role == "member":
        if inv.get("owner_id") != user.get("id"):
            raise PermissionError("403 forbidden")
    else:
        raise PermissionError("403 forbidden")
    return copy.deepcopy(inv)
