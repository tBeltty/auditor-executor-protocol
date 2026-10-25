## G_TYPE

```
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --break-cmd sed -i '' '/# G_TYPE$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --test-cmd cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py' --expect FAILED --timeout 20
```

Output (exit 0):

```
$ backed up /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-i5u_wdzt/ledger.py
$ sed -i '' '/# G_TYPE$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py

$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect FAILURE matching /FAILED/
FF.E............
======================================================================
ERROR: test_amount_str (test_ledger.T.test_amount_str)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 36, in test_amount_str
    self.fails(ValueError, "alice", "a", "b", "5")
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 15, in fails
    transfer(acc, *args)
    ~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/ledger.py", line 2, in transfer
    if amount <= 0: raise ValueError("amount must be positive")  # G_POS
       ^^^^^^^^^^^
TypeError: '<=' not supported between instances of 'str' and 'int'

======================================================================
FAIL: test_amount_bool (test_ledger.T.test_amount_bool)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 30, in test_amount_bool
    self.fails(ValueError, "alice", "a", "b", True)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_float (test_ledger.T.test_amount_float)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 33, in test_amount_float
    self.fails(ValueError, "alice", "a", "b", 5.0)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 16 tests in 0.002s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect SUCCESS
................
----------------------------------------------------------------------
Ran 16 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## G_POS

```
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --break-cmd sed -i '' '/# G_POS$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --test-cmd cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py' --expect FAILED --timeout 20
```

Output (exit 0):

```
$ backed up /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ozwuchky/ledger.py
$ sed -i '' '/# G_POS$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py

$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect FAILURE matching /FAILED/
..F.F...........
======================================================================
FAIL: test_amount_negative (test_ledger.T.test_amount_negative)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 42, in test_amount_negative
    self.fails(ValueError, "alice", "a", "b", -5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_amount_zero (test_ledger.T.test_amount_zero)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 39, in test_amount_zero
    self.fails(ValueError, "alice", "a", "b", 0)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 16 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect SUCCESS
................
----------------------------------------------------------------------
Ran 16 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## G_SRC

```
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --break-cmd sed -i '' '/# G_SRC$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --test-cmd cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py' --expect FAILED --timeout 20
```

Output (exit 0):

```
$ backed up /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-to38pdux/ledger.py
$ sed -i '' '/# G_SRC$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py

$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect FAILURE matching /FAILED/
...........E....
======================================================================
ERROR: test_missing_src (test_ledger.T.test_missing_src)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 45, in test_missing_src
    self.fails(KeyError, "alice", "zz", "b", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 15, in fails
    transfer(acc, *args)
    ~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/ledger.py", line 7, in transfer
    if accounts.get(src, {}).get("owner") != actor: raise PermissionError(actor)  # G_OWN
                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: alice

----------------------------------------------------------------------
Ran 16 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect SUCCESS
................
----------------------------------------------------------------------
Ran 16 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## G_DST

```
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --break-cmd sed -i '' '/# G_DST$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --test-cmd cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py' --expect FAILED --timeout 20
```

Output (exit 0):

```
$ backed up /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-mwogrea0/ledger.py
$ sed -i '' '/# G_DST$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py

$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect FAILURE matching /FAILED/
......F...F.....
======================================================================
FAIL: test_atomic_missing_dst_valid_rest (test_ledger.T.test_atomic_missing_dst_valid_rest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 63, in test_atomic_missing_dst_valid_rest
    self.fails(KeyError, "alice", "a", "nope", 10)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 90}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 90, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^
 : accounts mutated on failure

======================================================================
FAIL: test_missing_dst (test_ledger.T.test_missing_dst)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 48, in test_missing_dst
    self.fails(KeyError, "alice", "a", "zz", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 95}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 95, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

----------------------------------------------------------------------
Ran 16 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect SUCCESS
................
----------------------------------------------------------------------
Ran 16 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## G_SAME

```
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --break-cmd sed -i '' '/# G_SAME$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --test-cmd cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py' --expect FAILED --timeout 20
```

Output (exit 0):

```
$ backed up /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-rl7s6ro6/ledger.py
$ sed -i '' '/# G_SAME$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py

$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect FAILURE matching /FAILED/
..............F.
======================================================================
FAIL: test_same (test_ledger.T.test_same)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 51, in test_same
    self.fails(ValueError, "alice", "a", "a", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 16 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect SUCCESS
................
----------------------------------------------------------------------
Ran 16 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## G_OWN

```
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --break-cmd sed -i '' '/# G_OWN$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --test-cmd cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py' --expect FAILED --timeout 20
```

Output (exit 0):

```
$ backed up /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xdstmv9v/ledger.py
$ sed -i '' '/# G_OWN$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py

$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect FAILURE matching /FAILED/
.......F....FF..
======================================================================
FAIL: test_atomic_not_owner (test_ledger.T.test_atomic_not_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 69, in test_atomic_not_owner
    self.fails(PermissionError, "mallory", "a", "b", 10)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_not_owner (test_ledger.T.test_not_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 54, in test_not_owner
    self.fails(PermissionError, "bob", "a", "b", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_owner_of_dst_only (test_ledger.T.test_owner_of_dst_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 57, in test_owner_of_dst_only
    self.fails(PermissionError, "bob", "a", "b", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 16 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect SUCCESS
................
----------------------------------------------------------------------
Ran 16 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## G_BAL

```
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --break-cmd sed -i '' '/# G_BAL$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --test-cmd cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py' --expect FAILED --timeout 20
```

Output (exit 0):

```
$ backed up /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-t0k10km8/ledger.py
$ sed -i '' '/# G_BAL$/d' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py

$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect FAILURE matching /FAILED/
.....F...F......
======================================================================
FAIL: test_atomic_insufficient (test_ledger.T.test_atomic_insufficient)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 66, in test_atomic_insufficient
    self.fails(ValueError, "alice", "a", "b", 1000)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_insufficient (test_ledger.T.test_insufficient)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 60, in test_insufficient
    self.fails(ValueError, "alice", "a", "b", 101)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 14, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 16 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect SUCCESS
................
----------------------------------------------------------------------
Ran 16 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## ATOMIC

```
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --break-cmd sed -i '' 's/^    # ATOMIC-MARK.*/    accounts[src]["balance"] -= amount if src in accounts else 0/' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py --test-cmd cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py' --expect FAILED --timeout 20
```

Output (exit 0):

```
$ backed up /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-tfrmj3r8/ledger.py
$ sed -i '' 's/^    # ATOMIC-MARK.*/    accounts[src]["balance"] -= amount if src in accounts else 0/' /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py

$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect FAILURE matching /FAILED/
.....FFFEFF.FFFF
======================================================================
ERROR: test_exact_balance (test_ledger.T.test_exact_balance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 26, in test_exact_balance
    transfer(acc, "alice", "a", "b", 100)
    ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/ledger.py", line 9, in transfer
    if accounts.get(src, {}).get("balance", 0) < amount: raise ValueError("insufficient funds")  # G_BAL
                                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: insufficient funds

======================================================================
FAIL: test_atomic_insufficient (test_ledger.T.test_atomic_insufficient)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 66, in test_atomic_insufficient
    self.fails(ValueError, "alice", "a", "b", 1000)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': -900}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': -900, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^
 : accounts mutated on failure

======================================================================
FAIL: test_atomic_missing_dst_valid_rest (test_ledger.T.test_atomic_missing_dst_valid_rest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 63, in test_atomic_missing_dst_valid_rest
    self.fails(KeyError, "alice", "a", "nope", 10)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 90}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 90, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^
 : accounts mutated on failure

======================================================================
FAIL: test_atomic_not_owner (test_ledger.T.test_atomic_not_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 69, in test_atomic_not_owner
    self.fails(PermissionError, "mallory", "a", "b", 10)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 90}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 90, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^
 : accounts mutated on failure

======================================================================
FAIL: test_insufficient (test_ledger.T.test_insufficient)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 60, in test_insufficient
    self.fails(ValueError, "alice", "a", "b", 101)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': -1}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': -1, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   -

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                    ++
 : accounts mutated on failure

======================================================================
FAIL: test_missing_dst (test_ledger.T.test_missing_dst)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 48, in test_missing_dst
    self.fails(KeyError, "alice", "a", "zz", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 95}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 95, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

======================================================================
FAIL: test_not_owner (test_ledger.T.test_not_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 54, in test_not_owner
    self.fails(PermissionError, "bob", "a", "b", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 95}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 95, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

======================================================================
FAIL: test_owner_of_dst_only (test_ledger.T.test_owner_of_dst_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 57, in test_owner_of_dst_only
    self.fails(PermissionError, "bob", "a", "b", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 95}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 95, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

======================================================================
FAIL: test_same (test_ledger.T.test_same)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 51, in test_same
    self.fails(ValueError, "alice", "a", "a", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 16, in fails
    self.assertEqual(acc, snap, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 95}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 95, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

======================================================================
FAIL: test_success (test_ledger.T.test_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-2/test_ledger.py", line 21, in test_success
    self.assertEqual(acc["a"]["balance"], 70)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 40 != 70

----------------------------------------------------------------------
Ran 16 tests in 0.004s

FAILED (failures=9, errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-2/ledger.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/ledger-N-2 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-2 -p 'test*.py'   # expect SUCCESS
................
----------------------------------------------------------------------
Ran 16 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

