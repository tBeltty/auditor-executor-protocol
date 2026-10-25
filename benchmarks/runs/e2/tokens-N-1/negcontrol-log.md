## Guard FORMAT_TYPE

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py --break-cmd "perl -pi -e 's/: raise .*?  # GUARD_FORMAT_TYPE/: pass  # GUARD_FORMAT_TYPE/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'" --expect "ERROR: test_format_nonstr" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-cqhcdnu6/tokens.py
$ perl -pi -e 's/: raise .*?  # GUARD_FORMAT_TYPE/: pass  # GUARD_FORMAT_TYPE/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect FAILURE matching /ERROR: test_format_nonstr/
...E.........
======================================================================
ERROR: test_format_nonstr (test_tokens.T.test_format_nonstr)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 44, in test_format_nonstr
    verify_token(bad, S, NOW, "read")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/tokens-N-1/tokens.py", line 26, in verify_token
    if token.count(".") != 1: raise ValueError("token must have two parts")  # GUARD_FORMAT_PARTS
       ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'count'

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard FORMAT_PARTS

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py --break-cmd "perl -pi -e 's/: raise .*?  # GUARD_FORMAT_PARTS/: pass  # GUARD_FORMAT_PARTS/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'" --expect "ERROR: test_format_parts" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-u8b3b_ap/tokens.py
$ perl -pi -e 's/: raise .*?  # GUARD_FORMAT_PARTS/: pass  # GUARD_FORMAT_PARTS/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect FAILURE matching /ERROR: test_format_parts/
....E........
======================================================================
ERROR: test_format_parts (test_tokens.T.test_format_parts)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 50, in test_format_parts
    verify_token(bad, S, NOW, "read")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/tokens-N-1/tokens.py", line 32, in verify_token
    if not hmac.compare_digest(_sign(body, secret).encode("ascii"), sig.encode("utf-8")): raise PermissionError("bad signature")  # GUARD_SIG
                                                                                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: bad signature

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard FORMAT_JSON

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py --break-cmd "perl -pi -e 's/raise ValueError\(.body not decodable.\)/payload = {}/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'" --expect "ERROR: test_format_json" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xmv3spl7/tokens.py
$ perl -pi -e 's/raise ValueError\(.body not decodable.\)/payload = {}/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect FAILURE matching /ERROR: test_format_json/
..E..........
======================================================================
ERROR: test_format_json (test_tokens.T.test_format_json)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 55, in test_format_json
    verify_token(forge(b64(raw)), S, NOW, "read")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/runs/e2/tokens-N-1/tokens.py", line 33, in verify_token
    if payload["exp"] <= now: raise PermissionError("token expired")  # GUARD_EXP
       ~~~~~~~^^^^^^^
KeyError: 'exp'

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard SIG

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py --break-cmd "perl -pi -e 's/: raise .*?  # GUARD_SIG/: pass  # GUARD_SIG/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'" --expect "FAIL: test_signature" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-f_k8mlla/tokens.py
$ perl -pi -e 's/: raise .*?  # GUARD_SIG/: pass  # GUARD_SIG/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect FAILURE matching /FAIL: test_signature/
.........FFF.
======================================================================
FAIL: test_signature (test_tokens.T.test_signature)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 64, in test_signature
    with self.assertRaises(PermissionError) as c:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_signature_before_expiry (test_tokens.T.test_signature_before_expiry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 83, in test_signature_before_expiry
    self.assertIn("signature", str(c.exception))
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'signature' not found in 'token expired'

======================================================================
FAIL: test_signature_before_scope (test_tokens.T.test_signature_before_scope)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 90, in test_signature_before_scope
    self.assertIn("signature", str(c.exception))
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'signature' not found in 'missing scope'

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard EXP

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py --break-cmd "perl -pi -e 's/: raise .*?  # GUARD_EXP/: pass  # GUARD_EXP/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'" --expect "FAIL: test_expiry" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-r6zyeklo/tokens.py
$ perl -pi -e 's/: raise .*?  # GUARD_EXP/: pass  # GUARD_EXP/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect FAILURE matching /FAIL: test_expiry/
FF...........
======================================================================
FAIL: test_expiry (test_tokens.T.test_expiry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 94, in test_expiry
    with self.assertRaises(PermissionError) as c:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_expiry_before_scope (test_tokens.T.test_expiry_before_scope)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 102, in test_expiry_before_scope
    self.assertIn("expired", str(c.exception))
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'expired' not found in 'missing scope'

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Guard SCOPE

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py --break-cmd "perl -pi -e 's/: raise .*?  # GUARD_SCOPE/: pass  # GUARD_SCOPE/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'" --expect "FAIL: test_scope" --timeout 20
$ backed up /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-syzpg_cb/tokens.py
$ perl -pi -e 's/: raise .*?  # GUARD_SCOPE/: pass  # GUARD_SCOPE/' /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py

$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect FAILURE matching /FAIL: test_scope/
.......FF....
======================================================================
FAIL: test_scope (test_tokens.T.test_scope)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 106, in test_scope
    with self.assertRaises(PermissionError) as c:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_scope_missing_key (test_tokens.T.test_scope_missing_key)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/runs/e2/tokens-N-1/test_tokens.py", line 115, in test_scope_missing_key
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 13 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/runs/e2/tokens-N-1/tokens.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/runs/e2/tokens-N-1 -p 'test*.py'   # expect SUCCESS
.............
----------------------------------------------------------------------
Ran 13 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

