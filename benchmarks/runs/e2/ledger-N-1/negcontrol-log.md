## G_BOOL
```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --break-cmd sed -i.bak '/# G_BOOL$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak --test-cmd python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py' --expect (FAIL|AssertionError|not raised|Error) --timeout 20
$ backed up /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7s3es22_/ledger.py
$ sed -i.bak '/# G_BOOL$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect FAILURE matching /(FAIL|AssertionError|not raised|Error)/
F............
======================================================================
FAIL: test_bool (test_ledger.TransferTests.test_bool)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 35, in test_bool
    self.fails(ValueError, "alice", "a", "b", True)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 17, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## G_INT
```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --break-cmd sed -i.bak '/# G_INT$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak --test-cmd python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py' --expect (FAIL|AssertionError|not raised|Error) --timeout 20
$ backed up /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-b2dl_egx/ledger.py
$ sed -i.bak '/# G_INT$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect FAILURE matching /(FAIL|AssertionError|not raised|Error)/
..F.......E..
======================================================================
ERROR: test_string (test_ledger.TransferTests.test_string)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 42, in test_string
    self.fails(ValueError, "alice", "a", "b", "5")
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 18, in fails
    transfer(acc, *args)
    ~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/ledger.py", line 3, in transfer
    if amount <= 0: raise ValueError("amount must be positive")  # G_POS
       ^^^^^^^^^^^
TypeError: '<=' not supported between instances of 'str' and 'int'

======================================================================
FAIL: test_float (test_ledger.TransferTests.test_float)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 38, in test_float
    self.fails(ValueError, "alice", "a", "b", 5.0)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 17, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## G_POS
```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --break-cmd sed -i.bak '/# G_POS$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak --test-cmd python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py' --expect (FAIL|AssertionError|not raised|Error) --timeout 20
$ backed up /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-92qtsnkm/ledger.py
$ sed -i.bak '/# G_POS$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect FAILURE matching /(FAIL|AssertionError|not raised|Error)/
.......F....F
======================================================================
FAIL: test_negative (test_ledger.TransferTests.test_negative)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 48, in test_negative
    self.fails(ValueError, "alice", "a", "b", -5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 17, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_zero (test_ledger.TransferTests.test_zero)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 45, in test_zero
    self.fails(ValueError, "alice", "a", "b", 0)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 17, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## G_SRC
```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --break-cmd sed -i.bak '/# G_SRC$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak --test-cmd python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py' --expect (FAIL|AssertionError|not raised|Error) --timeout 20
$ backed up /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-p7xs261y/ledger.py
$ sed -i.bak '/# G_SRC$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect FAILURE matching /(FAIL|AssertionError|not raised|Error)/
.....E.......
======================================================================
ERROR: test_missing_src (test_ledger.TransferTests.test_missing_src)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 51, in test_missing_src
    self.fails(KeyError, "alice", "zz", "b", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 18, in fails
    transfer(acc, *args)
    ~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/ledger.py", line 7, in transfer
    if accounts.get(src, {}).get("owner") != actor: raise PermissionError(actor)  # G_OWN
                                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: alice

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## G_DST
```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --break-cmd sed -i.bak '/# G_DST$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak --test-cmd python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py' --expect (FAIL|AssertionError|not raised|Error) --timeout 20
$ backed up /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-es8vrp78/ledger.py
$ sed -i.bak '/# G_DST$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect FAILURE matching /(FAIL|AssertionError|not raised|Error)/
....F........
======================================================================
FAIL: test_missing_dst (test_ledger.TransferTests.test_missing_dst)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 54, in test_missing_dst
    self.fails(KeyError, "alice", "a", "zz", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 19, in fails
    self.assertEqual(acc, before, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 95}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 95, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## G_SAME
```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --break-cmd sed -i.bak '/# G_SAME$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak --test-cmd python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py' --expect (FAIL|AssertionError|not raised|Error) --timeout 20
$ backed up /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-gwhwe71a/ledger.py
$ sed -i.bak '/# G_SAME$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect FAILURE matching /(FAIL|AssertionError|not raised|Error)/
.........F...
======================================================================
FAIL: test_same_account (test_ledger.TransferTests.test_same_account)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 57, in test_same_account
    self.fails(ValueError, "alice", "a", "a", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 17, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## G_OWN
```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --break-cmd sed -i.bak '/# G_OWN$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak --test-cmd python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py' --expect (FAIL|AssertionError|not raised|Error) --timeout 20
$ backed up /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5i__z8nl/ledger.py
$ sed -i.bak '/# G_OWN$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect FAILURE matching /(FAIL|AssertionError|not raised|Error)/
........F....
======================================================================
FAIL: test_not_owner (test_ledger.TransferTests.test_not_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 60, in test_not_owner
    self.fails(PermissionError, "bob", "a", "b", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 17, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## G_BAL
```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --break-cmd sed -i.bak '/# G_BAL$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak --test-cmd python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py' --expect (FAIL|AssertionError|not raised|Error) --timeout 20
$ backed up /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-34h8slzx/ledger.py
$ sed -i.bak '/# G_BAL$/d' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py && rm -f /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py.bak

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect FAILURE matching /(FAIL|AssertionError|not raised|Error)/
...F.........
======================================================================
FAIL: test_insufficient (test_ledger.TransferTests.test_insufficient)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 64, in test_insufficient
    self.fails(ValueError, "alice", "a", "b", 101)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 17, in fails
    with self.assertRaises(exc):
         ~~~~~~~~~~~~~~~~~^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

## G_ATOMIC
```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --break-cmd perl -pi -e 's/^(def transfer.*
)/$1    accounts[src]["balance"] -= amount if src in accounts and isinstance(amount, int) else 0
/' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py --test-cmd python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py' --expect mutated on failure --timeout 20
$ backed up /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-_ggxmnq1/ledger.py
$ perl -pi -e 's/^(def transfer.*\n)/$1    accounts[src]["balance"] -= amount if src in accounts and isinstance(amount, int) else 0\n/' /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect FAILURE matching /mutated on failure/
FE.FF.EFFF.F.
======================================================================
ERROR: test_exact_balance (test_ledger.TransferTests.test_exact_balance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 30, in test_exact_balance
    transfer(acc, "alice", "a", "b", 100)
    ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/ledger.py", line 10, in transfer
    if accounts[src]["balance"] < amount: raise ValueError("insufficient funds")  # G_BAL
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: insufficient funds

======================================================================
ERROR: test_multiple_sequential (test_ledger.TransferTests.test_multiple_sequential)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 69, in test_multiple_sequential
    transfer(acc, "bob", "b", "a", 60)
    ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/ledger.py", line 10, in transfer
    if accounts[src]["balance"] < amount: raise ValueError("insufficient funds")  # G_BAL
                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: insufficient funds

======================================================================
FAIL: test_bool (test_ledger.TransferTests.test_bool)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 35, in test_bool
    self.fails(ValueError, "alice", "a", "b", True)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 19, in fails
    self.assertEqual(acc, before, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 99}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 99, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

======================================================================
FAIL: test_insufficient (test_ledger.TransferTests.test_insufficient)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 64, in test_insufficient
    self.fails(ValueError, "alice", "a", "b", 101)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 19, in fails
    self.assertEqual(acc, before, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': -1}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': -1, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   -

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                    ++
 : accounts mutated on failure

======================================================================
FAIL: test_missing_dst (test_ledger.TransferTests.test_missing_dst)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 54, in test_missing_dst
    self.fails(KeyError, "alice", "a", "zz", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 19, in fails
    self.assertEqual(acc, before, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 95}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 95, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

======================================================================
FAIL: test_negative (test_ledger.TransferTests.test_negative)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 48, in test_negative
    self.fails(ValueError, "alice", "a", "b", -5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 19, in fails
    self.assertEqual(acc, before, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 105}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 105, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                     ^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                     ^
 : accounts mutated on failure

======================================================================
FAIL: test_not_owner (test_ledger.TransferTests.test_not_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 60, in test_not_owner
    self.fails(PermissionError, "bob", "a", "b", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 19, in fails
    self.assertEqual(acc, before, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 95}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 95, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

======================================================================
FAIL: test_same_account (test_ledger.TransferTests.test_same_account)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 57, in test_same_account
    self.fails(ValueError, "alice", "a", "a", 5)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 19, in fails
    self.assertEqual(acc, before, "accounts mutated on failure")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'a': {'owner': 'alice', 'balance': 95}, 'b': {'owner': 'bob', 'balance': 50}} != {'a': {'owner': 'alice', 'balance': 100}, 'b': {'owner': 'bob', 'balance': 50}}
- {'a': {'balance': 95, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^

+ {'a': {'balance': 100, 'owner': 'alice'}, 'b': {'balance': 50, 'owner': 'bob'}}
?                   ^^^
 : accounts mutated on failure

======================================================================
FAIL: test_success (test_ledger.TransferTests.test_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/ledger-N-1/test_ledger.py", line 24, in test_success
    self.assertEqual(acc["a"]["balance"], 70)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 40 != 70

----------------------------------------------------------------------
Ran 13 tests in 0.004s

FAILED (failures=7, errors=2)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/ledger-N-1/ledger.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/ledger-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
[exit 0]
```

