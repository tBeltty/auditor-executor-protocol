import unittest
from invoices import get_invoice


def mk():
    return {
        "a": {"id": "a", "tenant": "t1", "amount": 10, "owner_id": "u1"},
        "b": {"id": "b", "tenant": "t1", "amount": 20, "owner_id": "u2"},
        "c": {"id": "c", "tenant": "t2", "amount": 30, "owner_id": "u1"},
    }


def U(role, uid="u1", tenant="t1", auth=True):
    return {"id": uid, "tenant": tenant, "role": role, "authenticated": auth}


class T(unittest.TestCase):
    def test_unauth_false(self):
        for role in ("admin", "viewer", "member"):
            with self.assertRaises(PermissionError) as c:
                get_invoice(U(role, auth=False), "a", mk())
            self.assertTrue(str(c.exception).startswith("401"))

    def test_unauth_missing_flag(self):
        u = U("admin")
        del u["authenticated"]
        with self.assertRaises(PermissionError) as c:
            get_invoice(u, "a", mk())
        self.assertTrue(str(c.exception).startswith("401"))

    def test_unauth_before_keyerror(self):
        with self.assertRaises(PermissionError):
            get_invoice(U("admin", auth=False), "zzz", mk())

    def test_missing_invoice(self):
        with self.assertRaises(KeyError):
            get_invoice(U("admin"), "zzz", mk())

    def test_cross_tenant_all_roles(self):
        for role in ("admin", "viewer", "member"):
            with self.assertRaises(PermissionError) as c:
                get_invoice(U(role, uid="u1"), "c", mk())
            self.assertTrue(str(c.exception).startswith("403"))

    def test_admin_viewer_read_any_in_tenant(self):
        for role in ("admin", "viewer"):
            self.assertEqual(get_invoice(U(role), "b", mk())["id"], "b")
            self.assertEqual(get_invoice(U(role), "a", mk())["id"], "a")

    def test_member_own_only(self):
        self.assertEqual(get_invoice(U("member"), "a", mk())["id"], "a")
        with self.assertRaises(PermissionError) as c:
            get_invoice(U("member"), "b", mk())
        self.assertTrue(str(c.exception).startswith("403"))

    def test_other_roles_denied(self):
        for role in ("guest", None, "", "ADMIN", "owner"):
            with self.assertRaises(PermissionError) as c:
                get_invoice(U(role), "a", mk())
            self.assertTrue(str(c.exception).startswith("403"))

    def test_copy(self):
        s = mk()
        r = get_invoice(U("admin"), "a", s)
        r["amount"] = 999
        self.assertEqual(s["a"]["amount"], 10)
        self.assertEqual(r["id"], "a")


if __name__ == "__main__":
    unittest.main()
