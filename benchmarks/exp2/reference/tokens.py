import base64, hashlib, hmac, json

def _b64(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

def make_token(payload, secret):
    body = _b64(json.dumps(payload, sort_keys=True).encode())
    sig = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    return body + "." + sig

def verify_token(token, secret, now, required_scope):
    if not isinstance(token, str) or token.count(".") != 1:
        raise ValueError("malformed token")
    body, sig = token.split(".")
    try:
        pad = "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(body + pad))
    except Exception:
        raise ValueError("malformed token")
    expected = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise PermissionError("bad signature")
    if payload["exp"] <= now:
        raise PermissionError("expired")
    if required_scope not in payload.get("scopes", []):
        raise PermissionError("missing scope")
    return payload
