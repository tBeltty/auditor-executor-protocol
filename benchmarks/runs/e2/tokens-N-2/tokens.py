import base64
import hashlib
import hmac
import json


def _sign(body, secret):
    return hmac.new(secret, body.encode("ascii"), hashlib.sha256).hexdigest()


def make_token(payload, secret):
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return body + "." + _sign(body, secret)


def verify_token(token, secret, now, required_scope):
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    parts = token.split(".")
    if len(parts) != 2:
        raise ValueError("token must have two parts")
    body, sig = parts[0], parts[1]
    try:
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    except Exception:
        raise ValueError("body not decodable")

    if not hmac.compare_digest(sig.encode("utf-8"), _sign(body, secret).encode("ascii")):
        raise PermissionError("bad signature")
    if payload["exp"] <= now:
        raise PermissionError("token expired")
    if required_scope not in payload.get("scopes", []):
        raise PermissionError("missing scope")
    return payload
