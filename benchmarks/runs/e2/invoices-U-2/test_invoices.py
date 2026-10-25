import unittest
from invoices import get_invoice


def mk(role="admin", auth=True, tenant="t1", uid="u1"):
    u = {"id": uid, "tenant": tenant, "role": role}
    if auth is not None:
        u["authenticated"] = auth
    return u


STORE = {
    "i1": {"id": "i1", "tenant": "t1", "amount": 10, "owner_id": "u1"},
    "i2": {"id": "i2", "tenant": "t1", "amount": 20, "owner_id": "u2"},
    "i3": {"id": "i3", "tenant": "t2", "amount": 30, "owner_id": "u1"},
}


class T(unittest.TestCase):
    def test_unauth(self):
        for a in (False, None):
            with self.assertRaises(PermissionError) as c:
                get_invoice(mk(auth=a), "i1", STORE)
            self.assertTrue(str(c.exception).startswith("401"))

    def test_unauth_before_missing(self):
        with self.assertRaises(PermissionError):
            get_invoice(mk(auth=False), "zz", STORE)

    def test_missing(self):
        with self.assertRaises(KeyError):
            get_invoice(mk(), "zz", STORE)

    def test_cross_tenant_all_roles(self):
        for r in ("admin", "viewer", "member", "x", None):
            with self.assertRaises(PermissionError) as c:
                get_invoice(mk(role=r), "i3", STORE)
            self.assertTrue(str(c.exception).startswith("403"))

    def test_admin_viewer(self):
        for r in ("admin", "viewer"):
            self.assertEqual(get_invoice(mk(role=r), "i2", STORE), STORE["i2"])

    def test_member(self):
        self.assertEqual(get_invoice(mk(role="member"), "i1", STORE), STORE["i1"])
        with self.assertRaises(PermissionError) as c:
            get_invoice(mk(role="member"), "i2", STORE)
        self.assertTrue(str(c.exception).startswith("403"))

    def test_other_roles(self):
        for r in ("guest", None, ""):
            with self.assertRaises(PermissionError) as c:
                get_invoice(mk(role=r), "i1", STORE)
            self.assertTrue(str(c.exception).startswith("403"))

    def test_copy(self):
        r = get_invoice(mk(), "i1", STORE)
        r["amount"] = 999
        self.assertEqual(STORE["i1"]["amount"], 10)


if __name__ == "__main__":
    unittest.main()
