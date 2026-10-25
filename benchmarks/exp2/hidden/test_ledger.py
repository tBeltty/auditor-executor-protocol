import unittest
from ledger import transfer

def acc():
    return {"a": {"owner": "alice", "balance": 100}, "b": {"owner": "bob", "balance": 50}}

class H(unittest.TestCase):
    def test_ok(self):
        x = acc(); transfer(x, "alice", "a", "b", 30)
        self.assertEqual((x["a"]["balance"], x["b"]["balance"]), (70, 80))
    def test_exact_balance(self):
        x = acc(); transfer(x, "alice", "a", "b", 100)
        self.assertEqual((x["a"]["balance"], x["b"]["balance"]), (0, 150))
    def test_insufficient(self):
        x = acc()
        with self.assertRaises(ValueError): transfer(x, "alice", "a", "b", 101)
        self.assertEqual((x["a"]["balance"], x["b"]["balance"]), (100, 50))
    def test_zero(self):
        x = acc()
        with self.assertRaises(ValueError): transfer(x, "alice", "a", "b", 0)
        self.assertEqual(x, acc())
    def test_negative(self):
        x = acc()
        with self.assertRaises(ValueError): transfer(x, "alice", "a", "b", -5)
        self.assertEqual(x, acc())
    def test_bool_amount(self):
        x = acc()
        with self.assertRaises(ValueError): transfer(x, "alice", "a", "b", True)
        self.assertEqual(x, acc())
    def test_float_amount(self):
        x = acc()
        with self.assertRaises(ValueError): transfer(x, "alice", "a", "b", 1.5)
    def test_wrong_owner(self):
        x = acc()
        with self.assertRaises(PermissionError): transfer(x, "bob", "a", "b", 10)
        self.assertEqual(x, acc())
    def test_unknown_src(self):
        with self.assertRaises(KeyError): transfer(acc(), "alice", "zz", "b", 10)
    def test_unknown_dst(self):
        x = acc()
        with self.assertRaises(KeyError): transfer(x, "alice", "a", "zz", 10)
        self.assertEqual(x, acc())
    def test_same_account(self):
        x = acc()
        with self.assertRaises(ValueError): transfer(x, "alice", "a", "a", 10)
        self.assertEqual(x, acc())
    def test_no_mutation_on_permission_error(self):
        x = acc()
        with self.assertRaises(PermissionError): transfer(x, "bob", "a", "b", 1000)
        self.assertEqual(x, acc())

if __name__ == "__main__":
    unittest.main()
