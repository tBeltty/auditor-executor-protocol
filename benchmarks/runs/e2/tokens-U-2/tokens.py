import base64
import binascii
import hashlib
import hmac
import json


def _sig(secret, body):
    return hmac.new(secret, body.encode("ascii"), hashlib.sha256).hexdigest()


def make_token(payload, secret):
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    return body + "." + _sig(secret, body)


def verify_token(token, secret, now, required_scope):
    if not isinstance(token, str):
        raise ValueError("token must be a string")
    parts = token.split(".")
    if len(parts) != 2:
        raise ValueError("malformed token")
    body, sig = parts
    try:
        raw = base64.urlsafe_b64decode(body.encode("ascii") + b"=" * (-len(body) % 4))
        payload = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError, binascii.Error):
        raise ValueError("undecodable body")
    if not isinstance(payload, dict):
        raise ValueError("payload not an object")
    expected = _sig(secret, body)
    if not hmac.compare_digest(expected.encode("utf-8"), sig.encode("utf-8")):
        raise PermissionError("bad signature")
    if payload["exp"] <= now:
        raise PermissionError("token expired")
    if required_scope not in payload.get("scopes", []):
        raise PermissionError("missing scope")
    return payload
