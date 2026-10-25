import base64, hashlib, hmac, json, unittest
from tokens import make_token, verify_token

S = b"secret"
NOW = 1000


def P(**kw):
    d = {"sub": "u", "exp": 2000, "scopes": ["read", "write"]}
    d.update(kw)
    return d


def forge(body, secret=S):
    return body + "." + hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()


def b64(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


class T(unittest.TestCase):
    def test_make_format(self):
        t = make_token(P(), S)
        body, sig = t.split(".")
        self.assertNotIn("=", body)
        self.assertEqual(json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))), P())
        self.assertEqual(sig, hmac.new(S, body.encode(), hashlib.sha256).hexdigest())
        self.assertEqual(sig, sig.lower())

    def test_sorted_keys(self):
        a = make_token({"b": 1, "a": 2}, S)
        b = make_token({"a": 2, "b": 1}, S)
        self.assertEqual(a, b)
        raw = base64.urlsafe_b64decode(a.split(".")[0] + "==")
        self.assertEqual(raw, b'{"a": 2, "b": 1}')

    def test_ok(self):
        self.assertEqual(verify_token(make_token(P(), S), S, NOW, "read"), P())

    def test_format_nonstr(self):
        for bad in (None, 5, b"a.b", ["a", "b"]):
            with self.assertRaises(ValueError):
                verify_token(bad, S, NOW, "read")

    def test_format_parts(self):
        t = make_token(P(), S)
        for bad in ("", "abc", t + ".x", "a.b.c"):
            with self.assertRaises(ValueError):
                verify_token(bad, S, NOW, "read")

    def test_format_json(self):
        for raw in (b"not json", b"\xff\xfe"):
            with self.assertRaises(ValueError):
                verify_token(forge(b64(raw)), S, NOW, "read")
        with self.assertRaises(ValueError):
            verify_token(forge("!!!"), S, NOW, "read")
        with self.assertRaises(ValueError):
            verify_token("x.y", S, NOW, "read")

    def test_signature(self):
        t = make_token(P(), S)
        for bad in (verify_token_args(t, b"other"),):
            with self.assertRaises(PermissionError) as c:
                verify_token(*bad)
            self.assertIn("signature", str(c.exception))
        body = t.split(".")[0]
        with self.assertRaises(PermissionError) as c:
            verify_token(body + "." + "0" * 64, S, NOW, "read")
        self.assertIn("signature", str(c.exception))
        with self.assertRaises(PermissionError):
            verify_token(body + ".", S, NOW, "read")
        # tampered payload, original signature
        evil = b64(json.dumps(P(scopes=["admin"]), sort_keys=True).encode())
        with self.assertRaises(PermissionError) as c:
            verify_token(evil + "." + t.split(".")[1], S, NOW, "admin")
        self.assertIn("signature", str(c.exception))

    def test_signature_before_expiry(self):
        t = make_token(P(exp=1), S)
        with self.assertRaises(PermissionError) as c:
            verify_token(t, b"other", NOW, "read")
        self.assertIn("signature", str(c.exception))
        self.assertNotIn("expired", str(c.exception))

    def test_signature_before_scope(self):
        t = make_token(P(), S)
        with self.assertRaises(PermissionError) as c:
            verify_token(t, b"other", NOW, "nope")
        self.assertIn("signature", str(c.exception))

    def test_expiry(self):
        for exp in (NOW, NOW - 1, 0):
            with self.assertRaises(PermissionError) as c:
                verify_token(make_token(P(exp=exp), S), S, NOW, "read")
            self.assertIn("expired", str(c.exception))
        self.assertEqual(verify_token(make_token(P(exp=NOW + 1), S), S, NOW, "read")["exp"], NOW + 1)

    def test_expiry_before_scope(self):
        with self.assertRaises(PermissionError) as c:
            verify_token(make_token(P(exp=1), S), S, NOW, "nope")
        self.assertIn("expired", str(c.exception))

    def test_scope(self):
        t = make_token(P(), S)
        with self.assertRaises(PermissionError) as c:
            verify_token(t, S, NOW, "admin")
        self.assertNotIn("signature", str(c.exception))
        self.assertNotIn("expired", str(c.exception))
        with self.assertRaises(PermissionError):
            verify_token(make_token(P(scopes=[]), S), S, NOW, "read")

    def test_scope_missing_key(self):
        t = make_token({"sub": "u", "exp": 2000}, S)
        with self.assertRaises(PermissionError):
            verify_token(t, S, NOW, "read")


def verify_token_args(t, secret):
    return (t, secret, NOW, "read")


if __name__ == "__main__":
    unittest.main()
