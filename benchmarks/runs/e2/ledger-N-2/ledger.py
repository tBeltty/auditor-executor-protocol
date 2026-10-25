def transfer(accounts, actor, src, dst, amount):
    if type(amount) is not int: raise ValueError("amount must be an int")  # G_TYPE
    if amount <= 0: raise ValueError("amount must be positive")  # G_POS
    # ATOMIC-MARK: no mutation may happen before every check below has passed
    if src not in accounts: raise KeyError(src)  # G_SRC
    if dst not in accounts: raise KeyError(dst)  # G_DST
    if src == dst: raise ValueError("src equals dst")  # G_SAME
    if accounts.get(src, {}).get("owner") != actor: raise PermissionError(actor)  # G_OWN
    if accounts.get(src, {}).get("balance", 0) < amount: raise ValueError("insufficient funds")  # G_BAL
    accounts[src]["balance"] -= amount
    accounts[dst]["balance"] += amount
