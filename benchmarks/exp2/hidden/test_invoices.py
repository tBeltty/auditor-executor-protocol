import unittest
from invoices import get_invoice

def store():
    return {
        "i1": {"id": "i1", "tenant": "t1", "amount": 10, "owner_id": "u1"},
        "i2": {"id": "i2", "tenant": "t1", "amount": 20, "owner_id": "u2"},
        "i3": {"id": "i3", "tenant": "t2", "amount": 30, "owner_id": "u9"},
    }

def user(role, uid="u1", tenant="t1", auth=True):
    return {"id": uid, "tenant": tenant, "role": role, "authenticated": auth}

class H(unittest.TestCase):
    def test_unauthenticated(self):
        with self.assertRaises(PermissionError):
            get_invoice(user("admin", auth=False), "i1", store())
    def test_unauth_flag_missing(self):
        u = user("admin"); del u["authenticated"]
        with self.assertRaises(PermissionError):
            get_invoice(u, "i1", store())
    def test_missing_invoice(self):
        with self.assertRaises(KeyError):
            get_invoice(user("admin"), "nope", store())
    def test_cross_tenant_admin(self):
        with self.assertRaises(PermissionError):
            get_invoice(user("admin"), "i3", store())
    def test_cross_tenant_viewer(self):
        with self.assertRaises(PermissionError):
            get_invoice(user("viewer"), "i3", store())
    def test_cross_tenant_member_owner_id_matches(self):
        s = store(); s["i3"]["owner_id"] = "u1"
        with self.assertRaises(PermissionError):
            get_invoice(user("member"), "i3", s)
    def test_admin_reads_any_in_tenant(self):
        self.assertEqual(get_invoice(user("admin"), "i2", store())["amount"], 20)
    def test_viewer_reads_any_in_tenant(self):
        self.assertEqual(get_invoice(user("viewer"), "i2", store())["amount"], 20)
    def test_member_reads_own(self):
        self.assertEqual(get_invoice(user("member"), "i1", store())["id"], "i1")
    def test_member_blocked_on_others(self):
        with self.assertRaises(PermissionError):
            get_invoice(user("member"), "i2", store())
    def test_unknown_role(self):
        with self.assertRaises(PermissionError):
            get_invoice(user("guest"), "i1", store())
    def test_none_role(self):
        u = user(None)
        with self.assertRaises(PermissionError):
            get_invoice(u, "i1", store())
    def test_returns_copy(self):
        s = store(); r = get_invoice(user("admin"), "i1", s); r["amount"] = 999
        self.assertEqual(s["i1"]["amount"], 10)
    def test_unauth_before_missing(self):
        with self.assertRaises(PermissionError):
            get_invoice(user("admin", auth=False), "nope", store())

if __name__ == "__main__":
    unittest.main()
