import copy
import unittest

from ledger import transfer


def mk():
    return {
        "a": {"owner": "alice", "balance": 100},
        "b": {"owner": "bob", "balance": 50},
    }


class TransferTests(unittest.TestCase):
    def fails(self, exc, *args):
        acc = mk()
        before = copy.deepcopy(acc)
        with self.assertRaises(exc):
            transfer(acc, *args)
        self.assertEqual(acc, before)

    def test_success(self):
        acc = mk()
        transfer(acc, "alice", "a", "b", 30)
        self.assertEqual(acc["a"]["balance"], 70)
        self.assertEqual(acc["b"]["balance"], 80)

    def test_exact_balance(self):
        acc = mk()
        transfer(acc, "alice", "a", "b", 100)
        self.assertEqual(acc["a"]["balance"], 0)
        self.assertEqual(acc["b"]["balance"], 150)

    def test_bad_amounts(self):
        for amt in (True, False, 1.0, 0, -5, "5", None):
            self.fails(ValueError, "alice", "a", "b", amt)

    def test_missing_accounts(self):
        self.fails(KeyError, "alice", "x", "b", 1)
        self.fails(KeyError, "alice", "a", "x", 1)

    def test_same_account(self):
        self.fails(ValueError, "alice", "a", "a", 1)

    def test_permission(self):
        self.fails(PermissionError, "bob", "a", "b", 1)

    def test_insufficient(self):
        self.fails(ValueError, "alice", "a", "b", 101)


if __name__ == "__main__":
    unittest.main()
