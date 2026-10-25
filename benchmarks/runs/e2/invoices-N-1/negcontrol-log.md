## auth

`/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py --break-cmd "sed -i '' 's/if not user.get(\"authenticated\") is True:  # GUARD_AUTH/if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py" --test-cmd "cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1" --expect "FAIL|Error" --timeout 20`

```
$ backed up /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-4refeon_/invoices.py
$ sed -i '' 's/if not user.get("authenticated") is True:  # GUARD_AUTH/if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py

$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect FAILURE matching /FAIL|Error/
.......EFF
======================================================================
ERROR: test_unauth_before_keyerror (test_invoices.T.test_unauth_before_keyerror)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-1/test_invoices.py", line 30, in test_unauth_before_keyerror
    get_invoice(U(auth=False), "nope", S())
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/invoices-N-1/invoices.py", line 5, in get_invoice
    raise KeyError(invoice_id)
KeyError: 'nope'

======================================================================
FAIL: test_unauth_false (test_invoices.T.test_unauth_false)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-1/test_invoices.py", line 19, in test_unauth_false
    with self.assertRaisesRegex(PermissionError, "^401"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unauth_missing (test_invoices.T.test_unauth_missing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-1/test_invoices.py", line 25, in test_unauth_missing
    with self.assertRaisesRegex(PermissionError, "^401"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 10 tests in 0.001s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect SUCCESS
..........
----------------------------------------------------------------------
Ran 10 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## tenant

`/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py --break-cmd "sed -i '' 's/if inv\[\"tenant\"\] != user.get(\"tenant\"):  # GUARD_TENANT/if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py" --test-cmd "cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1" --expect "FAIL|Error" --timeout 20`

```
$ backed up /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9y4qu0vh/invoices.py
$ sed -i '' 's/if inv\["tenant"\] != user.get("tenant"):  # GUARD_TENANT/if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py

$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect FAILURE matching /FAIL|Error/
..F.......
======================================================================
FAIL: test_cross_tenant_all_roles (test_invoices.T.test_cross_tenant_all_roles)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-1/test_invoices.py", line 38, in test_cross_tenant_all_roles
    with self.assertRaisesRegex(PermissionError, "^403"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 10 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect SUCCESS
..........
----------------------------------------------------------------------
Ran 10 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## owner

`/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py --break-cmd "sed -i '' 's/if inv\[\"owner_id\"\] != user.get(\"id\"):  # GUARD_OWNER/if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py" --test-cmd "cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1" --expect "FAIL|Error" --timeout 20`

```
$ backed up /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-mqk6d90z/invoices.py
$ sed -i '' 's/if inv\["owner_id"\] != user.get("id"):  # GUARD_OWNER/if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py

$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect FAILURE matching /FAIL|Error/
...F......
======================================================================
FAIL: test_member_other (test_invoices.T.test_member_other)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-1/test_invoices.py", line 49, in test_member_other
    with self.assertRaisesRegex(PermissionError, "^403"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 10 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect SUCCESS
..........
----------------------------------------------------------------------
Ran 10 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## role_other

`/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py --break-cmd "sed -i '' 's/else:  # GUARD_ROLE_OTHER/else:  # x\n        return dict(inv)\n    if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py" --test-cmd "cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1" --expect "FAIL|Error" --timeout 20`

```
$ backed up /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-i2pz6wia/invoices.py
$ sed -i '' 's/else:  # GUARD_ROLE_OTHER/else:  # x\n        return dict(inv)\n    if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py

$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect FAILURE matching /FAIL|Error/
......F...
======================================================================
FAIL: test_other_roles (test_invoices.T.test_other_roles)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-1/test_invoices.py", line 54, in test_other_roles
    with self.assertRaisesRegex(PermissionError, "^403"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 10 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect SUCCESS
..........
----------------------------------------------------------------------
Ran 10 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## role_read

`/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py --break-cmd "sed -i '' 's/if role in (\"admin\", \"viewer\"):  # GUARD_ROLE_READ/if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py" --test-cmd "cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1" --expect "FAIL|Error" --timeout 20`

```
$ backed up /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-hkquh_rc/invoices.py
$ sed -i '' 's/if role in ("admin", "viewer"):  # GUARD_ROLE_READ/if False:/' /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py

$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect FAILURE matching /FAIL|Error/
EE........
======================================================================
ERROR: test_admin_viewer_read_any_in_tenant (test_invoices.T.test_admin_viewer_read_any_in_tenant)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-1/test_invoices.py", line 43, in test_admin_viewer_read_any_in_tenant
    self.assertEqual(get_invoice(U(role=r), "i2", S())["amount"], 7)
                     ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/invoices-N-1/invoices.py", line 16, in get_invoice
    raise PermissionError("403 role not allowed")
PermissionError: 403 role not allowed

======================================================================
ERROR: test_copy (test_invoices.T.test_copy)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-1/test_invoices.py", line 59, in test_copy
    r = get_invoice(U(), "i1", s)
  File "/tmp/aep-lab/runs/e2/invoices-N-1/invoices.py", line 16, in get_invoice
    raise PermissionError("403 role not allowed")
PermissionError: 403 role not allowed

----------------------------------------------------------------------
Ran 10 tests in 0.001s

FAILED (errors=2)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/invoices-N-1/invoices.py from backup (byte-identical)
$ cd /tmp/aep-lab/runs/e2/invoices-N-1 && python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-1 -p 'test*.py' 2>&1   # expect SUCCESS
..........
----------------------------------------------------------------------
Ran 10 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

