import unittest
from tokens import make_token, verify_token

S = b"secret"
P = {"sub": "a", "exp": 100, "scopes": ["r", "w"]}


class T(unittest.TestCase):
    def test_roundtrip(self):
        t = make_token(P, S)
        self.assertNotIn("=", t)
        self.assertEqual(verify_token(t, S, 50, "r"), P)

    def test_malformed(self):
        for t in [5, "abc", "a.b.c", "!!!.x"]:
            with self.assertRaises(ValueError):
                verify_token(t, S, 0, "r")

    def test_bad_json(self):
        import base64
        b = base64.urlsafe_b64encode(b"nope").decode().rstrip("=")
        with self.assertRaises(ValueError):
            verify_token(b + ".00", S, 0, "r")

    def test_signature_before_expiry(self):
        t = make_token(P, b"other")
        with self.assertRaises(PermissionError) as c:
            verify_token(t, S, 999, "r")
        self.assertIn("signature", str(c.exception))

    def test_expired(self):
        t = make_token(P, S)
        with self.assertRaises(PermissionError) as c:
            verify_token(t, S, 100, "r")
        self.assertIn("expired", str(c.exception))

    def test_scope(self):
        with self.assertRaises(PermissionError):
            verify_token(make_token(P, S), S, 1, "x")
        with self.assertRaises(PermissionError):
            verify_token(make_token({"sub": "a", "exp": 100}, S), S, 1, "r")


if __name__ == "__main__":
    unittest.main()
