import base64
import hashlib
import hmac
import json


def _b64e(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _sign(body, secret):
    return hmac.new(secret, body.encode("ascii"), hashlib.sha256).hexdigest()


def make_token(payload, secret):
    body = _b64e(json.dumps(payload, sort_keys=True).encode("utf-8"))
    return body + "." + _sign(body, secret)


def verify_token(token, secret, now, required_scope):
    if not isinstance(token, str): raise ValueError("token must be a string")  # GUARD_FORMAT_TYPE
    if token.count(".") != 1: raise ValueError("token must have two parts")  # GUARD_FORMAT_PARTS
    body, _, sig = token.partition(".")
    try:
        payload = json.loads(_b64d(body).decode("utf-8"))
    except Exception:  # GUARD_FORMAT_JSON
        raise ValueError("body not decodable")
    if not hmac.compare_digest(_sign(body, secret).encode("ascii"), sig.encode("utf-8")): raise PermissionError("bad signature")  # GUARD_SIG
    if payload["exp"] <= now: raise PermissionError("token expired")  # GUARD_EXP
    if required_scope not in payload.get("scopes", []): raise PermissionError("missing scope")  # GUARD_SCOPE
    return payload
