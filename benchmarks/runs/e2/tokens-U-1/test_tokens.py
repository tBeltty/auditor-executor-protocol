import unittest
from tokens import make_token, verify_token

S = b"k"
P = {"sub": "u", "exp": 100, "scopes": ["a", "b"]}


class T(unittest.TestCase):
    def test_roundtrip(self):
        self.assertEqual(verify_token(make_token(P, S), S, 50, "a"), P)

    def test_no_padding(self):
        t = make_token(P, S)
        self.assertNotIn("=", t.split(".")[0])

    def test_malformed(self):
        for t in [5, "abc", "a.b.c", "!!.sig"]:
            with self.assertRaises(ValueError):
                verify_token(t, S, 0, "a")

    def test_bad_json(self):
        import base64
        b = base64.urlsafe_b64encode(b"nope").decode().rstrip("=")
        with self.assertRaises(ValueError):
            verify_token(b + ".x", S, 0, "a")

    def test_signature(self):
        with self.assertRaises(PermissionError) as c:
            verify_token(make_token(P, S), b"z", 50, "a")
        self.assertIn("signature", str(c.exception))

    def test_sig_before_expiry(self):
        with self.assertRaises(PermissionError) as c:
            verify_token(make_token(P, S), b"z", 500, "a")
        self.assertIn("signature", str(c.exception))

    def test_expired(self):
        for now in (100, 101):
            with self.assertRaises(PermissionError) as c:
                verify_token(make_token(P, S), S, now, "a")
            self.assertIn("expired", str(c.exception))

    def test_scope(self):
        with self.assertRaises(PermissionError):
            verify_token(make_token(P, S), S, 50, "c")
        q = {"sub": "u", "exp": 100}
        with self.assertRaises(PermissionError):
            verify_token(make_token(q, S), S, 50, "a")


if __name__ == "__main__":
    unittest.main()
