import unittest
from tokens import make_token, verify_token

S = b"secret"
def tok(**kw):
    p = {"sub": "u1", "exp": 1000, "scopes": ["read", "write"]}; p.update(kw)
    return make_token(p, S)

class H(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(verify_token(tok(), S, 500, "read")["sub"], "u1")
    def test_expired(self):
        with self.assertRaises(PermissionError): verify_token(tok(), S, 1500, "read")
    def test_exp_boundary_is_expired(self):
        with self.assertRaises(PermissionError): verify_token(tok(), S, 1000, "read")
    def test_one_before_exp_ok(self):
        self.assertEqual(verify_token(tok(), S, 999, "read")["sub"], "u1")
    def test_wrong_secret(self):
        with self.assertRaises(PermissionError): verify_token(tok(), b"other", 500, "read")
    def test_tampered_payload(self):
        t = tok(); body, sig = t.split(".")
        forged = make_token({"sub": "admin", "exp": 1000, "scopes": ["read"]}, b"x").split(".")[0]
        with self.assertRaises(PermissionError): verify_token(forged + "." + sig, S, 500, "read")
    def test_tampered_signature(self):
        t = tok(); body, sig = t.split(".")
        bad = sig[:-1] + ("0" if sig[-1] != "0" else "1")
        with self.assertRaises(PermissionError): verify_token(body + "." + bad, S, 500, "read")
    def test_missing_scope(self):
        with self.assertRaises(PermissionError): verify_token(tok(), S, 500, "admin")
    def test_empty_scopes(self):
        with self.assertRaises(PermissionError): verify_token(tok(scopes=[]), S, 500, "read")
    def test_no_dot(self):
        with self.assertRaises(ValueError): verify_token("abcdef", S, 500, "read")
    def test_two_dots(self):
        with self.assertRaises(ValueError): verify_token("a.b.c", S, 500, "read")
    def test_non_string(self):
        with self.assertRaises(ValueError): verify_token(None, S, 500, "read")
    def test_garbage_body(self):
        with self.assertRaises(ValueError): verify_token("!!!.abc", S, 500, "read")
    def test_signature_checked_before_expiry(self):
        with self.assertRaises(PermissionError) as cm:
            verify_token(tok(), b"other", 5000, "read")
        self.assertIn("signature", str(cm.exception).lower())

if __name__ == "__main__":
    unittest.main()
