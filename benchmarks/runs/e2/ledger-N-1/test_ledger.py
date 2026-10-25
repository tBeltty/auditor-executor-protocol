import copy
import unittest
from ledger import transfer


def make():
    return {
        "a": {"owner": "alice", "balance": 100},
        "b": {"owner": "bob", "balance": 50},
    }


class TransferTests(unittest.TestCase):
    def fails(self, exc, *args):
        acc = make()
        before = copy.deepcopy(acc)
        with self.assertRaises(exc):
            transfer(acc, *args)
        self.assertEqual(acc, before, "accounts mutated on failure")

    def test_success(self):
        acc = make()
        self.assertIsNone(transfer(acc, "alice", "a", "b", 30))
        self.assertEqual(acc["a"]["balance"], 70)
        self.assertEqual(acc["b"]["balance"], 80)
        self.assertEqual(acc["a"]["owner"], "alice")

    def test_exact_balance(self):
        acc = make()
        transfer(acc, "alice", "a", "b", 100)
        self.assertEqual(acc["a"]["balance"], 0)
        self.assertEqual(acc["b"]["balance"], 150)

    def test_bool(self):
        self.fails(ValueError, "alice", "a", "b", True)

    def test_float(self):
        self.fails(ValueError, "alice", "a", "b", 5.0)
        self.fails(ValueError, "alice", "a", "b", 5.5)

    def test_string(self):
        self.fails(ValueError, "alice", "a", "b", "5")

    def test_zero(self):
        self.fails(ValueError, "alice", "a", "b", 0)

    def test_negative(self):
        self.fails(ValueError, "alice", "a", "b", -5)

    def test_missing_src(self):
        self.fails(KeyError, "alice", "zz", "b", 5)

    def test_missing_dst(self):
        self.fails(KeyError, "alice", "a", "zz", 5)

    def test_same_account(self):
        self.fails(ValueError, "alice", "a", "a", 5)

    def test_not_owner(self):
        self.fails(PermissionError, "bob", "a", "b", 5)
        self.fails(PermissionError, "alice", "b", "a", 5)

    def test_insufficient(self):
        self.fails(ValueError, "alice", "a", "b", 101)

    def test_multiple_sequential(self):
        acc = make()
        transfer(acc, "alice", "a", "b", 10)
        transfer(acc, "bob", "b", "a", 60)
        self.assertEqual(acc["a"]["balance"], 150)
        self.assertEqual(acc["b"]["balance"], 0)


if __name__ == "__main__":
    unittest.main()
