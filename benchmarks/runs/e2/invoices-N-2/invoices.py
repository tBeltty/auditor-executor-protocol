import copy


def get_invoice(user, invoice_id, store):
    if not user.get("authenticated") is True:  # GUARD_AUTH
        raise PermissionError("401 unauthenticated")
    if invoice_id not in store:
        raise KeyError(invoice_id)
    invoice = store[invoice_id]
    if invoice.get("tenant") != user.get("tenant"):  # GUARD_TENANT
        raise PermissionError("403 tenant mismatch")
    role = user.get("role")
    if role in ("admin", "viewer"):  # GUARD_ROLE_ALLOW
        pass
    elif role == "member":
        if invoice.get("owner_id") != user.get("id"):  # GUARD_OWNER
            raise PermissionError("403 not owner")
    else:
        raise PermissionError("403 role not allowed")  # GUARD_ROLE_OTHER
    return copy.deepcopy(invoice)
