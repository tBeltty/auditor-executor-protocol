import base64
import unittest

import tokens

S = b"secret"
P = {"sub": "u1", "exp": 1000, "scopes": ["read", "write"]}


def forge(body_bytes, secret=S):
    body = base64.urlsafe_b64encode(body_bytes).rstrip(b"=").decode()
    return body + "." + tokens._sign(body, secret)


class T(unittest.TestCase):
    def test_roundtrip(self):
        t = tokens.make_token(P, S)
        self.assertEqual(tokens.verify_token(t, S, 999, "read"), P)
        self.assertNotIn("=", t)
        self.assertEqual(len(t.split(".")[1]), 64)

    def test_format_non_str(self):
        for bad in (None, 5, b"a.b"):
            with self.assertRaises(ValueError):
                tokens.verify_token(bad, S, 1, "read")

    def test_format_parts(self):
        good = tokens.make_token(P, S)
        for bad in ("abc", "a.b.c", "", good + ".extra", "." + good):
            with self.assertRaises(ValueError):
                tokens.verify_token(bad, S, 1, "read")

    def test_format_undecodable_body(self):
        with self.assertRaises(ValueError):
            tokens.verify_token(forge(b"not json"), S, 1, "read")
        with self.assertRaises(ValueError):
            tokens.verify_token("!!!.abc", S, 1, "read")

    def test_signature(self):
        t = tokens.make_token(P, S)
        with self.assertRaisesRegex(PermissionError, "signature"):
            tokens.verify_token(t, b"other", 1, "read")
        body, sig = t.split(".")
        with self.assertRaisesRegex(PermissionError, "signature"):
            tokens.verify_token(body + "." + "0" * 64, S, 1, "read")
        evil = tokens.make_token(dict(P, scopes=["admin"]), S).split(".")[0]
        with self.assertRaisesRegex(PermissionError, "signature"):
            tokens.verify_token(evil + "." + sig, S, 1, "admin")

    def test_signature_before_expiry(self):
        t = tokens.make_token(P, b"other")
        with self.assertRaisesRegex(PermissionError, "signature"):
            tokens.verify_token(t, S, 5000, "read")

    def test_expiry(self):
        t = tokens.make_token(P, S)
        with self.assertRaisesRegex(PermissionError, "expired"):
            tokens.verify_token(t, S, 1000, "read")
        with self.assertRaisesRegex(PermissionError, "expired"):
            tokens.verify_token(t, S, 2000, "read")
        self.assertEqual(tokens.verify_token(t, S, 999, "read"), P)

    def test_scope(self):
        t = tokens.make_token(P, S)
        with self.assertRaises(PermissionError) as c:
            tokens.verify_token(t, S, 1, "admin")
        self.assertNotIn("signature", str(c.exception))
        self.assertNotIn("expired", str(c.exception))
        t2 = tokens.make_token({"sub": "u", "exp": 1000}, S)
        with self.assertRaises(PermissionError):
            tokens.verify_token(t2, S, 1, "read")
        t3 = tokens.make_token({"sub": "u", "exp": 1000, "scopes": []}, S)
        with self.assertRaises(PermissionError):
            tokens.verify_token(t3, S, 1, "read")


if __name__ == "__main__":
    unittest.main()
