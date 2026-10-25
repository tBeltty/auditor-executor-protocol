def transfer(accounts, actor, src, dst, amount):
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("amount must be a positive int")
    if src not in accounts or dst not in accounts:
        raise KeyError("unknown account")
    if src == dst:
        raise ValueError("src and dst must differ")
    if accounts[src]["owner"] != actor:
        raise PermissionError("actor does not own src")
    if accounts[src]["balance"] < amount:
        raise ValueError("insufficient funds")
    accounts[src]["balance"] -= amount
    accounts[dst]["balance"] += amount
