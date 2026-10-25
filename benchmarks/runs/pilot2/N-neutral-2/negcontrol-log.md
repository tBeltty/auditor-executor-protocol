# Negative-control log -- crm.py

Module: `/tmp/aep-lab/pilot2/N-neutral-2/crm.py`
Tests: `test_*.py` in `/tmp/aep-lab/pilot2/N-neutral-2`
Spec: `/tmp/aep-lab/specs/crm.md`
Tool: `/tmp/aep-lab/v060/bin/aepkit negcontrol`

A control passes (exit 0) only if the suite fails under the injected break,
the failing output matches `--expect`, and the suite passes again after the
file is restored from the backup.

Guard-removal patches live in `negcontrol/break.py`; the driver that produced
the transcript below is `negcontrol/run_all.py`. Run with:

```sh
python3 /tmp/aep-lab/pilot2/N-neutral-2/negcontrol/run_all.py
```

## Baseline (unbroken module)

```sh
python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"
```

```
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
```

## Guard group: email/name/source validation -- break `email`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py email' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_rejects_email_without_at --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ks2ath2p/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py email
guard removed: email
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_rejects_email_without_at/
E.............................................................................................................FE.EEFFFFFEFE.......
======================================================================
ERROR: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTests.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 36, in test_failed_add_lead_changes_nothing
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        ValueError, lambda: self.crm.add_lead("bad-email", "X", "web", "r1")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 32, in assert_fails_cleanly
    call()
    ~~~~^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 37, in <lambda>
    ValueError, lambda: self.crm.add_lead("bad-email", "X", "web", "r1")
                        ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 104, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 88, in _new_lead_score
    domain = email.split("@")[1]
             ~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_failed_email_validation_creates_nothing (test_validation.EmailValidationTests.test_failed_email_validation_creates_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 72, in test_failed_email_validation_creates_nothing
    self.crm.add_lead("nope", "A", "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 104, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 88, in _new_lead_score
    domain = email.split("@")[1]
             ~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_rejects_blank_email (test_validation.EmailValidationTests.test_rejects_blank_email) (email='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 63, in test_rejects_blank_email
    self.crm.add_lead(bad, "A", "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 104, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 88, in _new_lead_score
    domain = email.split("@")[1]
             ~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_rejects_blank_email (test_validation.EmailValidationTests.test_rejects_blank_email) (email='   ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 63, in test_rejects_blank_email
    self.crm.add_lead(bad, "A", "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 104, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 88, in _new_lead_score
    domain = email.split("@")[1]
             ~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_rejects_email_without_at (test_validation.EmailValidationTests.test_rejects_email_without_at)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 35, in test_rejects_email_without_at
    self.crm.add_lead("alice.example.com", "A", "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 104, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 88, in _new_lead_score
    domain = email.split("@")[1]
             ~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_rejects_empty_local_part (test_validation.EmailValidationTests.test_rejects_empty_local_part) (email='  @example.com  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 45, in test_rejects_empty_local_part
    self.crm.add_lead(bad, "A", "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 103, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead email, existing id L1

======================================================================
FAIL: test_email_checked_before_name (test_validation.EmailValidationTests.test_email_checked_before_name)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 68, in test_email_checked_before_name
    self.assertIn("email", str(caught.exception).lower())
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'email' not found in 'name must be a non-empty string'

======================================================================
FAIL: test_rejects_blank_email (test_validation.EmailValidationTests.test_rejects_blank_email) (email='@')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 62, in test_rejects_blank_email
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_domain_without_dot (test_validation.EmailValidationTests.test_rejects_domain_without_dot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 48, in test_rejects_domain_without_dot
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_dot_as_first_domain_character (test_validation.EmailValidationTests.test_rejects_dot_as_first_domain_character)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 52, in test_rejects_dot_as_first_domain_character
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_dot_as_last_domain_character (test_validation.EmailValidationTests.test_rejects_dot_as_last_domain_character)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 56, in test_rejects_dot_as_last_domain_character
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_email_with_several_ats (test_validation.EmailValidationTests.test_rejects_email_with_several_ats)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 38, in test_rejects_email_with_several_ats
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_empty_local_part (test_validation.EmailValidationTests.test_rejects_empty_local_part) (email='@example.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 44, in test_rejects_empty_local_part
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.006s

FAILED (failures=7, errors=6)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: email/name/source validation -- break `name`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py name' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_rejects_blank_name --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-eio9lme4/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py name
guard removed: name
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_rejects_blank_name/
F........................................................................................................................FEEEEEE...F
======================================================================
ERROR: test_rejects_blank_name (test_validation.NameValidationTests.test_rejects_blank_name) (name='   ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 91, in test_rejects_blank_name
    self.crm.add_lead("a@b.com", bad, "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 111, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead email, existing id L1

======================================================================
ERROR: test_rejects_blank_name (test_validation.NameValidationTests.test_rejects_blank_name) (name='\t\n')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 91, in test_rejects_blank_name
    self.crm.add_lead("a@b.com", bad, "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 111, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead email, existing id L1

======================================================================
ERROR: test_rejects_non_string_name (test_validation.NameValidationTests.test_rejects_non_string_name) (name=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 85, in test_rejects_non_string_name
    self.crm.add_lead("a@b.com", bad, "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 119, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

======================================================================
ERROR: test_rejects_non_string_name (test_validation.NameValidationTests.test_rejects_non_string_name) (name=7)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 85, in test_rejects_non_string_name
    self.crm.add_lead("a@b.com", bad, "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 119, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'int' object has no attribute 'strip'

======================================================================
ERROR: test_rejects_non_string_name (test_validation.NameValidationTests.test_rejects_non_string_name) (name=3.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 85, in test_rejects_non_string_name
    self.crm.add_lead("a@b.com", bad, "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 119, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'float' object has no attribute 'strip'

======================================================================
ERROR: test_rejects_non_string_name (test_validation.NameValidationTests.test_rejects_non_string_name) (name=['Alice'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 85, in test_rejects_non_string_name
    self.crm.add_lead("a@b.com", bad, "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 119, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'list' object has no attribute 'strip'

======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTests.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 39, in test_failed_add_lead_changes_nothing
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        ValueError, lambda: self.crm.add_lead("new@corp.com", "", "web", "r1")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_rejects_blank_name (test_validation.NameValidationTests.test_rejects_blank_name) (name='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 90, in test_rejects_blank_name
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_source_checked_after_name (test_validation.SourceValidationTests.test_source_checked_after_name)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 117, in test_source_checked_after_name
    self.assertIn("name", str(caught.exception).lower())
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'name' not found in 'source must be web, referral or event'

----------------------------------------------------------------------
Ran 127 tests in 0.005s

FAILED (failures=3, errors=6)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: email/name/source validation -- break `source`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py source' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_rejects_unknown_source --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-13hv08s_/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py source
guard removed: source
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_rejects_unknown_source/
E............................................................................................................................EEEEEEE.
======================================================================
ERROR: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTests.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 42, in test_failed_add_lead_changes_nothing
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        ValueError, lambda: self.crm.add_lead("new@corp.com", "X", "billboard", "r1")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 32, in assert_fails_cleanly
    call()
    ~~~~^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 43, in <lambda>
    ValueError, lambda: self.crm.add_lead("new@corp.com", "X", "billboard", "r1")
                        ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 112, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 95, in _new_lead_score
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'billboard'

======================================================================
ERROR: test_rejects_unknown_source (test_validation.SourceValidationTests.test_rejects_unknown_source) (source='ads')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 112, in test_rejects_unknown_source
    self.crm.add_lead("a@b.com", "A", bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 112, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 95, in _new_lead_score
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'ads'

======================================================================
ERROR: test_rejects_unknown_source (test_validation.SourceValidationTests.test_rejects_unknown_source) (source='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 112, in test_rejects_unknown_source
    self.crm.add_lead("a@b.com", "A", bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 112, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 95, in _new_lead_score
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: ''

======================================================================
ERROR: test_rejects_unknown_source (test_validation.SourceValidationTests.test_rejects_unknown_source) (source='Web')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 112, in test_rejects_unknown_source
    self.crm.add_lead("a@b.com", "A", bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 112, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 95, in _new_lead_score
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'Web'

======================================================================
ERROR: test_rejects_unknown_source (test_validation.SourceValidationTests.test_rejects_unknown_source) (source='WEB')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 112, in test_rejects_unknown_source
    self.crm.add_lead("a@b.com", "A", bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 112, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 95, in _new_lead_score
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'WEB'

======================================================================
ERROR: test_rejects_unknown_source (test_validation.SourceValidationTests.test_rejects_unknown_source) (source=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 112, in test_rejects_unknown_source
    self.crm.add_lead("a@b.com", "A", bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 112, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 95, in _new_lead_score
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: None

======================================================================
ERROR: test_rejects_unknown_source (test_validation.SourceValidationTests.test_rejects_unknown_source) (source=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 112, in test_rejects_unknown_source
    self.crm.add_lead("a@b.com", "A", bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 112, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 95, in _new_lead_score
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 3

======================================================================
ERROR: test_rejects_unknown_source (test_validation.SourceValidationTests.test_rejects_unknown_source) (source=['web'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_validation.py", line 112, in test_rejects_unknown_source
    self.crm.add_lead("a@b.com", "A", bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 112, in add_lead
    score = self._new_lead_score(source, normalized)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 95, in _new_lead_score
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 127 tests in 0.005s

FAILED (errors=8)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: duplicate detection -- break `duplicate`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py duplicate' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_duplicate_after_normalization_raises --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fml_zxf9/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py duplicate
guard removed: duplicate
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_duplicate_after_normalization_raises/
F..F............................................FFF.FFF..........................................................................
======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTests.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 45, in test_failed_add_lead_changes_nothing
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        crm.DuplicateLeadError,
        ^^^^^^^^^^^^^^^^^^^^^^^
        lambda: self.crm.add_lead("BASE@corp.com", "Clone", "event", "m1"),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_failed_calls_do_not_consume_ids (test_atomicity.AtomicityTests.test_failed_calls_do_not_consume_ids)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 126, in test_failed_calls_do_not_consume_ids
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        crm.DuplicateLeadError,
        ^^^^^^^^^^^^^^^^^^^^^^^
        lambda: self.crm.add_lead("base@corp.com", "Clone", "web", "r1"),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_after_normalization_raises (test_leads.DuplicateTests.test_duplicate_after_normalization_raises) (email='BOB@CORP.COM')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 23, in test_duplicate_after_normalization_raises
    with self.assertRaises(crm.DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_after_normalization_raises (test_leads.DuplicateTests.test_duplicate_after_normalization_raises) (email='  bob@corp.com  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 23, in test_duplicate_after_normalization_raises
    with self.assertRaises(crm.DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_after_normalization_raises (test_leads.DuplicateTests.test_duplicate_after_normalization_raises) (email='Bob@Corp.Com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 23, in test_duplicate_after_normalization_raises
    with self.assertRaises(crm.DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_does_not_advance_the_id_sequence (test_leads.DuplicateTests.test_duplicate_does_not_advance_the_id_sequence)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 44, in test_duplicate_does_not_advance_the_id_sequence
    with self.assertRaises(crm.DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_error_is_not_a_value_error (test_leads.DuplicateTests.test_duplicate_error_is_not_a_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 29, in test_duplicate_error_is_not_a_value_error
    with self.assertRaises(crm.DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_leaves_state_untouched (test_leads.DuplicateTests.test_duplicate_leaves_state_untouched)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 52, in test_duplicate_leaves_state_untouched
    with self.assertRaises(crm.DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.005s

FAILED (failures=8)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: rep assignment and capacity -- break `capacity`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py capacity' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_capacity_is_respected --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-avh5241q/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py capacity
guard removed: capacity
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_capacity_is_respected/
..F.............................FFF..F.F.....F................................................F................................
======================================================================
FAIL: test_failed_call_does_not_assign_waiting_leads (test_atomicity.AtomicityTests.test_failed_call_does_not_assign_waiting_leads)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 148, in test_failed_call_does_not_assign_waiting_leads
    self.assertIsNone(system.leads[waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_at_capacity_queue_does_not_overflow_capacity (test_leads.AssignmentTests.test_at_capacity_queue_does_not_overflow_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 174, in test_at_capacity_queue_does_not_overflow_capacity
    self.assertEqual(owners, ["r1", "r1", None, None])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ['r1', 'r1', 'r1', 'r1'] != ['r1', 'r1', None, None]

First differing element 2:
'r1'
None

- ['r1', 'r1', 'r1', 'r1']
+ ['r1', 'r1', None, None]

======================================================================
FAIL: test_capacity_is_respected (test_leads.AssignmentTests.test_capacity_is_respected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 110, in test_capacity_is_respected
    self.assertIsNone(system.leads[third]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_lead_without_rep_joins_queue_and_is_assigned_later (test_leads.AssignmentTests.test_lead_without_rep_joins_queue_and_is_assigned_later)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 135, in test_lead_without_rep_joins_queue_and_is_assigned_later
    self.assertIsNone(system.leads[waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_one_assignment_per_freed_slot (test_leads.AssignmentTests.test_one_assignment_per_freed_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 168, in test_one_assignment_per_freed_slot
    self.assertEqual(assigned, [("assign", waiting, "system")])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != [('assign', 'L2', 'system')]

Second list contains 1 additional elements.
First extra element 0:
('assign', 'L2', 'system')

- []
+ [('assign', 'L2', 'system')]

======================================================================
FAIL: test_queue_is_fifo (test_leads.AssignmentTests.test_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 157, in test_queue_is_fifo
    self.assertIsNone(system.leads[second_waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_lead_without_owner_cannot_be_converted (test_leads.ConversionTests.test_lead_without_owner_cannot_be_converted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 288, in test_lead_without_owner_cannot_be_converted
    self.assertIsNone(system.leads[waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_transfer_frees_previous_owner_capacity (test_transfer.SlotReleaseTests.test_transfer_frees_previous_owner_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 106, in test_transfer_frees_previous_owner_capacity
    self.assertEqual(system.leads[blocked]["owner"], "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' != 'r2'
- r1
+ r2


----------------------------------------------------------------------
Ran 127 tests in 0.005s

FAILED (failures=8)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: rep assignment and capacity -- break `lowest_load`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py lowest_load' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_lowest_load_wins --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-hei59uz9/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py lowest_load
guard removed: lowest_load
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_lowest_load_wins/
...................................F......................................................................F....................
======================================================================
FAIL: test_lowest_load_wins (test_leads.AssignmentTests.test_lowest_load_wins)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 90, in test_lowest_load_wins
    self.assertEqual(system.leads[lead_id]["owner"], expected)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' != 'r2'
- r1
+ r2


======================================================================
FAIL: test_target_full_of_leads_is_rejected (test_transfer.TransferRulesTests.test_target_full_of_leads_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 75, in test_target_full_of_leads_is_rejected
    self.assertEqual(system.leads[other]["owner"], "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' != 'r2'
- r1
+ r2


----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: waiting queue -- break `queue_fifo`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py queue_fifo' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_queue_is_fifo --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9q_u61mh/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py queue_fifo
guard removed: queue_fifo
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_queue_is_fifo/
................................F......F.......................................................................................
======================================================================
FAIL: test_at_capacity_queue_does_not_overflow_capacity (test_leads.AssignmentTests.test_at_capacity_queue_does_not_overflow_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 179, in test_at_capacity_queue_does_not_overflow_capacity
    self.assertEqual(system.leads[leads[2]]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_queue_is_fifo (test_leads.AssignmentTests.test_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 156, in test_queue_is_fifo
    self.assertEqual(system.leads[first_waiting]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: waiting queue -- break `queue_capacity`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py queue_capacity' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_at_capacity_queue_does_not_overflow_capacity --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-zxkptb_h/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py queue_capacity
guard removed: queue_capacity
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_at_capacity_queue_does_not_overflow_capacity/
................................F......F.......................................................................................
======================================================================
FAIL: test_at_capacity_queue_does_not_overflow_capacity (test_leads.AssignmentTests.test_at_capacity_queue_does_not_overflow_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 180, in test_at_capacity_queue_does_not_overflow_capacity
    self.assertIsNone(system.leads[leads[3]]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_queue_is_fifo (test_leads.AssignmentTests.test_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 157, in test_queue_is_fifo
    self.assertIsNone(system.leads[second_waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: permission checks -- break `actor`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py actor' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_unknown_actor_rejected_everywhere --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-yad_hbum/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py actor
guard removed: actor
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_unknown_actor_rejected_everywhere/
F.................E.......................................................EEFEEEEE..............E...................................
======================================================================
ERROR: test_other_rep_cannot_discount (test_discount.DiscountPermissionTests.test_other_rep_cannot_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 58, in test_other_rep_cannot_discount
    self.crm.discount(self.opp, 5, "r2")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 200, in discount
    if opp["owner"] != actor and not self._is_manager(actor):
                                     ~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 41, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'r2'

======================================================================
ERROR: test_unknown_actor_does_not_log (test_permissions.UnknownActorTests.test_unknown_actor_does_not_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 48, in test_unknown_actor_does_not_log
    self.crm.advance(self.opp, "proposal", "ghost")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 178, in advance
    if opp["owner"] != actor and not self._is_manager(actor):
                                     ~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 41, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_is_checked_before_other_arguments (test_permissions.UnknownActorTests.test_unknown_actor_is_checked_before_other_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 35, in test_unknown_actor_is_checked_before_other_arguments
    self.crm.add_lead(None, None, "nonsense", "ghost")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 103, in add_lead
    normalized = self._normalize_email(email)
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 82, in _normalize_email
    raise ValueError("email must be a string")
ValueError: email must be a string

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_permissions.UnknownActorTests.test_unknown_actor_rejected_everywhere) (call=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 31, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 22, in <lambda>
    lambda: self.crm.qualify(self.lead, "ghost"),
            ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 135, in qualify
    if lead["owner"] != actor and not self._is_manager(actor):
                                      ~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 41, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_permissions.UnknownActorTests.test_unknown_actor_rejected_everywhere) (call=2)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 31, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 23, in <lambda>
    lambda: self.crm.convert(self.lead, 10, "ghost"),
            ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 151, in convert
    if lead["owner"] != actor and not self._is_manager(actor):
                                      ~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 41, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_permissions.UnknownActorTests.test_unknown_actor_rejected_everywhere) (call=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 31, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 24, in <lambda>
    lambda: self.crm.advance(self.opp, "proposal", "ghost"),
            ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 178, in advance
    if opp["owner"] != actor and not self._is_manager(actor):
                                     ~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 41, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_permissions.UnknownActorTests.test_unknown_actor_rejected_everywhere) (call=4)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 31, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 25, in <lambda>
    lambda: self.crm.discount(self.opp, 5, "ghost"),
            ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 200, in discount
    if opp["owner"] != actor and not self._is_manager(actor):
                                     ~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 41, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_permissions.UnknownActorTests.test_unknown_actor_rejected_everywhere) (call=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 31, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 26, in <lambda>
    lambda: self.crm.transfer(self.opp, "r2", "ghost"),
            ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 217, in transfer
    if not self._is_manager(actor):
           ~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 41, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_permission_is_checked_before_final_state (test_stages.TransitionTests.test_permission_is_checked_before_final_state)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_stages.py", line 86, in test_permission_is_checked_before_final_state
    self.crm.advance(self.opp, "proposal", "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 178, in advance
    if opp["owner"] != actor and not self._is_manager(actor):
                                     ~~~~~~~~~~~~~~~~^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 41, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'r2'

======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.AtomicityTests.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 49, in test_failed_add_lead_changes_nothing
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        PermissionError, lambda: self.crm.add_lead("new@corp.com", "X", "web", "ghost")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_actor_rejected_everywhere (test_permissions.UnknownActorTests.test_unknown_actor_rejected_everywhere) (call=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 30, in test_unknown_actor_rejected_everywhere
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.007s

FAILED (failures=2, errors=9)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: permission checks -- break `ownership`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py ownership' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_other_rep_cannot_qualify --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3xio95x2/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py ownership
guard removed: ownership
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_other_rep_cannot_qualify/
.......E...............................................................F.F.....................................................
======================================================================
ERROR: test_failed_qualify_changes_nothing (test_atomicity.AtomicityTests.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 62, in test_failed_qualify_changes_nothing
    self.assert_fails_cleanly(PermissionError, lambda: self.crm.qualify(low, other))
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 32, in assert_fails_cleanly
    call()
    ~~~~^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 62, in <lambda>
    self.assert_fails_cleanly(PermissionError, lambda: self.crm.qualify(low, other))
                                                       ~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 141, in qualify
    raise ValueError("lead score below 30")
ValueError: lead score below 30

======================================================================
FAIL: test_other_rep_cannot_qualify (test_permissions.OwnershipTests.test_other_rep_cannot_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 57, in test_other_rep_cannot_qualify
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_ownership_check_precedes_status_check (test_permissions.OwnershipTests.test_ownership_check_precedes_status_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 111, in test_ownership_check_precedes_status_check
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: permission checks -- break `manager_only`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py manager_only' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_transfer_requires_manager --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-pj7l8fon/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py manager_only
guard removed: manager_only
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_transfer_requires_manager/
........F.........................................................F...................................FEFE.......................
======================================================================
ERROR: test_non_manager_cannot_transfer (test_transfer.TransferRulesTests.test_non_manager_cannot_transfer) (actor='r2')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 36, in test_non_manager_cannot_transfer
    self.crm.transfer(self.opp, "r2", actor)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 226, in transfer
    raise ValueError("new owner is already the owner")
ValueError: new owner is already the owner

======================================================================
ERROR: test_permission_precedes_target_validation (test_transfer.TransferRulesTests.test_permission_precedes_target_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 41, in test_permission_precedes_target_validation
    self.crm.transfer(self.opp, "nobody", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 222, in transfer
    raise ValueError("new owner must be a known rep")
ValueError: new owner must be a known rep

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.AtomicityTests.test_failed_transfer_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 114, in test_failed_transfer_changes_nothing
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        PermissionError, lambda: self.crm.transfer(self.opp, "r2", "r1")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_transfer_requires_manager (test_permissions.ManagerOnlyTests.test_transfer_requires_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_permissions.py", line 121, in test_transfer_requires_manager
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_manager_cannot_transfer (test_transfer.TransferRulesTests.test_non_manager_cannot_transfer) (actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 35, in test_non_manager_cannot_transfer
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_manager_cannot_transfer (test_transfer.TransferRulesTests.test_non_manager_cannot_transfer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 37, in test_non_manager_cannot_transfer
    self.assertEqual(self.crm.opps[self.opp]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


----------------------------------------------------------------------
Ran 127 tests in 0.005s

FAILED (failures=4, errors=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: qualification score threshold -- break `score`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py score' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_score_below_threshold_is_rejected --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fwngfuyz/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py score
guard removed: score
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_score_below_threshold_is_rejected/
.......F.............................................F.FFF.F.....................................................................
======================================================================
FAIL: test_failed_qualify_changes_nothing (test_atomicity.AtomicityTests.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 57, in test_failed_qualify_changes_nothing
    self.assert_fails_cleanly(ValueError, lambda: self.crm.qualify(low, owner))
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_qualification_logs_nothing (test_leads.QualificationTests.test_failed_qualification_logs_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 222, in test_failed_qualification_logs_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_is_rejected (test_leads.QualificationTests.test_score_below_threshold_is_rejected) (index=0, source='web')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 197, in test_score_below_threshold_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_is_rejected (test_leads.QualificationTests.test_score_below_threshold_is_rejected) (index=1, source='event')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 197, in test_score_below_threshold_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_is_rejected (test_leads.QualificationTests.test_score_below_threshold_is_rejected) (index=2, source='web')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 197, in test_score_below_threshold_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_ten_points_cannot_pass (test_leads.QualificationTests.test_score_ten_points_cannot_pass)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_leads.py", line 216, in test_score_ten_points_cannot_pass
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=6)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: stage-transition rules -- break `transition`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py transition' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_skip_ahead_is_rejected --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-sf6qthmc/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py transition
guard removed: transition
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_skip_ahead_is_rejected/
.FF................................................................................F.F..E...FF..................................
======================================================================
ERROR: test_invalid_transition_happens_before_big_deal_check (test_stages.TransitionTests.test_invalid_transition_happens_before_big_deal_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_stages.py", line 93, in test_invalid_transition_happens_before_big_deal_check
    self.crm.advance(self.opp, "negotiation", "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 188, in advance
    raise PermissionError("manager approval required for deals over 50000")
PermissionError: manager approval required for deals over 50000

======================================================================
FAIL: test_failed_advance_changes_nothing (test_atomicity.AtomicityTests.test_failed_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 80, in test_failed_advance_changes_nothing
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        ValueError, lambda: self.crm.advance(self.opp, "won", "r1")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_call_does_not_assign_waiting_leads (test_atomicity.AtomicityTests.test_failed_call_does_not_assign_waiting_leads)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 145, in test_failed_call_does_not_assign_waiting_leads
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_backwards_transition_is_rejected (test_stages.TransitionTests.test_backwards_transition_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_stages.py", line 57, in test_backwards_transition_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_transition_logs_nothing (test_stages.TransitionTests.test_failed_transition_logs_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_stages.py", line 97, in test_failed_transition_logs_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_skip_ahead_is_rejected (test_stages.TransitionTests.test_skip_ahead_is_rejected) (target='negotiation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_stages.py", line 37, in test_skip_ahead_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_skip_ahead_is_rejected (test_stages.TransitionTests.test_skip_ahead_is_rejected) (target='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_stages.py", line 37, in test_skip_ahead_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.005s

FAILED (failures=6, errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: big-deal approval -- break `bigdeal`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py bigdeal' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_rep_needs_manager_above_50000 --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-uwn3d5aj/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py bigdeal
guard removed: bigdeal
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_rep_needs_manager_above_50000/
..................................................................................F............................................
======================================================================
FAIL: test_rep_needs_manager_above_50000 (test_stages.BigDealTests.test_rep_needs_manager_above_50000)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_stages.py", line 114, in test_rep_needs_manager_above_50000
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: discount limits -- break `discount_range`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py discount_range' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_pct_must_be_int_in_range --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-povxvu_m/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py discount_range
guard removed: discount_range
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_pct_must_be_int_in_range/
.....F...............FFEEF.........................................................................................................
======================================================================
ERROR: test_pct_must_be_int_in_range (test_discount.DiscountRangeTests.test_pct_must_be_int_in_range) (pct=31)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 29, in test_pct_must_be_int_in_range
    self.crm.discount(self.opp, bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 206, in discount
    raise PermissionError("reps may discount at most 10 percent")
PermissionError: reps may discount at most 10 percent

======================================================================
ERROR: test_pct_must_be_int_in_range (test_discount.DiscountRangeTests.test_pct_must_be_int_in_range) (pct=100)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 29, in test_pct_must_be_int_in_range
    self.crm.discount(self.opp, bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 206, in discount
    raise PermissionError("reps may discount at most 10 percent")
PermissionError: reps may discount at most 10 percent

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.AtomicityTests.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 95, in test_failed_discount_changes_nothing
    self.assert_fails_cleanly(ValueError, lambda: self.crm.discount(self.opp, 0, "r1"))
    ~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_int_in_range (test_discount.DiscountRangeTests.test_pct_must_be_int_in_range) (pct=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 28, in test_pct_must_be_int_in_range
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_int_in_range (test_discount.DiscountRangeTests.test_pct_must_be_int_in_range) (pct=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 28, in test_pct_must_be_int_in_range
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_int_in_range (test_discount.DiscountRangeTests.test_pct_must_be_int_in_range)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 30, in test_pct_must_be_int_in_range
    self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 10100 != 10000

----------------------------------------------------------------------
Ran 127 tests in 0.005s

FAILED (failures=4, errors=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.004s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: discount limits -- break `discount_ceiling`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py discount_ceiling' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_rep_ceiling_is_ten --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-p_0n36sp/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py discount_ceiling
guard removed: discount_ceiling
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_rep_ceiling_is_ten/
.....F.............FE..........................................................................................................
======================================================================
ERROR: test_rep_ceiling_precedes_cumulative_floor (test_discount.DiscountPermissionTests.test_rep_ceiling_precedes_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 69, in test_rep_ceiling_precedes_cumulative_floor
    system.discount(opp, 11, "r1")
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/crm.py", line 209, in discount
    raise ValueError("cumulative discount would exceed 30 percent")
ValueError: cumulative discount would exceed 30 percent

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.AtomicityTests.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 97, in test_failed_discount_changes_nothing
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        PermissionError, lambda: self.crm.discount(self.opp, 11, "r1")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_rep_ceiling_is_ten (test_discount.DiscountPermissionTests.test_rep_ceiling_is_ten)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 52, in test_rep_ceiling_is_ten
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: cumulative discount floor -- break `discount_floor`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py discount_floor' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_beyond_thirty_percent_of_original_is_rejected --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bpf5x2om/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py discount_floor
guard removed: discount_floor
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_beyond_thirty_percent_of_original_is_rejected/
......F..F.FFFF................................................................................................................
======================================================================
FAIL: test_failed_discount_does_not_move_amount_below_the_floor (test_atomicity.AtomicityTests.test_failed_discount_does_not_move_amount_below_the_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 108, in test_failed_discount_does_not_move_amount_below_the_floor
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_beyond_thirty_percent_of_original_is_rejected (test_discount.CumulativeFloorTests.test_beyond_thirty_percent_of_original_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 101, in test_beyond_thirty_percent_of_original_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_exact_floor_passes (test_discount.CumulativeFloorTests.test_exact_floor_passes)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 137, in test_exact_floor_passes
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_discount_logs_nothing_and_keeps_amount (test_discount.CumulativeFloorTests.test_failed_discount_logs_nothing_and_keeps_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 148, in test_failed_discount_logs_nothing_and_keeps_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_floor_is_inclusive_at_exactly_seventy_percent (test_discount.CumulativeFloorTests.test_floor_is_inclusive_at_exactly_seventy_percent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 123, in test_floor_is_inclusive_at_exactly_seventy_percent
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_floor_uses_original_amount_not_running_amount (test_discount.CumulativeFloorTests.test_floor_uses_original_amount_not_running_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 111, in test_floor_uses_original_amount_not_running_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=6)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: atomicity -- break `atomicity`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py atomicity' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_failed_discount_does_not_move_amount_below_the_floor --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ewmoh_7i/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py atomicity
guard removed: atomicity
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_failed_discount_does_not_move_amount_below_the_floor/
......F..F.FFFF................................................................................................................
======================================================================
FAIL: test_failed_discount_does_not_move_amount_below_the_floor (test_atomicity.AtomicityTests.test_failed_discount_does_not_move_amount_below_the_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 110, in test_failed_discount_does_not_move_amount_below_the_floor
    self.assertEqual(snapshot(self.crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[207 chars]nt': 693, 'original_amount': 1000, 'stage': 'p[117 chars]1')]} != {'lea[207 chars]nt': 700, 'original_amount': 1000, 'stage': 'p[117 chars]1')]}
Diff is 739 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_beyond_thirty_percent_of_original_is_rejected (test_discount.CumulativeFloorTests.test_beyond_thirty_percent_of_original_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 103, in test_beyond_thirty_percent_of_original_is_rejected
    self.assertEqual(system.opps[opp]["amount"], 700)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 693 != 700

======================================================================
FAIL: test_exact_floor_passes (test_discount.CumulativeFloorTests.test_exact_floor_passes)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 139, in test_exact_floor_passes
    self.assertEqual(system.opps[opp]["amount"], 705)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 697 != 705

======================================================================
FAIL: test_failed_discount_logs_nothing_and_keeps_amount (test_discount.CumulativeFloorTests.test_failed_discount_logs_nothing_and_keeps_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 151, in test_failed_discount_logs_nothing_and_keeps_amount
    self.assertEqual(system.opps[opp]["amount"], 700)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 665 != 700

======================================================================
FAIL: test_floor_is_inclusive_at_exactly_seventy_percent (test_discount.CumulativeFloorTests.test_floor_is_inclusive_at_exactly_seventy_percent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 125, in test_floor_is_inclusive_at_exactly_seventy_percent
    self.assertEqual(system.opps[opp]["amount"], 750)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 697 != 750

======================================================================
FAIL: test_floor_uses_original_amount_not_running_amount (test_discount.CumulativeFloorTests.test_floor_uses_original_amount_not_running_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_discount.py", line 113, in test_floor_uses_original_amount_not_running_amount
    self.assertEqual(system.opps[opp]["amount"], 729)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 692 != 729

----------------------------------------------------------------------
Ran 127 tests in 0.005s

FAILED (failures=6)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: transfer rules -- break `transfer_target_role`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py transfer_target_role' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_manager_cannot_be_target --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8sflcup0/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py transfer_target_role
guard removed: transfer_target_role
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_manager_cannot_be_target/
....................................................................................................F..........................
======================================================================
FAIL: test_manager_cannot_be_target (test_transfer.TransferRulesTests.test_manager_cannot_be_target)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 51, in test_manager_cannot_be_target
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.004s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: transfer rules -- break `transfer_same_owner`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py transfer_same_owner' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_same_owner_is_rejected --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8kx0nbdw/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py transfer_same_owner
guard removed: transfer_same_owner
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_same_owner_is_rejected/
........F.........................................................................................F.....F......................
======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.AtomicityTests.test_failed_transfer_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 120, in test_failed_transfer_changes_nothing
    self.assert_fails_cleanly(
    ~~~~~~~~~~~~~~~~~~~~~~~~~^
        ValueError, lambda: self.crm.transfer(self.opp, "r1", "m1")
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_atomicity.py", line 31, in assert_fails_cleanly
    with self.assertRaises(exception_type):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_transfer_logs_nothing (test_transfer.TransferRulesTests.test_failed_transfer_logs_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 92, in test_failed_transfer_logs_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_same_owner_is_rejected (test_transfer.TransferRulesTests.test_same_owner_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 56, in test_same_owner_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=3)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.004s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)

## Guard group: transfer rules -- break `transfer_capacity`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py transfer_capacity' --test-cmd 'python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"' --expect test_target_at_capacity_is_rejected --timeout 20
```

Verbatim output (exit 0):

```
$ backed up /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-s6alb2z7/crm.py
$ python3 /private/tmp/aep-lab/pilot2/N-neutral-2/negcontrol/break.py transfer_capacity
guard removed: transfer_capacity
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect FAILURE matching /test_target_at_capacity_is_rejected/
.........................................................................................................FF....................
======================================================================
FAIL: test_target_at_capacity_is_rejected (test_transfer.TransferRulesTests.test_target_at_capacity_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 62, in test_target_at_capacity_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_target_full_of_leads_is_rejected (test_transfer.TransferRulesTests.test_target_full_of_leads_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/N-neutral-2/test_transfer.py", line 76, in test_target_full_of_leads_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 127 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/N-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /private/tmp/aep-lab/pilot2/N-neutral-2 -p "test*.py"   # expect SUCCESS
...............................................................................................................................
----------------------------------------------------------------------
Ran 127 tests in 0.004s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Verdict: PASS (exit 0)
