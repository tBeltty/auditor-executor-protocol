import copy
import unittest
from ledger import transfer


def make():
    return {"a": {"owner": "alice", "balance": 100}, "b": {"owner": "bob", "balance": 50}}


class T(unittest.TestCase):
    def fails(self, exc, *args):
        acc = make()
        snap = copy.deepcopy(acc)
        with self.assertRaises(exc):
            transfer(acc, *args)
        self.assertEqual(acc, snap, "accounts mutated on failure")

    def test_success(self):
        acc = make()
        self.assertIsNone(transfer(acc, "alice", "a", "b", 30))
        self.assertEqual(acc["a"]["balance"], 70)
        self.assertEqual(acc["b"]["balance"], 80)

    def test_exact_balance(self):
        acc = make()
        transfer(acc, "alice", "a", "b", 100)
        self.assertEqual((acc["a"]["balance"], acc["b"]["balance"]), (0, 150))

    def test_amount_bool(self):
        self.fails(ValueError, "alice", "a", "b", True)

    def test_amount_float(self):
        self.fails(ValueError, "alice", "a", "b", 5.0)

    def test_amount_str(self):
        self.fails(ValueError, "alice", "a", "b", "5")

    def test_amount_zero(self):
        self.fails(ValueError, "alice", "a", "b", 0)

    def test_amount_negative(self):
        self.fails(ValueError, "alice", "a", "b", -5)

    def test_missing_src(self):
        self.fails(KeyError, "alice", "zz", "b", 5)

    def test_missing_dst(self):
        self.fails(KeyError, "alice", "a", "zz", 5)

    def test_same(self):
        self.fails(ValueError, "alice", "a", "a", 5)

    def test_not_owner(self):
        self.fails(PermissionError, "bob", "a", "b", 5)

    def test_owner_of_dst_only(self):
        self.fails(PermissionError, "bob", "a", "b", 5)

    def test_insufficient(self):
        self.fails(ValueError, "alice", "a", "b", 101)

    def test_atomic_missing_dst_valid_rest(self):
        self.fails(KeyError, "alice", "a", "nope", 10)

    def test_atomic_insufficient(self):
        self.fails(ValueError, "alice", "a", "b", 1000)

    def test_atomic_not_owner(self):
        self.fails(PermissionError, "mallory", "a", "b", 10)


if __name__ == "__main__":
    unittest.main()
