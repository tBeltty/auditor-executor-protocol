### format: non-str

```
$ aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --break-cmd sed -i '' 's/if not isinstance(token, str):/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --expect AttributeError --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-lw_k1vga/tokens.py
$ sed -i '' 's/if not isinstance(token, str):/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect FAILURE matching /AttributeError/
.E......
======================================================================
ERROR: test_format_non_str (test_tokens.T.test_format_non_str)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 25, in test_format_non_str
    tokens.verify_token(bad, S, 1, "read")
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/tokens-N-2/tokens.py", line 20, in verify_token
    parts = token.split(".")
            ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'split'

----------------------------------------------------------------------
Ran 8 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect SUCCESS
........
----------------------------------------------------------------------
Ran 8 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```
### format: part count

```
$ aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --break-cmd sed -i '' 's/if len(parts) != 2:/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --expect IndexError|AssertionError --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ivhmuw4b/tokens.py
$ sed -i '' 's/if len(parts) != 2:/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect FAILURE matching /IndexError|AssertionError/
..E.....
======================================================================
ERROR: test_format_parts (test_tokens.T.test_format_parts)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 31, in test_format_parts
    tokens.verify_token(bad, S, 1, "read")
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/tokens-N-2/tokens.py", line 23, in verify_token
    body, sig = parts[0], parts[1]
                          ~~~~~^^^
IndexError: list index out of range

----------------------------------------------------------------------
Ran 8 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect SUCCESS
........
----------------------------------------------------------------------
Ran 8 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```
### format: undecodable body

```
$ aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --break-cmd sed -i '' 's/^        payload = json.loads(base64.*/        payload = {"exp": 10**9, "scopes": ["read"]}/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --expect ValueError --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-s7mjdeqh/tokens.py
$ sed -i '' 's/^        payload = json.loads(base64.*/        payload = {"exp": 10**9, "scopes": ["read"]}/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect FAILURE matching /ValueError/
F..FFF..
======================================================================
FAIL: test_expiry (test_tokens.T.test_expiry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 57, in test_expiry
    with self.assertRaisesRegex(PermissionError, "expired"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_format_undecodable_body (test_tokens.T.test_format_undecodable_body)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 34, in test_format_undecodable_body
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_roundtrip (test_tokens.T.test_roundtrip)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 18, in test_roundtrip
    self.assertEqual(tokens.verify_token(t, S, 999, "read"), P)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'exp': 1000000000, 'scopes': ['read']} != {'sub': 'u1', 'exp': 1000, 'scopes': ['read', 'write']}
- {'exp': 1000000000, 'scopes': ['read']}
+ {'exp': 1000, 'scopes': ['read', 'write'], 'sub': 'u1'}

======================================================================
FAIL: test_scope (test_tokens.T.test_scope)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 70, in test_scope
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 8 tests in 0.001s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect SUCCESS
........
----------------------------------------------------------------------
Ran 8 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```
### signature

```
$ aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --break-cmd sed -i '' 's/if not hmac.compare_digest(.*/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --expect signature --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-36jvw2ii/tokens.py
$ sed -i '' 's/if not hmac.compare_digest(.*/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect FAILURE matching /signature/
......FF
======================================================================
FAIL: test_signature (test_tokens.T.test_signature)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 41, in test_signature
    with self.assertRaisesRegex(PermissionError, "signature"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_signature_before_expiry (test_tokens.T.test_signature_before_expiry)
----------------------------------------------------------------------
PermissionError: token expired

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 52, in test_signature_before_expiry
    with self.assertRaisesRegex(PermissionError, "signature"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "signature" does not match "token expired"

----------------------------------------------------------------------
Ran 8 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect SUCCESS
........
----------------------------------------------------------------------
Ran 8 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```
### expiry

```
$ aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --break-cmd sed -i '' 's/if payload\["exp"\] <= now:/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --expect expired --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-cogrwd61/tokens.py
$ sed -i '' 's/if payload\["exp"\] <= now:/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect FAILURE matching /expired/
F.......
======================================================================
FAIL: test_expiry (test_tokens.T.test_expiry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 57, in test_expiry
    with self.assertRaisesRegex(PermissionError, "expired"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 8 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect SUCCESS
........
----------------------------------------------------------------------
Ran 8 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```
### scope

```
$ aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --break-cmd sed -i '' 's/if required_scope not in payload.get("scopes", \[\]):/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py --expect PermissionError --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5487rkmr/tokens.py
$ sed -i '' 's/if required_scope not in payload.get("scopes", \[\]):/if False:/' /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect FAILURE matching /PermissionError/
.....F..
======================================================================
FAIL: test_scope (test_tokens.T.test_scope)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-2/test_tokens.py", line 65, in test_scope
    with self.assertRaises(PermissionError) as c:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 8 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-2/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-2 -p 'test*.py'   # expect SUCCESS
........
----------------------------------------------------------------------
Ran 8 tests in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit=0
```
