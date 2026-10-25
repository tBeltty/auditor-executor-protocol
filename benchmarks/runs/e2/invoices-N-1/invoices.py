def get_invoice(user, invoice_id, store):
    if not user.get("authenticated") is True:  # GUARD_AUTH
        raise PermissionError("401 unauthenticated")
    if invoice_id not in store:
        raise KeyError(invoice_id)
    inv = store[invoice_id]
    if inv["tenant"] != user.get("tenant"):  # GUARD_TENANT
        raise PermissionError("403 tenant mismatch")
    role = user.get("role")
    if role in ("admin", "viewer"):  # GUARD_ROLE_READ
        pass
    elif role == "member":
        if inv["owner_id"] != user.get("id"):  # GUARD_OWNER
            raise PermissionError("403 not owner")
    else:  # GUARD_ROLE_OTHER
        raise PermissionError("403 role not allowed")
    return dict(inv)
