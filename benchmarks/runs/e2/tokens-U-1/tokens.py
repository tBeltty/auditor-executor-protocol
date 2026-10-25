import base64
import hashlib
import hmac
import json


def _sig(body, secret):
    return hmac.new(secret, body.encode("ascii"), hashlib.sha256).hexdigest()


def make_token(payload, secret):
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return body + "." + _sig(body, secret)


def verify_token(token, secret, now, required_scope):
    if not isinstance(token, str):
        raise ValueError("token must be a str")
    parts = token.split(".")
    if len(parts) != 2:
        raise ValueError("malformed token")
    body, sig = parts
    try:
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except Exception:
        raise ValueError("undecodable body")
    expected = _sig(body, secret)
    if not hmac.compare_digest(expected.encode("utf-8"), sig.encode("utf-8")):
        raise PermissionError("bad signature")
    if not isinstance(payload, dict):
        raise ValueError("payload not an object")
    if payload["exp"] <= now:
        raise PermissionError("token expired")
    if required_scope not in (payload.get("scopes") or []):
        raise PermissionError("missing scope")
    return payload
