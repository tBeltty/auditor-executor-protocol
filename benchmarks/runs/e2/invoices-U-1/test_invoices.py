import unittest
from invoices import get_invoice


def U(role="admin", tenant="t1", uid="u1", auth=True):
    return {"id": uid, "tenant": tenant, "role": role, "authenticated": auth}


def S():
    return {
        "i1": {"id": "i1", "tenant": "t1", "amount": 5, "owner_id": "u1"},
        "i2": {"id": "i2", "tenant": "t1", "amount": 7, "owner_id": "u2"},
        "i3": {"id": "i3", "tenant": "t2", "amount": 9, "owner_id": "u1"},
    }


class T(unittest.TestCase):
    def test_unauth(self):
        for u in (U(auth=False), {"id": "u1", "tenant": "t1", "role": "admin"}):
            with self.assertRaises(PermissionError) as c:
                get_invoice(u, "i1", S())
            self.assertTrue(str(c.exception).startswith("401"))

    def test_unauth_before_missing(self):
        with self.assertRaises(PermissionError):
            get_invoice(U(auth=False), "nope", S())

    def test_missing(self):
        with self.assertRaises(KeyError):
            get_invoice(U(), "nope", S())

    def test_cross_tenant_all_roles(self):
        for r in ("admin", "viewer", "member", "x", None):
            with self.assertRaises(PermissionError) as c:
                get_invoice(U(role=r), "i3", S())
            self.assertTrue(str(c.exception).startswith("403"))

    def test_admin_viewer(self):
        for r in ("admin", "viewer"):
            self.assertEqual(get_invoice(U(role=r), "i2", S())["id"], "i2")

    def test_member(self):
        self.assertEqual(get_invoice(U(role="member"), "i1", S())["id"], "i1")
        with self.assertRaises(PermissionError) as c:
            get_invoice(U(role="member"), "i2", S())
        self.assertTrue(str(c.exception).startswith("403"))

    def test_other_roles(self):
        for r in ("guest", None, ""):
            with self.assertRaises(PermissionError) as c:
                get_invoice(U(role=r), "i1", S())
            self.assertTrue(str(c.exception).startswith("403"))

    def test_copy(self):
        s = S()
        r = get_invoice(U(), "i1", s)
        r["amount"] = 999
        self.assertEqual(s["i1"]["amount"], 5)


if __name__ == "__main__":
    unittest.main()
