# Module: tokens.py
Implement in a file named exactly `tokens.py`:
- `make_token(payload: dict, secret: bytes) -> str`: returns `<body>.<sig>` where body = urlsafe-base64 (no padding) of JSON(payload, sort_keys=True) and sig = lowercase hex HMAC-SHA256(secret, body).
- `verify_token(token: str, secret: bytes, now: int, required_scope: str) -> dict`
payload = {"sub": str, "exp": int, "scopes": [str, ...]}
Rules:
1. token not a str, or not exactly two dot-separated parts, or body not decodable JSON -> ValueError.
2. Signature mismatch -> PermissionError whose message contains "signature". Compare in constant time. The signature check happens BEFORE the expiry check.
3. exp <= now -> PermissionError (message contains "expired").
4. required_scope not in payload["scopes"] (missing key counts as empty) -> PermissionError.
5. Otherwise return the payload dict.
