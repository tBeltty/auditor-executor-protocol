def transfer(accounts, actor, src, dst, amount):
    if isinstance(amount, bool): raise ValueError("bool amount")  # G_BOOL
    if not isinstance(amount, int): raise ValueError("non-int amount")  # G_INT
    if amount <= 0: raise ValueError("amount must be positive")  # G_POS
    if src not in accounts: raise KeyError(src)  # G_SRC
    if dst not in accounts: raise KeyError(dst)  # G_DST
    if src == dst: raise ValueError("same account")  # G_SAME
    if accounts.get(src, {}).get("owner") != actor: raise PermissionError(actor)  # G_OWN
    if accounts[src]["balance"] < amount: raise ValueError("insufficient funds")  # G_BAL
    accounts[src]["balance"] -= amount
    accounts[dst]["balance"] += amount
