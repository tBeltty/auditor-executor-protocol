## auth

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py --break-cmd "sed -i '' 's/if not user.get(\"authenticated\") is True:  # GUARD_AUTH/if False:  # GUARD_AUTH/' /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'" --expect "FAIL|Error" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-vn68pgl3/invoices.py
$ sed -i '' 's/if not user.get("authenticated") is True:  # GUARD_AUTH/if False:  # GUARD_AUTH/' /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'   # expect FAILURE matching /FAIL|Error/
......EFF
======================================================================
ERROR: test_unauth_before_keyerror (test_invoices.T.test_unauth_before_keyerror)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-2/test_invoices.py", line 33, in test_unauth_before_keyerror
    get_invoice(U("admin", auth=False), "zzz", mk())
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/invoices-N-2/invoices.py", line 8, in get_invoice
    raise KeyError(invoice_id)
KeyError: 'zzz'

======================================================================
FAIL: test_unauth_false (test_invoices.T.test_unauth_false)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-2/test_invoices.py", line 20, in test_unauth_false
    with self.assertRaises(PermissionError) as c:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unauth_missing_flag (test_invoices.T.test_unauth_missing_flag)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-2/test_invoices.py", line 27, in test_unauth_missing_flag
    with self.assertRaises(PermissionError) as c:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 9 tests in 0.001s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## tenant

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py --break-cmd "sed -i '' 's/if invoice.get(\"tenant\") != user.get(\"tenant\"):  # GUARD_TENANT/if False:  # GUARD_TENANT/' /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'" --expect "FAIL|Error" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ak8dfz8q/invoices.py
$ sed -i '' 's/if invoice.get("tenant") != user.get("tenant"):  # GUARD_TENANT/if False:  # GUARD_TENANT/' /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'   # expect FAILURE matching /FAIL|Error/
..F......
======================================================================
FAIL: test_cross_tenant_all_roles (test_invoices.T.test_cross_tenant_all_roles)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-2/test_invoices.py", line 41, in test_cross_tenant_all_roles
    with self.assertRaises(PermissionError) as c:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 9 tests in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## owner

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py --break-cmd "sed -i '' 's/if invoice.get(\"owner_id\") != user.get(\"id\"):  # GUARD_OWNER/if False:  # GUARD_OWNER/' /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'" --expect "FAIL|Error" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3kemppdk/invoices.py
$ sed -i '' 's/if invoice.get("owner_id") != user.get("id"):  # GUARD_OWNER/if False:  # GUARD_OWNER/' /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'   # expect FAILURE matching /FAIL|Error/
...F.....
======================================================================
FAIL: test_member_own_only (test_invoices.T.test_member_own_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-2/test_invoices.py", line 52, in test_member_own_only
    with self.assertRaises(PermissionError) as c:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 9 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## role

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py --break-cmd "sed -i '' 's/raise PermissionError(\"403 role not allowed\")  # GUARD_ROLE_OTHER/pass/' /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'" --expect "FAIL|Error" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-l1z9dpfg/invoices.py
$ sed -i '' 's/raise PermissionError("403 role not allowed")  # GUARD_ROLE_OTHER/pass/' /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'   # expect FAILURE matching /FAIL|Error/
.....F...
======================================================================
FAIL: test_other_roles_denied (test_invoices.T.test_other_roles_denied)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/invoices-N-2/test_invoices.py", line 58, in test_other_roles_denied
    with self.assertRaises(PermissionError) as c:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 9 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/invoices-N-2/invoices.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/invoices-N-2 -p 'test*.py'   # expect SUCCESS
.........
----------------------------------------------------------------------
Ran 9 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

