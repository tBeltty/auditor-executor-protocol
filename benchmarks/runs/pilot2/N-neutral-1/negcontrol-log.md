# Negative-control log

Every control below runs `/tmp/aep-lab/v060/bin/aepkit negcontrol`, which backs up
`crm.py`, applies one break, runs the test suite, requires the output to match
`--expect`, restores the file byte-for-byte, and re-runs the suite.
A control passes (exit 0) only when the tests fail under the break and pass after restore.

## 1. email validation

Case: email: every sub-rule disabled at once

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_str email_at email_local email_dot" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_email_ --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ssciyv43/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_str email_at email_local email_dot

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_email_/
..........F..EFFF............................................................
======================================================================
ERROR: test_email_not_str (test_crm.EmailValidationTest.test_email_not_str)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 30, in test_email_not_str
    crm.add_lead(bad, "Ada", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 125, in add_lead
    normalized, domain = self._validate_email(email)
                         ~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 111, in _validate_email
    normalized = email.strip().lower()
                 ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

======================================================================
FAIL: test_lead_ids_count_successful_creations_only (test_crm.DuplicateLeadTest.test_lead_ids_count_successful_creations_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 137, in test_lead_ids_count_successful_creations_only
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_requires_exactly_one_at (test_crm.EmailValidationTest.test_email_requires_exactly_one_at)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 37, in test_email_requires_exactly_one_at
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_requires_inner_dot_in_domain (test_crm.EmailValidationTest.test_email_requires_inner_dot_in_domain)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 51, in test_email_requires_inner_dot_in_domain
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_requires_local_part (test_crm.EmailValidationTest.test_email_requires_local_part)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 44, in test_email_requires_local_part
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.004s

FAILED (failures=4, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 2. email validation

Case: email: exactly-one-@ rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_at" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_email_requires_exactly_one_at --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-j5hfp1lt/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_at

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_email_requires_exactly_one_at/
..............F..............................................................
======================================================================
FAIL: test_email_requires_exactly_one_at (test_crm.EmailValidationTest.test_email_requires_exactly_one_at)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 37, in test_email_requires_exactly_one_at
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 3. email validation

Case: email: non-empty local part rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_local" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_email_requires_local_part --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ae009xk9/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_local

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_email_requires_local_part/
................F............................................................
======================================================================
FAIL: test_email_requires_local_part (test_crm.EmailValidationTest.test_email_requires_local_part)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 44, in test_email_requires_local_part
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 4. email validation

Case: email: inner-dot-in-domain rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_dot" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_email_requires_inner_dot_in_domain --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-dyzjalx9/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_dot

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_email_requires_inner_dot_in_domain/
...............F.............................................................
======================================================================
FAIL: test_email_requires_inner_dot_in_domain (test_crm.EmailValidationTest.test_email_requires_inner_dot_in_domain)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 51, in test_email_requires_inner_dot_in_domain
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 5. email validation

Case: email: str-type rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_str" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_email_not_str --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1ov85z5o/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill email_str

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_email_not_str/
.............E...............................................................
======================================================================
ERROR: test_email_not_str (test_crm.EmailValidationTest.test_email_not_str)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 30, in test_email_not_str
    crm.add_lead(bad, "Ada", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 125, in add_lead
    normalized, domain = self._validate_email(email)
                         ~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 111, in _validate_email
    normalized = email.strip().lower()
                 ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 6. name validation

Case: name: str + non-empty rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill name_str" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_name_must_be_str_and_non_empty --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-c9u1qo1h/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill name_str

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_name_must_be_str_and_non_empty/
...................E.........................................................
======================================================================
ERROR: test_name_must_be_str_and_non_empty (test_crm.NameValidationTest.test_name_must_be_str_and_non_empty)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 81, in test_name_must_be_str_and_non_empty
    crm.add_lead("a@example.com", bad, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 145, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 7. source validation

Case: source: allow-list removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill source_valid" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_source_must_be_known --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1p8ekny8/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill source_valid

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_source_must_be_known/
..............................E..............................................
======================================================================
ERROR: test_source_must_be_known (test_crm.SourceValidationTest.test_source_must_be_known)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 96, in test_source_must_be_known
    crm.add_lead("a@example.com", "Ada", bad, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 134, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'LinkedIn'

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 8. duplicate detection

Case: duplicate check removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill dup" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_duplicate --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9kxsfnjo/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill dup

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_duplicate/
.......FFFF................................F.................................
======================================================================
FAIL: test_duplicate_failure_changes_nothing (test_crm.DuplicateLeadTest.test_duplicate_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 128, in test_duplicate_failure_changes_nothing
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_raises_with_existing_id (test_crm.DuplicateLeadTest.test_duplicate_raises_with_existing_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 111, in test_duplicate_raises_with_existing_id
    with self.assertRaises(DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_uses_normalized_email (test_crm.DuplicateLeadTest.test_duplicate_uses_normalized_email)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 119, in test_duplicate_uses_normalized_email
    with self.assertRaises(DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_lead_ids_count_successful_creations_only (test_crm.DuplicateLeadTest.test_lead_ids_count_successful_creations_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 135, in test_lead_ids_count_successful_creations_only
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_atomic_add_lead_failure_leaves_queue_untouched (test_crm_ops.AtomicityTest.test_atomic_add_lead_failure_leaves_queue_untouched)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 503, in test_atomic_add_lead_failure_leaves_queue_untouched
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.004s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 9. rep assignment / capacity / waiting queue

Case: capacity limit removed when picking a rep

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill assign_capacity" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_capacity_full_sends_lead_to_waiting_queue --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-d0o9e9le/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill assign_capacity

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_capacity_full_sends_lead_to_waiting_queue/
FEFE.FF.............E.EE.EEE...EE.EEEEEEEEE.EEEEEE.EE...EEEEEEEEE.EEEEEEEFE.E
======================================================================
ERROR: test_drain_stops_at_capacity (test_crm.AssignmentTest.test_drain_stops_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 235, in test_drain_stops_at_capacity
    crm.qualify(first, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_load_counts_new_and_qualified_leads (test_crm.AssignmentTest.test_load_counts_new_and_qualified_leads)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 249, in test_load_counts_new_and_qualified_leads
    crm.qualify(first, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_manager_can_act (test_crm.PermissionTest.test_manager_can_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 317, in test_manager_can_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_non_owner_rep_cannot_act (test_crm.PermissionTest.test_non_owner_rep_cannot_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 295, in test_non_owner_rep_cannot_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_owner_can_act (test_crm.PermissionTest.test_owner_can_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 310, in test_owner_can_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_crm.PermissionTest.test_unknown_actor_rejected_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 266, in test_unknown_actor_rejected_everywhere
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_score_at_or_above_threshold_qualifies (test_crm.ScoreTest.test_score_at_or_above_threshold_qualifies)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 171, in test_score_at_or_above_threshold_qualifies
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_score_below_threshold_cannot_qualify (test_crm.ScoreTest.test_score_below_threshold_cannot_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 163, in test_score_below_threshold_cannot_qualify
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_advance_full_path_logs (test_crm_ops.AdvanceTest.test_advance_full_path_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 186, in test_advance_full_path_logs
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_advance_rejects_final_opportunity (test_crm_ops.AdvanceTest.test_advance_rejects_final_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 148, in test_advance_rejects_final_opportunity
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_advance_requires_immediate_next_stage (test_crm_ops.AdvanceTest.test_advance_requires_immediate_next_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 161, in test_advance_requires_immediate_next_stage
    first = make_opp(crm, 1000, "a@example.com")
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_advance_requires_permission (test_crm_ops.AdvanceTest.test_advance_requires_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 139, in test_advance_requires_permission
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_advance_stage_name_validated_before_permission (test_crm_ops.AdvanceTest.test_advance_stage_name_validated_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 129, in test_advance_stage_name_validated_before_permission
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_advance_to_lost_from_any_open_stage (test_crm_ops.AdvanceTest.test_advance_to_lost_from_any_open_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 175, in test_advance_to_lost_from_any_open_stage
    first = make_opp(crm, 1000, "a@example.com")
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_big_deal_check_follows_stage_order (test_crm_ops.AdvanceTest.test_big_deal_check_follows_stage_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 222, in test_big_deal_check_follows_stage_order
    opp = make_opp(crm, 60000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_big_deal_denied_only_at_negotiation (test_crm_ops.AdvanceTest.test_big_deal_denied_only_at_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 214, in test_big_deal_denied_only_at_negotiation
    opp = make_opp(crm, 60000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_big_deal_requires_manager (test_crm_ops.AdvanceTest.test_big_deal_requires_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 195, in test_big_deal_requires_manager
    opp = make_opp(crm, 50001)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_big_deal_threshold_is_inclusive (test_crm_ops.AdvanceTest.test_big_deal_threshold_is_inclusive)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 207, in test_big_deal_threshold_is_inclusive
    opp = make_opp(crm, 50000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_big_deal_uses_current_amount (test_crm_ops.AdvanceTest.test_big_deal_uses_current_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 230, in test_big_deal_uses_current_amount
    opp = make_opp(crm, 60000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_atomic_advance_bigdeal (test_crm_ops.AtomicityTest.test_atomic_advance_bigdeal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 454, in test_atomic_advance_bigdeal
    opp = make_opp(crm, 60000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_atomic_discount_failure (test_crm_ops.AtomicityTest.test_atomic_discount_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 464, in test_atomic_discount_failure
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_atomic_discount_floor_failure (test_crm_ops.AtomicityTest.test_atomic_discount_floor_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 475, in test_atomic_discount_floor_failure
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_atomic_log_qualify (test_crm_ops.AtomicityTest.test_atomic_log_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 439, in test_atomic_log_qualify
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_atomic_state_convert (test_crm_ops.AtomicityTest.test_atomic_state_convert)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 448, in test_atomic_state_convert
    crm.convert(lead_id, 1000, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_atomic_transfer_failure (test_crm_ops.AtomicityTest.test_atomic_transfer_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 485, in test_atomic_transfer_failure
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_convert_builds_opportunity (test_crm_ops.ConvertTest.test_convert_builds_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 99, in test_convert_builds_opportunity
    opp_id = crm.convert(lead_id, 2500, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_convert_ids_increment (test_crm_ops.ConvertTest.test_convert_ids_increment)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 116, in test_convert_ids_increment
    first = crm.convert(qualified(crm, "a@example.com"), 100, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_convert_requires_qualified_status (test_crm_ops.ConvertTest.test_convert_requires_qualified_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 80, in test_convert_requires_qualified_status
    crm.convert(lead_id, 1000, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_discount_cumulative_floor (test_crm_ops.DiscountTest.test_discount_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 287, in test_discount_cumulative_floor
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_discount_floor_tracks_original_amount (test_crm_ops.DiscountTest.test_discount_floor_tracks_original_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 307, in test_discount_floor_tracks_original_amount
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_discount_keeps_original_amount (test_crm_ops.DiscountTest.test_discount_keeps_original_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 299, in test_discount_keeps_original_amount
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_discount_manager_may_use_full_range (test_crm_ops.DiscountTest.test_discount_manager_may_use_full_range)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 281, in test_discount_manager_may_use_full_range
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_discount_pct_validation (test_crm_ops.DiscountTest.test_discount_pct_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 241, in test_discount_pct_validation
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_discount_rejects_final_stage (test_crm_ops.DiscountTest.test_discount_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 259, in test_discount_rejects_final_stage
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_discount_rep_limit_is_ten (test_crm_ops.DiscountTest.test_discount_rep_limit_is_ten)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 271, in test_discount_rep_limit_is_ten
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_discount_requires_permission (test_crm_ops.DiscountTest.test_discount_requires_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 251, in test_discount_requires_permission
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_forecast_mixed_pipeline (test_crm_ops.ForecastTest.test_forecast_mixed_pipeline)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 412, in test_forecast_mixed_pipeline
    prospect = make_opp(crm, 1000, "a@example.com")
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_forecast_uses_current_amount (test_crm_ops.ForecastTest.test_forecast_uses_current_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 427, in test_forecast_uses_current_amount
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_transfer_is_manager_only (test_crm_ops.TransferTest.test_transfer_is_manager_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 324, in test_transfer_is_manager_only
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_transfer_manager_check_precedes_target_check (test_crm_ops.TransferTest.test_transfer_manager_check_precedes_target_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 333, in test_transfer_manager_check_precedes_target_check
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_transfer_moves_owner_and_logs (test_crm_ops.TransferTest.test_transfer_moves_owner_and_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 388, in test_transfer_moves_owner_and_logs
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_transfer_rejects_final_stage (test_crm_ops.TransferTest.test_transfer_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 352, in test_transfer_rejects_final_stage
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_transfer_rejects_same_owner (test_crm_ops.TransferTest.test_transfer_rejects_same_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 364, in test_transfer_rejects_same_owner
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_transfer_releases_previous_owner_load (test_crm_ops.TransferTest.test_transfer_releases_previous_owner_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 399, in test_transfer_releases_previous_owner_load
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
ERROR: test_transfer_target_must_be_known_rep (test_crm_ops.TransferTest.test_transfer_target_must_be_known_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 342, in test_transfer_target_must_be_known_rep
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 182, in convert
    raise ValueError("lead %s has no owner" % (lead_id,))
ValueError: lead L1 has no owner

======================================================================
FAIL: test_capacity_full_sends_lead_to_waiting_queue (test_crm.AssignmentTest.test_capacity_full_sends_lead_to_waiting_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 193, in test_capacity_full_sends_lead_to_waiting_queue
    self.assertEqual(crm.leads[first]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_load_balancing_picks_lowest_load (test_crm.AssignmentTest.test_load_balancing_picks_lowest_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 184, in test_load_balancing_picks_lowest_load
    self.assertEqual(owners, ["r1", "r2", "r3", "r1"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [None, None, None, None] != ['r1', 'r2', 'r3', 'r1']

First differing element 0:
None
'r1'

- [None, None, None, None]
+ ['r1', 'r2', 'r3', 'r1']

======================================================================
FAIL: test_tie_break_prefers_smallest_id (test_crm.AssignmentTest.test_tie_break_prefers_smallest_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 179, in test_tie_break_prefers_smallest_id
    self.assertEqual(crm.leads[lead_id]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_waiting_queue_is_fifo_on_freed_slot (test_crm.AssignmentTest.test_waiting_queue_is_fifo_on_freed_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 214, in test_waiting_queue_is_fifo_on_freed_slot
    self.assertEqual([crm.leads[k]["owner"] for k in (first, second, third, fourth)],
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     ["r1", "r1", None, None])
                     ^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [None, None, None, None] != ['r1', 'r1', None, None]

First differing element 0:
None
'r1'

- [None, None, None, None]
+ ['r1', 'r1', None, None]

======================================================================
FAIL: test_transfer_rejects_target_at_capacity (test_crm_ops.TransferTest.test_transfer_rejects_target_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 378, in test_transfer_rejects_target_at_capacity
    self.assertEqual(crm.leads[occupied]["owner"], "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r2'

----------------------------------------------------------------------
Ran 77 tests in 0.009s

FAILED (failures=5, errors=45)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 10. rep assignment / capacity / waiting queue

Case: tie-break flipped to largest id

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py sub assign_tie 'if best is None or load <= best[0]:'" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_tie_break_prefers_smallest_id --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-oo_tl_pq/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py sub assign_tie 'if best is None or load <= best[0]:'

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_tie_break_prefers_smallest_id/
..F..F..............E.EE.EEE...EE.....EEEEE.E..EEF.E....EE.E..EE...EF..EFFF..
======================================================================
ERROR: test_manager_can_act (test_crm.PermissionTest.test_manager_can_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 317, in test_manager_can_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_non_owner_rep_cannot_act (test_crm.PermissionTest.test_non_owner_rep_cannot_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 295, in test_non_owner_rep_cannot_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_owner_can_act (test_crm.PermissionTest.test_owner_can_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 310, in test_owner_can_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_crm.PermissionTest.test_unknown_actor_rejected_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 266, in test_unknown_actor_rejected_everywhere
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_score_at_or_above_threshold_qualifies (test_crm.ScoreTest.test_score_at_or_above_threshold_qualifies)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 171, in test_score_at_or_above_threshold_qualifies
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_score_below_threshold_cannot_qualify (test_crm.ScoreTest.test_score_below_threshold_cannot_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 163, in test_score_below_threshold_cannot_qualify
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_advance_full_path_logs (test_crm_ops.AdvanceTest.test_advance_full_path_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 188, in test_advance_full_path_logs
    crm.advance(opp, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_advance_rejects_final_opportunity (test_crm_ops.AdvanceTest.test_advance_rejects_final_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 149, in test_advance_rejects_final_opportunity
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_big_deal_check_follows_stage_order (test_crm_ops.AdvanceTest.test_big_deal_check_follows_stage_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 225, in test_big_deal_check_follows_stage_order
    crm.advance(opp, "negotiation", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_big_deal_denied_only_at_negotiation (test_crm_ops.AdvanceTest.test_big_deal_denied_only_at_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 215, in test_big_deal_denied_only_at_negotiation
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_big_deal_requires_manager (test_crm_ops.AdvanceTest.test_big_deal_requires_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 196, in test_big_deal_requires_manager
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_big_deal_threshold_is_inclusive (test_crm_ops.AdvanceTest.test_big_deal_threshold_is_inclusive)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 208, in test_big_deal_threshold_is_inclusive
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_big_deal_uses_current_amount (test_crm_ops.AdvanceTest.test_big_deal_uses_current_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 231, in test_big_deal_uses_current_amount
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_atomic_advance_bigdeal (test_crm_ops.AtomicityTest.test_atomic_advance_bigdeal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 455, in test_atomic_advance_bigdeal
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_atomic_log_qualify (test_crm_ops.AtomicityTest.test_atomic_log_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 439, in test_atomic_log_qualify
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_atomic_state_convert (test_crm_ops.AtomicityTest.test_atomic_state_convert)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 448, in test_atomic_state_convert
    crm.convert(lead_id, 1000, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_convert_builds_opportunity (test_crm_ops.ConvertTest.test_convert_builds_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 99, in test_convert_builds_opportunity
    opp_id = crm.convert(lead_id, 2500, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_convert_requires_qualified_status (test_crm_ops.ConvertTest.test_convert_requires_qualified_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 80, in test_convert_requires_qualified_status
    crm.convert(lead_id, 1000, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_discount_cumulative_floor (test_crm_ops.DiscountTest.test_discount_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 289, in test_discount_cumulative_floor
    crm.discount(opp, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 226, in discount
    raise PermissionError("actor %r may not discount %s" % (actor, opp_id))
PermissionError: actor 'r1' may not discount O1

======================================================================
ERROR: test_discount_keeps_original_amount (test_crm_ops.DiscountTest.test_discount_keeps_original_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 300, in test_discount_keeps_original_amount
    crm.discount(opp, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 226, in discount
    raise PermissionError("actor %r may not discount %s" % (actor, opp_id))
PermissionError: actor 'r1' may not discount O1

======================================================================
ERROR: test_discount_rejects_final_stage (test_crm_ops.DiscountTest.test_discount_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 260, in test_discount_rejects_final_stage
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_discount_rep_limit_is_ten (test_crm_ops.DiscountTest.test_discount_rep_limit_is_ten)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 276, in test_discount_rep_limit_is_ten
    crm.discount(opp, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 226, in discount
    raise PermissionError("actor %r may not discount %s" % (actor, opp_id))
PermissionError: actor 'r1' may not discount O1

======================================================================
ERROR: test_forecast_uses_current_amount (test_crm_ops.ForecastTest.test_forecast_uses_current_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 428, in test_forecast_uses_current_amount
    crm.discount(opp, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 226, in discount
    raise PermissionError("actor %r may not discount %s" % (actor, opp_id))
PermissionError: actor 'r1' may not discount O1

======================================================================
ERROR: test_transfer_rejects_final_stage (test_crm_ops.TransferTest.test_transfer_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 353, in test_transfer_rejects_final_stage
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
FAIL: test_load_balancing_picks_lowest_load (test_crm.AssignmentTest.test_load_balancing_picks_lowest_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 184, in test_load_balancing_picks_lowest_load
    self.assertEqual(owners, ["r1", "r2", "r3", "r1"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ['r3', 'r2', 'r1', 'r3'] != ['r1', 'r2', 'r3', 'r1']

First differing element 0:
'r3'
'r1'

- ['r3', 'r2', 'r1', 'r3']
+ ['r1', 'r2', 'r3', 'r1']

======================================================================
FAIL: test_tie_break_prefers_smallest_id (test_crm.AssignmentTest.test_tie_break_prefers_smallest_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 179, in test_tie_break_prefers_smallest_id
    self.assertEqual(crm.leads[lead_id]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r3' != 'r1'
- r3
+ r1


======================================================================
FAIL: test_atomic_transfer_failure (test_crm_ops.AtomicityTest.test_atomic_transfer_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 489, in test_atomic_transfer_failure
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_transfer_is_manager_only (test_crm_ops.TransferTest.test_transfer_is_manager_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 328, in test_transfer_is_manager_only
    self.assertEqual(crm.opps[opp]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r3' != 'r1'
- r3
+ r1


======================================================================
FAIL: test_transfer_rejects_same_owner (test_crm_ops.TransferTest.test_transfer_rejects_same_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 366, in test_transfer_rejects_same_owner
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_transfer_rejects_target_at_capacity (test_crm_ops.TransferTest.test_transfer_rejects_target_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 378, in test_transfer_rejects_target_at_capacity
    self.assertEqual(crm.leads[occupied]["owner"], "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' != 'r2'
- r1
+ r2


======================================================================
FAIL: test_transfer_releases_previous_owner_load (test_crm_ops.TransferTest.test_transfer_releases_previous_owner_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 400, in test_transfer_releases_previous_owner_load
    self.assertEqual(crm.opps[opp]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


----------------------------------------------------------------------
Ran 77 tests in 0.006s

FAILED (failures=7, errors=24)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 11. rep assignment / capacity / waiting queue

Case: lead no longer enqueued when no rep is free

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill queue_push" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_waiting_queue_is_fifo_on_freed_slot --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7k1qvm0_/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill queue_push

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_waiting_queue_is_fifo_on_freed_slot/
.F....F......................................................................
======================================================================
FAIL: test_drain_stops_at_capacity (test_crm.AssignmentTest.test_drain_stops_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 240, in test_drain_stops_at_capacity
    self.assertEqual(crm.leads[second]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_waiting_queue_is_fifo_on_freed_slot (test_crm.AssignmentTest.test_waiting_queue_is_fifo_on_freed_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 222, in test_waiting_queue_is_fifo_on_freed_slot
    self.assertEqual(crm.leads[third]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 12. rep assignment / capacity / waiting queue

Case: drain ignores capacity

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill drain_capacity" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_drain_stops_at_capacity --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-exbh173l/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill drain_capacity

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_drain_stops_at_capacity/
.F....F......................................................................
======================================================================
FAIL: test_drain_stops_at_capacity (test_crm.AssignmentTest.test_drain_stops_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 241, in test_drain_stops_at_capacity
    self.assertIsNone(crm.leads[third]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_waiting_queue_is_fifo_on_freed_slot (test_crm.AssignmentTest.test_waiting_queue_is_fifo_on_freed_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 224, in test_waiting_queue_is_fifo_on_freed_slot
    self.assertIsNone(crm.leads[fourth]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 13. rep assignment / capacity / waiting queue

Case: drain ignores an empty queue

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill drain_empty" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect "pop from empty list" --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-w0_r0d0o/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill drain_empty

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /pop from empty list/
....................E..........EE....E.E......................E...E...EE..E..
======================================================================
ERROR: test_manager_can_act (test_crm.PermissionTest.test_manager_can_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 320, in test_manager_can_act
    crm.transfer(opp, "r2", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 255, in transfer
    self._drain(previous)
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

======================================================================
ERROR: test_advance_full_path_logs (test_crm_ops.AdvanceTest.test_advance_full_path_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 188, in test_advance_full_path_logs
    crm.advance(opp, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 216, in advance
    self._drain(opp["owner"])
    ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

======================================================================
ERROR: test_advance_rejects_final_opportunity (test_crm_ops.AdvanceTest.test_advance_rejects_final_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 151, in test_advance_rejects_final_opportunity
    crm.advance(opp, "won", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 216, in advance
    self._drain(opp["owner"])
    ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

======================================================================
ERROR: test_advance_to_lost_from_any_open_stage (test_crm_ops.AdvanceTest.test_advance_to_lost_from_any_open_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 178, in test_advance_to_lost_from_any_open_stage
    crm.advance(first, "lost", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 216, in advance
    self._drain(opp["owner"])
    ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

======================================================================
ERROR: test_big_deal_denied_only_at_negotiation (test_crm_ops.AdvanceTest.test_big_deal_denied_only_at_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 217, in test_big_deal_denied_only_at_negotiation
    crm.advance(opp, "lost", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 216, in advance
    self._drain(opp["owner"])
    ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

======================================================================
ERROR: test_discount_rejects_final_stage (test_crm_ops.DiscountTest.test_discount_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 262, in test_discount_rejects_final_stage
    crm.advance(opp, "won", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 216, in advance
    self._drain(opp["owner"])
    ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

======================================================================
ERROR: test_forecast_mixed_pipeline (test_crm_ops.ForecastTest.test_forecast_mixed_pipeline)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 418, in test_forecast_mixed_pipeline
    crm.advance(won, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 216, in advance
    self._drain(opp["owner"])
    ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

======================================================================
ERROR: test_transfer_moves_owner_and_logs (test_crm_ops.TransferTest.test_transfer_moves_owner_and_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 389, in test_transfer_moves_owner_and_logs
    crm.transfer(opp, "r2", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 255, in transfer
    self._drain(previous)
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

======================================================================
ERROR: test_transfer_rejects_final_stage (test_crm_ops.TransferTest.test_transfer_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 355, in test_transfer_rejects_final_stage
    crm.advance(opp, "won", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 216, in advance
    self._drain(opp["owner"])
    ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

======================================================================
ERROR: test_transfer_releases_previous_owner_load (test_crm_ops.TransferTest.test_transfer_releases_previous_owner_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 401, in test_transfer_releases_previous_owner_load
    crm.transfer(opp, "r2", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 255, in transfer
    self._drain(previous)
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 96, in _drain
    lead_id = self.waiting.pop(0)
IndexError: pop from empty list

----------------------------------------------------------------------
Ran 77 tests in 0.005s

FAILED (errors=10)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 14. permission checks

Case: manager branch of the owner-or-manager check removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py sub perm_manager 'return True'" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_non_owner_rep_cannot_act --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7a2bjujr/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py sub perm_manager 'return True'

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_non_owner_rep_cannot_act/
......................E............F...................F........F............
======================================================================
ERROR: test_non_owner_rep_cannot_act (test_crm.PermissionTest.test_non_owner_rep_cannot_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 306, in test_non_owner_rep_cannot_act
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 300, in <lambda>
    lambda: crm.qualify("L1", "r2"),
            ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 164, in qualify
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
FAIL: test_advance_requires_permission (test_crm_ops.AdvanceTest.test_advance_requires_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 141, in test_advance_requires_permission
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_convert_requires_permission (test_crm_ops.ConvertTest.test_convert_requires_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 71, in test_convert_requires_permission
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_discount_requires_permission (test_crm_ops.DiscountTest.test_discount_requires_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 253, in test_discount_requires_permission
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=3, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 15. permission checks

Case: owner branch of the owner-or-manager check removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill perm_owner" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_owner_can_act --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-30b5cjbd/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill perm_owner

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_owner_can_act/
.E.E..E.............E.EE.EEE...EE.E..EEEEEE.E..EE..EE...EE.E..EE..EE...E.....
======================================================================
ERROR: test_drain_stops_at_capacity (test_crm.AssignmentTest.test_drain_stops_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 235, in test_drain_stops_at_capacity
    crm.qualify(first, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_load_counts_new_and_qualified_leads (test_crm.AssignmentTest.test_load_counts_new_and_qualified_leads)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 249, in test_load_counts_new_and_qualified_leads
    crm.qualify(first, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_waiting_queue_is_fifo_on_freed_slot (test_crm.AssignmentTest.test_waiting_queue_is_fifo_on_freed_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 216, in test_waiting_queue_is_fifo_on_freed_slot
    crm.qualify(first, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_manager_can_act (test_crm.PermissionTest.test_manager_can_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 317, in test_manager_can_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_non_owner_rep_cannot_act (test_crm.PermissionTest.test_non_owner_rep_cannot_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 295, in test_non_owner_rep_cannot_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_owner_can_act (test_crm.PermissionTest.test_owner_can_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 310, in test_owner_can_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_crm.PermissionTest.test_unknown_actor_rejected_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 266, in test_unknown_actor_rejected_everywhere
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 261, in fixture
    crm.qualify(lead, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_score_at_or_above_threshold_qualifies (test_crm.ScoreTest.test_score_at_or_above_threshold_qualifies)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 171, in test_score_at_or_above_threshold_qualifies
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_score_below_threshold_cannot_qualify (test_crm.ScoreTest.test_score_below_threshold_cannot_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 163, in test_score_below_threshold_cannot_qualify
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_advance_full_path_logs (test_crm_ops.AdvanceTest.test_advance_full_path_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 188, in test_advance_full_path_logs
    crm.advance(opp, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_advance_rejects_final_opportunity (test_crm_ops.AdvanceTest.test_advance_rejects_final_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 149, in test_advance_rejects_final_opportunity
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_advance_requires_immediate_next_stage (test_crm_ops.AdvanceTest.test_advance_requires_immediate_next_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 163, in test_advance_requires_immediate_next_stage
    crm.advance(second, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O2

======================================================================
ERROR: test_advance_to_lost_from_any_open_stage (test_crm_ops.AdvanceTest.test_advance_to_lost_from_any_open_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 177, in test_advance_to_lost_from_any_open_stage
    crm.advance(second, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O2

======================================================================
ERROR: test_big_deal_check_follows_stage_order (test_crm_ops.AdvanceTest.test_big_deal_check_follows_stage_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 225, in test_big_deal_check_follows_stage_order
    crm.advance(opp, "negotiation", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_big_deal_denied_only_at_negotiation (test_crm_ops.AdvanceTest.test_big_deal_denied_only_at_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 215, in test_big_deal_denied_only_at_negotiation
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_big_deal_requires_manager (test_crm_ops.AdvanceTest.test_big_deal_requires_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 196, in test_big_deal_requires_manager
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_big_deal_threshold_is_inclusive (test_crm_ops.AdvanceTest.test_big_deal_threshold_is_inclusive)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 208, in test_big_deal_threshold_is_inclusive
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_big_deal_uses_current_amount (test_crm_ops.AdvanceTest.test_big_deal_uses_current_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 231, in test_big_deal_uses_current_amount
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_atomic_advance_bigdeal (test_crm_ops.AtomicityTest.test_atomic_advance_bigdeal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 455, in test_atomic_advance_bigdeal
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_atomic_log_qualify (test_crm_ops.AtomicityTest.test_atomic_log_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 439, in test_atomic_log_qualify
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 162, in qualify
    raise PermissionError("actor %r may not qualify %s" % (actor, lead_id))
PermissionError: actor 'r1' may not qualify L1

======================================================================
ERROR: test_atomic_state_convert (test_crm_ops.AtomicityTest.test_atomic_state_convert)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 448, in test_atomic_state_convert
    crm.convert(lead_id, 1000, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_convert_builds_opportunity (test_crm_ops.ConvertTest.test_convert_builds_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 99, in test_convert_builds_opportunity
    opp_id = crm.convert(lead_id, 2500, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_convert_ids_increment (test_crm_ops.ConvertTest.test_convert_ids_increment)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 116, in test_convert_ids_increment
    first = crm.convert(qualified(crm, "a@example.com"), 100, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_convert_requires_qualified_status (test_crm_ops.ConvertTest.test_convert_requires_qualified_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 80, in test_convert_requires_qualified_status
    crm.convert(lead_id, 1000, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 178, in convert
    raise PermissionError("actor %r may not convert %s" % (actor, lead_id))
PermissionError: actor 'r1' may not convert L1

======================================================================
ERROR: test_discount_cumulative_floor (test_crm_ops.DiscountTest.test_discount_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 289, in test_discount_cumulative_floor
    crm.discount(opp, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 226, in discount
    raise PermissionError("actor %r may not discount %s" % (actor, opp_id))
PermissionError: actor 'r1' may not discount O1

======================================================================
ERROR: test_discount_keeps_original_amount (test_crm_ops.DiscountTest.test_discount_keeps_original_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 300, in test_discount_keeps_original_amount
    crm.discount(opp, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 226, in discount
    raise PermissionError("actor %r may not discount %s" % (actor, opp_id))
PermissionError: actor 'r1' may not discount O1

======================================================================
ERROR: test_discount_rejects_final_stage (test_crm_ops.DiscountTest.test_discount_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 260, in test_discount_rejects_final_stage
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

======================================================================
ERROR: test_discount_rep_limit_is_ten (test_crm_ops.DiscountTest.test_discount_rep_limit_is_ten)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 276, in test_discount_rep_limit_is_ten
    crm.discount(opp, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 226, in discount
    raise PermissionError("actor %r may not discount %s" % (actor, opp_id))
PermissionError: actor 'r1' may not discount O1

======================================================================
ERROR: test_forecast_mixed_pipeline (test_crm_ops.ForecastTest.test_forecast_mixed_pipeline)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 416, in test_forecast_mixed_pipeline
    crm.advance(proposal, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O2

======================================================================
ERROR: test_forecast_uses_current_amount (test_crm_ops.ForecastTest.test_forecast_uses_current_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 428, in test_forecast_uses_current_amount
    crm.discount(opp, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 226, in discount
    raise PermissionError("actor %r may not discount %s" % (actor, opp_id))
PermissionError: actor 'r1' may not discount O1

======================================================================
ERROR: test_transfer_rejects_final_stage (test_crm_ops.TransferTest.test_transfer_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 353, in test_transfer_rejects_final_stage
    crm.advance(opp, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r1' may not advance O1

----------------------------------------------------------------------
Ran 77 tests in 0.006s

FAILED (errors=31)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 16. permission checks

Case: unknown-actor rejection removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill actor_known" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_unknown_actor --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-qcpme5ip/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill actor_known

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_unknown_actor/
........................EE...................................................
======================================================================
ERROR: test_unknown_actor_checked_before_other_validation (test_crm.PermissionTest.test_unknown_actor_checked_before_other_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 292, in test_unknown_actor_checked_before_other_validation
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 284, in <lambda>
    lambda: crm.add_lead("bad-email", "", "bogus", "ghost"),
            ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 124, in add_lead
    self._check_actor(actor)
    ~~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 54, in _check_actor
    return self.users[actor]
           ~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_crm.PermissionTest.test_unknown_actor_rejected_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 278, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 269, in <lambda>
    lambda: crm.add_lead("z@example.com", "Zoe", "web", "ghost"),
            ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 124, in add_lead
    self._check_actor(actor)
    ~~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 54, in _check_actor
    return self.users[actor]
           ~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 17. qualification score threshold

Case: score >= 30 gate removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill qualify_score" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_score_below_threshold_cannot_qualify --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3jw592gy/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill qualify_score

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_score_below_threshold_cannot_qualify/
...........................F...................F.............................
======================================================================
FAIL: test_score_below_threshold_cannot_qualify (test_crm.ScoreTest.test_score_below_threshold_cannot_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 162, in test_score_below_threshold_cannot_qualify
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_atomic_log_qualify (test_crm_ops.AtomicityTest.test_atomic_log_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 438, in test_atomic_log_qualify
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 18. stage-transition rules

Case: unknown stage name accepted

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill advance_stage_valid" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_advance_stage_name_validated_before_permission --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ot5vd6us/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill advance_stage_valid

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_advance_stage_name_validated_before_permission/
....................................E........................................
======================================================================
ERROR: test_advance_stage_name_validated_before_permission (test_crm_ops.AdvanceTest.test_advance_stage_name_validated_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 132, in test_advance_stage_name_validated_before_permission
    crm.advance(opp, "bogus", "r2")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 206, in advance
    raise PermissionError("actor %r may not advance %s" % (actor, opp_id))
PermissionError: actor 'r2' may not advance O1

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 19. stage-transition rules

Case: immediate-next-stage rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill advance_order" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_advance_requires_immediate_next_stage --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-66jbhys1/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill advance_order

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_advance_requires_immediate_next_stage/
..................................F...E......................................
======================================================================
ERROR: test_big_deal_check_follows_stage_order (test_crm_ops.AdvanceTest.test_big_deal_check_follows_stage_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 225, in test_big_deal_check_follows_stage_order
    crm.advance(opp, "negotiation", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 212, in advance
    raise PermissionError("opportunity %s needs a manager to negotiate" % (opp_id,))
PermissionError: opportunity O1 needs a manager to negotiate

======================================================================
FAIL: test_advance_requires_immediate_next_stage (test_crm_ops.AdvanceTest.test_advance_requires_immediate_next_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 165, in test_advance_requires_immediate_next_stage
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 20. stage-transition rules

Case: final-stage lock removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill advance_final" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_advance_rejects_final_opportunity --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-mdlcqple/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill advance_final

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_advance_rejects_final_opportunity/
................................F............................................
======================================================================
FAIL: test_advance_rejects_final_opportunity (test_crm_ops.AdvanceTest.test_advance_rejects_final_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 154, in test_advance_rejects_final_opportunity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 21. big-deal approval

Case: manager requirement above 50000 removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill advance_bigdeal" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_big_deal_requires_manager --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9rvfptqz/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill advance_bigdeal

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_big_deal_requires_manager/
........................................F...F................................
======================================================================
FAIL: test_big_deal_requires_manager (test_crm_ops.AdvanceTest.test_big_deal_requires_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 198, in test_big_deal_requires_manager
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_atomic_advance_bigdeal (test_crm_ops.AtomicityTest.test_atomic_advance_bigdeal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 457, in test_atomic_advance_bigdeal
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 22. discount limits and cumulative floor

Case: pct range/type check removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill discount_pct" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_discount_pct_validation --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-u6_6edvj/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill discount_pct

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_discount_pct_validation/
.............................................F...............F...............
======================================================================
FAIL: test_atomic_discount_failure (test_crm_ops.AtomicityTest.test_atomic_discount_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 468, in test_atomic_discount_failure
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_discount_pct_validation (test_crm_ops.DiscountTest.test_discount_pct_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 244, in test_discount_pct_validation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 23. discount limits and cumulative floor

Case: non-manager 10% cap removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill discount_rep_limit" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_discount_rep_limit_is_ten --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-hit3a2iw/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill discount_rep_limit

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_discount_rep_limit_is_ten/
.............................................F.................F.............
======================================================================
FAIL: test_atomic_discount_failure (test_crm_ops.AtomicityTest.test_atomic_discount_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 466, in test_atomic_discount_failure
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_discount_rep_limit_is_ten (test_crm_ops.DiscountTest.test_discount_rep_limit_is_ten)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 273, in test_discount_rep_limit_is_ten
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.004s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 24. discount limits and cumulative floor

Case: 70% cumulative floor removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill discount_floor" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_discount_cumulative_floor --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-f72qrgf7/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill discount_floor

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_discount_cumulative_floor/
..............................................F..........FF..................
======================================================================
FAIL: test_atomic_discount_floor_failure (test_crm_ops.AtomicityTest.test_atomic_discount_floor_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 478, in test_atomic_discount_floor_failure
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_discount_cumulative_floor (test_crm_ops.DiscountTest.test_discount_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 292, in test_discount_cumulative_floor
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_discount_floor_tracks_original_amount (test_crm_ops.DiscountTest.test_discount_floor_tracks_original_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 311, in test_discount_floor_tracks_original_amount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 25. discount limits and cumulative floor

Case: final-stage discount lock removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill discount_final" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_discount_rejects_final_stage --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0zr2ifgb/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill discount_final

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_discount_rejects_final_stage/
..............................................................F..............
======================================================================
FAIL: test_discount_rejects_final_stage (test_crm_ops.DiscountTest.test_discount_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 264, in test_discount_rejects_final_stage
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 26. transfer rules

Case: manager-only rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_manager" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_transfer_is_manager_only --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7weut1r2/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_manager

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_transfer_is_manager_only/
.................................................F..................FE.......
======================================================================
ERROR: test_transfer_manager_check_precedes_target_check (test_crm_ops.TransferTest.test_transfer_manager_check_precedes_target_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 335, in test_transfer_manager_check_precedes_target_check
    crm.transfer(opp, "nobody", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 245, in transfer
    raise ValueError("transfer target must be a known rep: %r" % (new_owner,))
ValueError: transfer target must be a known rep: 'nobody'

======================================================================
FAIL: test_atomic_transfer_failure (test_crm_ops.AtomicityTest.test_atomic_transfer_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 487, in test_atomic_transfer_failure
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_transfer_is_manager_only (test_crm_ops.TransferTest.test_transfer_is_manager_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 326, in test_transfer_is_manager_only
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 27. transfer rules

Case: target must be a known rep: rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_target" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_transfer_target_must_be_known_rep --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-13ocnw24/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_target

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_transfer_target_must_be_known_rep/
............................................................................E
======================================================================
ERROR: test_transfer_target_must_be_known_rep (test_crm_ops.TransferTest.test_transfer_target_must_be_known_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 346, in test_transfer_target_must_be_known_rep
    crm.transfer(opp, bad, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 250, in transfer
    if self._load(new_owner) >= self.users[new_owner]["capacity"]:  # @g:transfer_capacity
                                ~~~~~~~~~~^^^^^^^^^^^
KeyError: 'nobody'

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 28. transfer rules

Case: same-owner rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_same" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_transfer_rejects_same_owner --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-rye9rsg4/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_same

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_transfer_rejects_same_owner/
.................................................F......................F....
======================================================================
FAIL: test_atomic_transfer_failure (test_crm_ops.AtomicityTest.test_atomic_transfer_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 489, in test_atomic_transfer_failure
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_transfer_rejects_same_owner (test_crm_ops.TransferTest.test_transfer_rejects_same_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 366, in test_transfer_rejects_same_owner
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 29. transfer rules

Case: target capacity rule removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_capacity" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_transfer_rejects_target_at_capacity --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-2yku1_ww/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_capacity

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_transfer_rejects_target_at_capacity/
.........................................................................F...
======================================================================
FAIL: test_transfer_rejects_target_at_capacity (test_crm_ops.TransferTest.test_transfer_rejects_target_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 381, in test_transfer_rejects_target_at_capacity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 30. transfer rules

Case: final-stage transfer lock removed

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_final" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_transfer_rejects_final_stage --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-tvoenhhm/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py kill transfer_final

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_transfer_rejects_final_stage/
.......................................................................F.....
======================================================================
FAIL: test_transfer_rejects_final_stage (test_crm_ops.TransferTest.test_transfer_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 357, in test_transfer_rejects_final_stage
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 31. atomicity (failed call changes nothing, logs nothing)

Case: log entry written before the failing guard (qualify)

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py insert qualify_score 'self.log.append(("qualify", lead_id, actor))'" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_atomic_log_qualify --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-qxqvduio/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py insert qualify_score 'self.log.append(("qualify", lead_id, actor))'

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_atomic_log_qualify/
...........................F...................F...F.........................
======================================================================
FAIL: test_score_below_threshold_cannot_qualify (test_crm.ScoreTest.test_score_below_threshold_cannot_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 165, in test_score_below_threshold_cannot_qualify
    self.assertEqual(state(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[112 chars]ew'}}, {}, [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')]) != ({'L1[112 chars]ew'}}, {}, [('add_lead', 'L1', 'r1')])

First differing element 2:
[('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')]
[('add_lead', 'L1', 'r1')]

  ({'L1': {'email': 'a@gmail.com',
           'id': 'L1',
           'name': 'Ada',
           'owner': 'r1',
           'score': 10,
           'source': 'web',
           'status': 'new'}},
   {},
-  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')])
+  [('add_lead', 'L1', 'r1')])

======================================================================
FAIL: test_atomic_log_qualify (test_crm_ops.AtomicityTest.test_atomic_log_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 441, in test_atomic_log_qualify
    self.assertEqual(state(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[114 chars]ew'}}, {}, [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')]) != ({'L1[114 chars]ew'}}, {}, [('add_lead', 'L1', 'r1')])

First differing element 2:
[('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')]
[('add_lead', 'L1', 'r1')]

  ({'L1': {'email': 'low@gmail.com',
           'id': 'L1',
           'name': 'Ada',
           'owner': 'r1',
           'score': 10,
           'source': 'web',
           'status': 'new'}},
   {},
-  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')])
+  [('add_lead', 'L1', 'r1')])

======================================================================
FAIL: test_convert_builds_opportunity (test_crm_ops.ConvertTest.test_convert_builds_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 110, in test_convert_builds_opportunity
    self.assertEqual(crm.log, [("add_lead", lead_id, "r1"),
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                               ("qualify", lead_id, "m1"),
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^
                               ("convert", "O1", "r1")])
                               ^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[33 chars] 'L1', 'm1'), ('qualify', 'L1', 'm1'), ('convert', 'O1', 'r1')] != [('ad[33 chars] 'L1', 'm1'), ('convert', 'O1', 'r1')]

First differing element 2:
('qualify', 'L1', 'm1')
('convert', 'O1', 'r1')

First list contains 1 additional elements.
First extra element 3:
('convert', 'O1', 'r1')

+ [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'm1'), ('convert', 'O1', 'r1')]
- [('add_lead', 'L1', 'r1'),
-  ('qualify', 'L1', 'm1'),
-  ('qualify', 'L1', 'm1'),
-  ('convert', 'O1', 'r1')]

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 32. atomicity (failed call changes nothing, logs nothing)

Case: lead status mutated before the failing guard (convert)

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py insert convert_status 'lead["status"] = "converted"'" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_atomic_state_convert --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9i4gzn64/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py insert convert_status 'lead["status"] = "converted"'

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_atomic_state_convert/
.E.E..E.............EFEE.E.....EE.EEEEEEEEE.EEE.FE.EE.F.FEEEEEEEE.EEEEEEEEE.E
======================================================================
ERROR: test_drain_stops_at_capacity (test_crm.AssignmentTest.test_drain_stops_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 236, in test_drain_stops_at_capacity
    opp = crm.convert(first, 1000, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_load_counts_new_and_qualified_leads (test_crm.AssignmentTest.test_load_counts_new_and_qualified_leads)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 253, in test_load_counts_new_and_qualified_leads
    crm.convert(first, 1000, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_waiting_queue_is_fifo_on_freed_slot (test_crm.AssignmentTest.test_waiting_queue_is_fifo_on_freed_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 217, in test_waiting_queue_is_fifo_on_freed_slot
    opp = crm.convert(first, 1000, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_manager_can_act (test_crm.PermissionTest.test_manager_can_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 317, in test_manager_can_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 262, in fixture
    opp = crm.convert(lead, 1000, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_non_owner_rep_cannot_act (test_crm.PermissionTest.test_non_owner_rep_cannot_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 295, in test_non_owner_rep_cannot_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 262, in fixture
    opp = crm.convert(lead, 1000, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_owner_can_act (test_crm.PermissionTest.test_owner_can_act)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 310, in test_owner_can_act
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 262, in fixture
    opp = crm.convert(lead, 1000, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_crm.PermissionTest.test_unknown_actor_rejected_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 266, in test_unknown_actor_rejected_everywhere
    crm, lead, opp = self.fixture()
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 262, in fixture
    opp = crm.convert(lead, 1000, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_advance_full_path_logs (test_crm_ops.AdvanceTest.test_advance_full_path_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 186, in test_advance_full_path_logs
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_advance_rejects_final_opportunity (test_crm_ops.AdvanceTest.test_advance_rejects_final_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 148, in test_advance_rejects_final_opportunity
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_advance_requires_immediate_next_stage (test_crm_ops.AdvanceTest.test_advance_requires_immediate_next_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 161, in test_advance_requires_immediate_next_stage
    first = make_opp(crm, 1000, "a@example.com")
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_advance_requires_permission (test_crm_ops.AdvanceTest.test_advance_requires_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 139, in test_advance_requires_permission
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_advance_stage_name_validated_before_permission (test_crm_ops.AdvanceTest.test_advance_stage_name_validated_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 129, in test_advance_stage_name_validated_before_permission
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_advance_to_lost_from_any_open_stage (test_crm_ops.AdvanceTest.test_advance_to_lost_from_any_open_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 175, in test_advance_to_lost_from_any_open_stage
    first = make_opp(crm, 1000, "a@example.com")
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_big_deal_check_follows_stage_order (test_crm_ops.AdvanceTest.test_big_deal_check_follows_stage_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 222, in test_big_deal_check_follows_stage_order
    opp = make_opp(crm, 60000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_big_deal_denied_only_at_negotiation (test_crm_ops.AdvanceTest.test_big_deal_denied_only_at_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 214, in test_big_deal_denied_only_at_negotiation
    opp = make_opp(crm, 60000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_big_deal_requires_manager (test_crm_ops.AdvanceTest.test_big_deal_requires_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 195, in test_big_deal_requires_manager
    opp = make_opp(crm, 50001)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_big_deal_threshold_is_inclusive (test_crm_ops.AdvanceTest.test_big_deal_threshold_is_inclusive)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 207, in test_big_deal_threshold_is_inclusive
    opp = make_opp(crm, 50000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_big_deal_uses_current_amount (test_crm_ops.AdvanceTest.test_big_deal_uses_current_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 230, in test_big_deal_uses_current_amount
    opp = make_opp(crm, 60000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_atomic_advance_bigdeal (test_crm_ops.AtomicityTest.test_atomic_advance_bigdeal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 454, in test_atomic_advance_bigdeal
    opp = make_opp(crm, 60000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_atomic_discount_failure (test_crm_ops.AtomicityTest.test_atomic_discount_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 464, in test_atomic_discount_failure
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_atomic_discount_floor_failure (test_crm_ops.AtomicityTest.test_atomic_discount_floor_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 475, in test_atomic_discount_floor_failure
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_atomic_transfer_failure (test_crm_ops.AtomicityTest.test_atomic_transfer_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 485, in test_atomic_transfer_failure
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_convert_builds_opportunity (test_crm_ops.ConvertTest.test_convert_builds_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 99, in test_convert_builds_opportunity
    opp_id = crm.convert(lead_id, 2500, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_convert_ids_increment (test_crm_ops.ConvertTest.test_convert_ids_increment)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 116, in test_convert_ids_increment
    first = crm.convert(qualified(crm, "a@example.com"), 100, "r1")
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_discount_cumulative_floor (test_crm_ops.DiscountTest.test_discount_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 287, in test_discount_cumulative_floor
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_discount_floor_tracks_original_amount (test_crm_ops.DiscountTest.test_discount_floor_tracks_original_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 307, in test_discount_floor_tracks_original_amount
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_discount_keeps_original_amount (test_crm_ops.DiscountTest.test_discount_keeps_original_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 299, in test_discount_keeps_original_amount
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_discount_manager_may_use_full_range (test_crm_ops.DiscountTest.test_discount_manager_may_use_full_range)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 281, in test_discount_manager_may_use_full_range
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_discount_pct_validation (test_crm_ops.DiscountTest.test_discount_pct_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 241, in test_discount_pct_validation
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_discount_rejects_final_stage (test_crm_ops.DiscountTest.test_discount_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 259, in test_discount_rejects_final_stage
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_discount_rep_limit_is_ten (test_crm_ops.DiscountTest.test_discount_rep_limit_is_ten)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 271, in test_discount_rep_limit_is_ten
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_discount_requires_permission (test_crm_ops.DiscountTest.test_discount_requires_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 251, in test_discount_requires_permission
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_forecast_mixed_pipeline (test_crm_ops.ForecastTest.test_forecast_mixed_pipeline)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 412, in test_forecast_mixed_pipeline
    prospect = make_opp(crm, 1000, "a@example.com")
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_forecast_uses_current_amount (test_crm_ops.ForecastTest.test_forecast_uses_current_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 427, in test_forecast_uses_current_amount
    opp = make_opp(crm, 1000)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_transfer_is_manager_only (test_crm_ops.TransferTest.test_transfer_is_manager_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 324, in test_transfer_is_manager_only
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_transfer_manager_check_precedes_target_check (test_crm_ops.TransferTest.test_transfer_manager_check_precedes_target_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 333, in test_transfer_manager_check_precedes_target_check
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_transfer_moves_owner_and_logs (test_crm_ops.TransferTest.test_transfer_moves_owner_and_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 388, in test_transfer_moves_owner_and_logs
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_transfer_rejects_final_stage (test_crm_ops.TransferTest.test_transfer_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 352, in test_transfer_rejects_final_stage
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_transfer_rejects_same_owner (test_crm_ops.TransferTest.test_transfer_rejects_same_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 364, in test_transfer_rejects_same_owner
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_transfer_rejects_target_at_capacity (test_crm_ops.TransferTest.test_transfer_rejects_target_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 379, in test_transfer_rejects_target_at_capacity
    opp = make_opp(crm, 1000, "c@example.com")
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L3 is converted

======================================================================
ERROR: test_transfer_releases_previous_owner_load (test_crm_ops.TransferTest.test_transfer_releases_previous_owner_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 399, in test_transfer_releases_previous_owner_load
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
ERROR: test_transfer_target_must_be_known_rep (test_crm_ops.TransferTest.test_transfer_target_must_be_known_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 342, in test_transfer_target_must_be_known_rep
    opp = make_opp(crm)
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 47, in make_opp
    return crm.convert(lead_id, amount, "m1")
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-1/crm.py", line 181, in convert
    raise ValueError("lead %s is %s" % (lead_id, lead["status"]))
ValueError: lead L1 is converted

======================================================================
FAIL: test_manager_cannot_convert_unowned_lead (test_crm.PermissionTest.test_manager_cannot_convert_unowned_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm.py", line 335, in test_manager_cannot_convert_unowned_lead
    self.assertEqual(state(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[113 chars]s': 'converted'}}, {}, [('add_lead', 'L1', 'r1[24 chars]1')]) != ({'L1[113 chars]s': 'qualified'}}, {}, [('add_lead', 'L1', 'r1[24 chars]1')])

First differing element 0:
{'L1'[66 chars]'referral', 'score': 45, 'owner': None, 'status': 'converted'}}
{'L1'[66 chars]'referral', 'score': 45, 'owner': None, 'status': 'qualified'}}

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Ada',
           'owner': None,
           'score': 45,
           'source': 'referral',
-          'status': 'converted'}},
?                     ^^^^^^^

+          'status': 'qualified'}},
?                     ^^^^^^^

   {},
   [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'm1')])

======================================================================
FAIL: test_atomic_state_convert (test_crm_ops.AtomicityTest.test_atomic_state_convert)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 449, in test_atomic_state_convert
    self.assertEqual(crm.leads[lead_id]["status"], "new")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'converted' != 'new'
- converted
+ new


======================================================================
FAIL: test_convert_requires_owner (test_crm_ops.ConvertTest.test_convert_requires_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 94, in test_convert_requires_owner
    self.assertEqual(state(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[116 chars]s': 'converted'}}, {}, [('add_lead', 'L1', 'r1[24 chars]1')]) != ({'L1[116 chars]s': 'qualified'}}, {}, [('add_lead', 'L1', 'r1[24 chars]1')])

First differing element 0:
{'L1'[69 chars]'referral', 'score': 45, 'owner': None, 'status': 'converted'}}
{'L1'[69 chars]'referral', 'score': 45, 'owner': None, 'status': 'qualified'}}

  ({'L1': {'email': 'lead@example.com',
           'id': 'L1',
           'name': 'Ada',
           'owner': None,
           'score': 45,
           'source': 'referral',
-          'status': 'converted'}},
?                     ^^^^^^^

+          'status': 'qualified'}},
?                     ^^^^^^^

   {},
   [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'm1')])

======================================================================
FAIL: test_convert_requires_qualified_status (test_crm_ops.ConvertTest.test_convert_requires_qualified_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 81, in test_convert_requires_qualified_status
    self.assertEqual(crm.leads[lead_id]["status"], "new")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'converted' != 'new'
- converted
+ new


----------------------------------------------------------------------
Ran 77 tests in 0.009s

FAILED (failures=4, errors=42)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 33. atomicity (failed call changes nothing, logs nothing)

Case: opp stage mutated before the failing guard (advance)

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py insert advance_bigdeal 'opp["stage"] = stage'" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_atomic_advance_bigdeal --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0f76cta7/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py insert advance_bigdeal 'opp["stage"] = stage'

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_atomic_advance_bigdeal/
........................................F...F................................
======================================================================
FAIL: test_big_deal_requires_manager (test_crm_ops.AdvanceTest.test_big_deal_requires_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 200, in test_big_deal_requires_manager
    self.assertEqual(crm.opps[opp]["stage"], "proposal")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'negotiation' != 'proposal'
- negotiation
+ proposal


======================================================================
FAIL: test_atomic_advance_bigdeal (test_crm_ops.AtomicityTest.test_atomic_advance_bigdeal)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 459, in test_atomic_advance_bigdeal
    self.assertEqual(crm.opps[opp]["stage"], "proposal")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'negotiation' != 'proposal'
- negotiation
+ proposal


----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## 34. atomicity (failed call changes nothing, logs nothing)

Case: amount mutated before the failing floor guard (discount)

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-1/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py insert discount_floor 'opp["amount"] = new_amount'" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'" --expect test_atomic_discount_floor_failure --timeout 20
```

Verdict: **PASS (exit 0)**

```text
$ backed up /tmp/aep-lab/pilot2/N-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-k2a_wb08/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-1/_negctl_break.py insert discount_floor 'opp["amount"] = new_amount'

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect FAILURE matching /test_atomic_discount_floor_failure/
..............................................F..........FF..................
======================================================================
FAIL: test_atomic_discount_floor_failure (test_crm_ops.AtomicityTest.test_atomic_discount_floor_failure)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 480, in test_atomic_discount_floor_failure
    self.assertEqual(crm.opps[opp]["amount"], 700)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 693 != 700

======================================================================
FAIL: test_discount_cumulative_floor (test_crm_ops.DiscountTest.test_discount_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 294, in test_discount_cumulative_floor
    self.assertEqual(crm.opps[opp]["amount"], 729)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 656 != 729

======================================================================
FAIL: test_discount_floor_tracks_original_amount (test_crm_ops.DiscountTest.test_discount_floor_tracks_original_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-1/test_crm_ops.py", line 313, in test_discount_floor_tracks_original_amount
    self.assertEqual(state(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[192 chars]nt': 693, 'original_amount': 1000, 'stage': 'p[110 chars]1')]) != ({'L1[192 chars]nt': 700, 'original_amount': 1000, 'stage': 'p[110 chars]1')])

First differing element 1:
{'O1'[45 chars], 'amount': 693, 'original_amount': 1000, 'stage': 'prospect'}}
{'O1'[45 chars], 'amount': 700, 'original_amount': 1000, 'stage': 'prospect'}}

  ({'L1': {'email': 'deal@example.com',
           'id': 'L1',
           'name': 'Ada',
           'owner': 'r1',
           'score': 45,
           'source': 'referral',
           'status': 'converted'}},
-  {'O1': {'amount': 693,
?                    ^^^

+  {'O1': {'amount': 700,
?                    ^^^

           'id': 'O1',
           'lead_id': 'L1',
           'original_amount': 1000,
           'owner': 'r1',
           'stage': 'prospect'}},
   [('add_lead', 'L1', 'r1'),
    ('qualify', 'L1', 'm1'),
    ('convert', 'O1', 'm1'),
    ('discount', 'O1', 'm1')])

----------------------------------------------------------------------
Ran 77 tests in 0.003s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-1 -p 'test*.py'   # expect SUCCESS
.............................................................................
----------------------------------------------------------------------
Ran 77 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

