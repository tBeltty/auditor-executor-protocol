import unittest
from invoices import get_invoice


def U(role="admin", tenant="t1", uid="u1", auth=True):
    return {"id": uid, "tenant": tenant, "role": role, "authenticated": auth}


def S():
    return {
        "i1": {"id": "i1", "tenant": "t1", "amount": 5, "owner_id": "u1"},
        "i2": {"id": "i2", "tenant": "t1", "amount": 7, "owner_id": "u2"},
        "x1": {"id": "x1", "tenant": "t2", "amount": 9, "owner_id": "u1"},
    }


class T(unittest.TestCase):
    def test_unauth_false(self):
        with self.assertRaisesRegex(PermissionError, "^401"):
            get_invoice(U(auth=False), "i1", S())

    def test_unauth_missing(self):
        u = U()
        del u["authenticated"]
        with self.assertRaisesRegex(PermissionError, "^401"):
            get_invoice(u, "i1", S())

    def test_unauth_before_keyerror(self):
        with self.assertRaisesRegex(PermissionError, "^401"):
            get_invoice(U(auth=False), "nope", S())

    def test_missing(self):
        with self.assertRaises(KeyError):
            get_invoice(U(), "nope", S())

    def test_cross_tenant_all_roles(self):
        for r in ("admin", "viewer", "member", "other", None):
            with self.assertRaisesRegex(PermissionError, "^403"):
                get_invoice(U(role=r, uid="u1"), "x1", S())

    def test_admin_viewer_read_any_in_tenant(self):
        for r in ("admin", "viewer"):
            self.assertEqual(get_invoice(U(role=r), "i2", S())["amount"], 7)

    def test_member_own(self):
        self.assertEqual(get_invoice(U(role="member"), "i1", S())["id"], "i1")

    def test_member_other(self):
        with self.assertRaisesRegex(PermissionError, "^403"):
            get_invoice(U(role="member"), "i2", S())

    def test_other_roles(self):
        for r in ("guest", "", None, "ADMIN"):
            with self.assertRaisesRegex(PermissionError, "^403"):
                get_invoice(U(role=r), "i1", S())

    def test_copy(self):
        s = S()
        r = get_invoice(U(), "i1", s)
        r["amount"] = 999
        self.assertEqual(s["i1"]["amount"], 5)
        self.assertIsNot(r, s["i1"])


if __name__ == "__main__":
    unittest.main()
