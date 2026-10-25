# Negative Control Log — crm.py (AE-neutral-2)

Project: `/tmp/aep-lab/pilot2/AE-neutral-2`  
Tool: `/tmp/aep-lab/v060/bin/aepkit negcontrol`  
Date: 2026-10-25T07:24:23Z

Each control backs up `crm.py`, applies one surgical break, runs the full
suite (`python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"`), restores `crm.py`, and runs the suite again.
Aepkit returns 0 only when the tests fail under the break, the failing
output matches `--expect`, and the tests pass after restoration.

## Audit remediation round 1

`audit.md` rejected the previous evidence because four spec guards could be
deleted while the suite stayed green (M1–M4) and five more guards had no
control. Tests were added for the four (plus a dedicated queue-membership
test); `crm.py` itself is unchanged (md5 `e04fde9b35aed227ca29113e462e8c19`).
Controls added: `break_won_frees_slot`, `break_advance_assign_target`,
`break_bigdeal_original_amount`, `break_forecast_original_amount`,
`break_normalization`, `break_forecast_weights`, `break_transfer_same_owner`,
`break_free_domain_bonus`, `break_queue_membership`, `break_email_at`,
`break_tie_order`, `break_managers_no_work`. This run: **35/35 controls exit 0**.
Control A1 (`break_transfer_queue`) is not runnable: a non-empty queue
implies every rep is at capacity, so `transfer` rejects every candidate
before the drain line (see `audit.md` §5.1).

## Summary

| # | Control | Guard group | Exit | Verdict |
|---|---|---|---|---|
| 1 | `break_email_domain` | G1 email/name/source validation | 0 | **PASS** |
| 2 | `break_email_local` | G1 email/name/source validation | 0 | **PASS** |
| 3 | `break_email_at` | G1 email/name/source validation | 0 | **PASS** |
| 4 | `break_name` | G1 email/name/source validation | 0 | **PASS** |
| 5 | `break_source` | G1 email/name/source validation | 0 | **PASS** |
| 6 | `break_normalization` | G1 email/name/source validation | 0 | **PASS** |
| 7 | `break_free_domain_bonus` | G1 email/name/source validation | 0 | **PASS** |
| 8 | `break_duplicate` | G2 duplicate detection | 0 | **PASS** |
| 9 | `break_assignment_capacity` | G3 rep assignment and capacity | 0 | **PASS** |
| 10 | `break_tie_order` | G3 rep assignment and capacity | 0 | **PASS** |
| 11 | `break_managers_no_work` | G3 rep assignment and capacity | 0 | **PASS** |
| 12 | `break_queue_membership` | G3 rep assignment and capacity | 0 | **PASS** |
| 13 | `break_waiting_queue` | G3 rep assignment and capacity | 0 | **PASS** |
| 14 | `break_won_frees_slot` | G3 rep assignment and capacity | 0 | **PASS** |
| 15 | `break_advance_assign_target` | G3 rep assignment and capacity | 0 | **PASS** |
| 16 | `break_unknown_actor` | G4 permission checks | 0 | **PASS** |
| 17 | `break_non_owner_permission` | G4 permission checks | 0 | **PASS** |
| 18 | `break_transfer_manager_only` | G4 permission checks | 0 | **PASS** |
| 19 | `break_score` | G5 qualification score threshold | 0 | **PASS** |
| 20 | `break_stage_transition` | G6 stage-transition rules | 0 | **PASS** |
| 21 | `break_big_deal` | G7 big-deal approval | 0 | **PASS** |
| 22 | `break_bigdeal_original_amount` | G7 big-deal approval | 0 | **PASS** |
| 23 | `break_discount_cap` | G8 discount limits | 0 | **PASS** |
| 24 | `break_pct_range` | G8 discount limits | 0 | **PASS** |
| 25 | `break_discount_floor` | G9 cumulative discount floor | 0 | **PASS** |
| 26 | `break_transfer_role` | G10 transfer rules | 0 | **PASS** |
| 27 | `break_transfer_capacity` | G10 transfer rules | 0 | **PASS** |
| 28 | `break_transfer_final` | G10 transfer rules | 0 | **PASS** |
| 29 | `break_transfer_same_owner` | G10 transfer rules | 0 | **PASS** |
| 30 | `break_atomicity_discount` | G11 atomicity | 0 | **PASS** |
| 31 | `break_atomicity_convert` | G11 atomicity | 0 | **PASS** |
| 32 | `break_atomicity_log` | G11 atomicity | 0 | **PASS** |
| 33 | `break_atomicity_counter` | G11 atomicity | 0 | **PASS** |
| 34 | `break_forecast_weights` | G12 forecast weighting | 0 | **PASS** |
| 35 | `break_forecast_original_amount` | G12 forecast weighting | 0 | **PASS** |

Baseline suite exit code: 0 (0 = pass).

## Baseline — full suite before any break

```bash
python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"
```

```text
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
```

## Controls

### 1. `break_email_domain` — G1 email/name/source validation

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_email_domain.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_email_domain_requires_an_interior_dot' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-pk9gullq/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_email_domain.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_email_domain_requires_an_interior_dot/
.............................................................................................FFFFFF............
======================================================================
FAIL: test_email_domain_requires_an_interior_dot (test_validation.TestEmailValidation.test_email_domain_requires_an_interior_dot) (email='a@b')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 50, in test_email_domain_requires_an_interior_dot
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_domain_requires_an_interior_dot (test_validation.TestEmailValidation.test_email_domain_requires_an_interior_dot) (email='a@.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 50, in test_email_domain_requires_an_interior_dot
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_domain_requires_an_interior_dot (test_validation.TestEmailValidation.test_email_domain_requires_an_interior_dot) (email='a@com.')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 50, in test_email_domain_requires_an_interior_dot
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_domain_requires_an_interior_dot (test_validation.TestEmailValidation.test_email_domain_requires_an_interior_dot) (email='a@.')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 50, in test_email_domain_requires_an_interior_dot
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_domain_requires_an_interior_dot (test_validation.TestEmailValidation.test_email_domain_requires_an_interior_dot) (email='a@..')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 50, in test_email_domain_requires_an_interior_dot
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_domain_requires_an_interior_dot (test_validation.TestEmailValidation.test_email_domain_requires_an_interior_dot) (email='a@.b.')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 50, in test_email_domain_requires_an_interior_dot
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=6)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 2. `break_email_local` — G1 email/name/source validation

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_email_local.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_email_requires_non_empty_local_part' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-6ms840k6/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_email_local.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_email_requires_non_empty_local_part/
..................................................................................................FF.......
======================================================================
FAIL: test_email_requires_non_empty_local_part (test_validation.TestEmailValidation.test_email_requires_non_empty_local_part) (email='@corp.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 33, in test_email_requires_non_empty_local_part
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_requires_non_empty_local_part (test_validation.TestEmailValidation.test_email_requires_non_empty_local_part) (email='   @corp.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 33, in test_email_requires_non_empty_local_part
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 3. `break_email_at` — G1 email/name/source validation

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_email_at.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_email_requires_exactly_one_at' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xcudym7u/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_email_at.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_email_requires_exactly_one_at/
.................................................................................................FFF........
======================================================================
FAIL: test_email_requires_exactly_one_at (test_validation.TestEmailValidation.test_email_requires_exactly_one_at) (email='a@@b.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 24, in test_email_requires_exactly_one_at
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_requires_exactly_one_at (test_validation.TestEmailValidation.test_email_requires_exactly_one_at) (email='a@b@c.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 24, in test_email_requires_exactly_one_at
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_requires_exactly_one_at (test_validation.TestEmailValidation.test_email_requires_exactly_one_at) (email='a@b.com@c.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 24, in test_email_requires_exactly_one_at
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 4. `break_name` — G1 email/name/source validation

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_name.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_name_must_be_non_empty_string' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-4674retr/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_name.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_name_must_be_non_empty_string/
.F....................................................................................................FFFEEEF...
======================================================================
ERROR: test_name_must_be_non_empty_string (test_validation.TestNameValidation.test_name_must_be_non_empty_string) (name=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 83, in test_name_must_be_non_empty_string
    crm.add_lead("a@corp.com", name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 132, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

======================================================================
ERROR: test_name_must_be_non_empty_string (test_validation.TestNameValidation.test_name_must_be_non_empty_string) (name=42)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 83, in test_name_must_be_non_empty_string
    crm.add_lead("a@corp.com", name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 132, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'int' object has no attribute 'strip'

======================================================================
ERROR: test_name_must_be_non_empty_string (test_validation.TestNameValidation.test_name_must_be_non_empty_string) (name=['Lead'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 83, in test_name_must_be_non_empty_string
    crm.add_lead("a@corp.com", name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 132, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'list' object has no attribute 'strip'

======================================================================
FAIL: test_invalid_payloads_change_nothing (test_atomicity.TestAddLeadAtomicity.test_invalid_payloads_change_nothing) (email='a@corp.com', name='', source='web')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 20, in test_invalid_payloads_change_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_name_must_be_non_empty_string (test_validation.TestNameValidation.test_name_must_be_non_empty_string) (name='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 82, in test_name_must_be_non_empty_string
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_name_must_be_non_empty_string (test_validation.TestNameValidation.test_name_must_be_non_empty_string) (name='   ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 82, in test_name_must_be_non_empty_string
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_name_must_be_non_empty_string (test_validation.TestNameValidation.test_name_must_be_non_empty_string) (name='\t\n')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 82, in test_name_must_be_non_empty_string
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_name_must_be_non_empty_string (test_validation.TestNameValidation.test_name_must_be_non_empty_string) (name=b'Lead')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 82, in test_name_must_be_non_empty_string
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.005s

FAILED (failures=5, errors=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 5. `break_source` — G1 email/name/source validation

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_source.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_source_must_be_allowed_value' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xgsknxhc/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_source.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_source_must_be_allowed_value/
.E..........................................................................................E............EEEEEEE
======================================================================
ERROR: test_invalid_payloads_change_nothing (test_atomicity.TestAddLeadAtomicity.test_invalid_payloads_change_nothing) (email='a@corp.com', name='Lead', source='fax')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 21, in test_invalid_payloads_change_nothing
    crm.add_lead(email, name, source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 121, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'fax'

======================================================================
ERROR: test_source_is_validated_before_duplicate (test_validation.TestDuplicateDetection.test_source_is_validated_before_duplicate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 142, in test_source_is_validated_before_duplicate
    crm.add_lead("a@corp.com", "Other", "fax", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 119, in add_lead
    raise DuplicateLeadError(lead["id"])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_source_must_be_allowed_value (test_validation.TestSourceValidation.test_source_must_be_allowed_value) (source='phone')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 99, in test_source_must_be_allowed_value
    crm.add_lead("a@corp.com", "Lead", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 121, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'phone'

======================================================================
ERROR: test_source_must_be_allowed_value (test_validation.TestSourceValidation.test_source_must_be_allowed_value) (source='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 99, in test_source_must_be_allowed_value
    crm.add_lead("a@corp.com", "Lead", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 121, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: ''

======================================================================
ERROR: test_source_must_be_allowed_value (test_validation.TestSourceValidation.test_source_must_be_allowed_value) (source='WEB')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 99, in test_source_must_be_allowed_value
    crm.add_lead("a@corp.com", "Lead", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 121, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'WEB'

======================================================================
ERROR: test_source_must_be_allowed_value (test_validation.TestSourceValidation.test_source_must_be_allowed_value) (source='web ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 99, in test_source_must_be_allowed_value
    crm.add_lead("a@corp.com", "Lead", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 121, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'web '

======================================================================
ERROR: test_source_must_be_allowed_value (test_validation.TestSourceValidation.test_source_must_be_allowed_value) (source=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 99, in test_source_must_be_allowed_value
    crm.add_lead("a@corp.com", "Lead", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 121, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: None

======================================================================
ERROR: test_source_must_be_allowed_value (test_validation.TestSourceValidation.test_source_must_be_allowed_value) (source=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 99, in test_source_must_be_allowed_value
    crm.add_lead("a@corp.com", "Lead", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 121, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 1

======================================================================
ERROR: test_source_must_be_allowed_value (test_validation.TestSourceValidation.test_source_must_be_allowed_value) (source=['web'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 99, in test_source_must_be_allowed_value
    crm.add_lead("a@corp.com", "Lead", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 121, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 106 tests in 0.005s

FAILED (errors=9)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 6. `break_normalization` — G1 email/name/source validation

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_normalization.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_email_normalized_before_storage' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-pfa_ryid/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_normalization.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_email_normalized_before_storage/
F........................................................................................FFF....F..F.......
======================================================================
FAIL: test_duplicate_changes_nothing (test_atomicity.TestAddLeadAtomicity.test_duplicate_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 28, in test_duplicate_changes_nothing
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_check_uses_normalized_email (test_validation.TestDuplicateDetection.test_duplicate_check_uses_normalized_email) (email='A.B@CORP.COM')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 135, in test_duplicate_check_uses_normalized_email
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_check_uses_normalized_email (test_validation.TestDuplicateDetection.test_duplicate_check_uses_normalized_email) (email='  a.b@corp.com  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 135, in test_duplicate_check_uses_normalized_email
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_raises_with_existing_id (test_validation.TestDuplicateDetection.test_duplicate_raises_with_existing_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 124, in test_duplicate_raises_with_existing_id
    with self.assertRaises(DuplicateLeadError) as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_email_normalized_before_storage (test_validation.TestEmailValidation.test_email_normalized_before_storage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 59, in test_email_normalized_before_storage
    self.assertEqual(lead["email"], "alice@corp.com")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: '  Alice@Corp.COM  ' != 'alice@corp.com'
-   Alice@Corp.COM  
+ alice@corp.com


======================================================================
FAIL: test_email_requires_non_empty_local_part (test_validation.TestEmailValidation.test_email_requires_non_empty_local_part) (email='   @corp.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 33, in test_email_requires_non_empty_local_part
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=6)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 7. `break_free_domain_bonus` — G1 email/name/source validation

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_free_domain_bonus.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_source_controls_score' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5de84qmp/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_free_domain_bonus.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_source_controls_score/
.................................................................FF......................................F.
======================================================================
FAIL: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='web', email='b@corp.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 98, in test_score_below_threshold_rejected
    self.assertEqual(crm.leads[lead_id]["score"], expected_score)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 10 != 25

======================================================================
FAIL: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 108, in test_score_below_threshold_rejected
    self.assertEqual(crm.leads[lead_id]["score"], 35)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 20 != 35

======================================================================
FAIL: test_source_controls_score (test_validation.TestSourceValidation.test_source_controls_score)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 108, in test_source_controls_score
    self.assertEqual(crm.leads[web]["score"], 25)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 10 != 25

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 8. `break_duplicate` — G2 duplicate detection

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_duplicate.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_duplicate_raises_with_existing_id' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-j4oo3wuz/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_duplicate.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_duplicate_raises_with_existing_id/
F..........FFFFFF.............................................................................FFFFF..............
======================================================================
FAIL: test_duplicate_changes_nothing (test_atomicity.TestAddLeadAtomicity.test_duplicate_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 28, in test_duplicate_changes_nothing
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 219, in test_every_failure_preserves_the_log
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        (ValueError, PermissionError, DuplicateLeadError)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>, <class 'crm.DuplicateLeadError'>) not raised

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=2)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('add_lead', 'L2', 'r1')] != [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 3:
('add_lead', 'L2', 'r1')

+ [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')]
- [('add_lead', 'L1', 'r1'),
-  ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
-  ('add_lead', 'L2', 'r1')]

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('add_lead', 'L2', 'r1')] != [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 3:
('add_lead', 'L2', 'r1')

+ [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')]
- [('add_lead', 'L1', 'r1'),
-  ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
-  ('add_lead', 'L2', 'r1')]

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=4)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('add_lead', 'L2', 'r1')] != [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 3:
('add_lead', 'L2', 'r1')

+ [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')]
- [('add_lead', 'L1', 'r1'),
-  ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
-  ('add_lead', 'L2', 'r1')]

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('add_lead', 'L2', 'r1')] != [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 3:
('add_lead', 'L2', 'r1')

+ [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')]
- [('add_lead', 'L1', 'r1'),
-  ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
-  ('add_lead', 'L2', 'r1')]

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=6)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('add_lead', 'L2', 'r1')] != [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 3:
('add_lead', 'L2', 'r1')

+ [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')]
- [('add_lead', 'L1', 'r1'),
-  ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
-  ('add_lead', 'L2', 'r1')]

======================================================================
FAIL: test_duplicate_check_uses_normalized_email (test_validation.TestDuplicateDetection.test_duplicate_check_uses_normalized_email) (email='A.B@CORP.COM')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 135, in test_duplicate_check_uses_normalized_email
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_check_uses_normalized_email (test_validation.TestDuplicateDetection.test_duplicate_check_uses_normalized_email) (email='  a.b@corp.com  ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 135, in test_duplicate_check_uses_normalized_email
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_check_uses_normalized_email (test_validation.TestDuplicateDetection.test_duplicate_check_uses_normalized_email) (email='a.b@corp.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 135, in test_duplicate_check_uses_normalized_email
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_raises_with_existing_id (test_validation.TestDuplicateDetection.test_duplicate_raises_with_existing_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 124, in test_duplicate_raises_with_existing_id
    with self.assertRaises(DuplicateLeadError) as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_failed_duplicate_does_not_consume_id_or_log (test_validation.TestDuplicateDetection.test_failed_duplicate_does_not_consume_id_or_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 147, in test_failed_duplicate_does_not_consume_id_or_log
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.006s

FAILED (failures=12)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 9. `break_assignment_capacity` — G3 rep assignment and capacity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_assignment_capacity.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_full_capacity_queues_lead' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ewr9oetw/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_assignment_capacity.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_full_capacity_queues_lead/
.................F..................F...................E.................F...FFFFFF.F.FF.................
======================================================================
ERROR: test_manager_may_act_on_any_work (test_rules.TestPermissionChecks.test_manager_may_act_on_any_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 82, in test_manager_may_act_on_any_work
    crm.transfer(opp_id, "r1", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 234, in transfer
    raise ValueError("new owner is already the owner")
ValueError: new owner is already the owner

======================================================================
FAIL: test_capacity_failure_leaves_queue_untouched (test_atomicity.TestTransferAtomicity.test_capacity_failure_leaves_queue_untouched)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 181, in test_capacity_failure_leaves_queue_untouched
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_lead_without_owner_cannot_be_converted (test_rules.TestConvert.test_lead_without_owner_cannot_be_converted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 215, in test_lead_without_owner_cannot_be_converted
    self.assertIsNone(crm.leads[queued]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_target_must_have_capacity (test_rules.TestTransfer.test_target_must_have_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 499, in test_target_must_have_capacity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_final_stage_frees_slot_and_assigns_waiting_lead (test_validation.TestAssignmentAndCapacity.test_final_stage_frees_slot_and_assigns_waiting_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 219, in test_final_stage_frees_slot_and_assigns_waiting_lead
    self.assertIsNone(crm.leads[waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_full_capacity_queues_lead (test_validation.TestAssignmentAndCapacity.test_full_capacity_queues_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 200, in test_full_capacity_queues_lead
    self.assertEqual(crm.leads[second]["owner"], "b")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'a' != 'b'
- a
+ b


======================================================================
FAIL: test_lowest_load_wins (test_validation.TestAssignmentAndCapacity.test_lowest_load_wins)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 170, in test_lowest_load_wins
    self.assertEqual(crm.leads[second]["owner"], "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' != 'r2'
- r1
+ r2


======================================================================
FAIL: test_manager_finalization_assigns_waiting_lead_to_the_owner (test_validation.TestAssignmentAndCapacity.test_manager_finalization_assigns_waiting_lead_to_the_owner)
Spec line 31: the drain targets the opportunity owner, not the actor.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 254, in test_manager_finalization_assigns_waiting_lead_to_the_owner
    self.assertIsNone(crm.leads[waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_managers_never_receive_work (test_validation.TestAssignmentAndCapacity.test_managers_never_receive_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 213, in test_managers_never_receive_work
    self.assertIsNone(crm.leads[second]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_open_opportunities_count_against_capacity (test_validation.TestAssignmentAndCapacity.test_open_opportunities_count_against_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 185, in test_open_opportunities_count_against_capacity
    self.assertEqual(crm.leads[second]["owner"], "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' != 'r2'
- r1
+ r2


======================================================================
FAIL: test_qualified_lead_still_counts_and_converted_lead_does_not (test_validation.TestAssignmentAndCapacity.test_qualified_lead_still_counts_and_converted_lead_does_not)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 307, in test_qualified_lead_still_counts_and_converted_lead_does_not
    self.assertIsNone(crm.leads[third]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_waiting_queue_is_fifo_and_drains_multiple_slots (test_validation.TestAssignmentAndCapacity.test_waiting_queue_is_fifo_and_drains_multiple_slots)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 283, in test_waiting_queue_is_fifo_and_drains_multiple_slots
    self.assertIsNone(crm.leads[l3]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_won_frees_slot_and_assigns_waiting_lead (test_validation.TestAssignmentAndCapacity.test_won_frees_slot_and_assigns_waiting_lead)
Spec line 31: every final stage frees the slot, not just 'lost'.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 236, in test_won_frees_slot_and_assigns_waiting_lead
    self.assertIsNone(crm.leads[waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

----------------------------------------------------------------------
Ran 106 tests in 0.005s

FAILED (failures=12, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 10. `break_tie_order` — G3 rep assignment and capacity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_tie_order.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_tie_broken_by_smallest_id' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-2ifsl6i3/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_tie_order.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_tie_broken_by_smallest_id/
..FFEEEE...EE.EEEF.FEEEEEEEEEE.EEEEEEF..EEE..EE..EE.EEF..E......EEEEEEEEEEEEE.EE.FFE.FE...FF..FF.F...................
======================================================================
ERROR: test_final_opportunity_failure_changes_nothing (test_atomicity.TestAdvanceAtomicity.test_final_opportunity_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 109, in test_final_opportunity_failure_changes_nothing
    crm.advance(opp_id, "lost", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_bad_amount_changes_nothing (test_atomicity.TestConvertAtomicity.test_bad_amount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 64, in test_bad_amount_changes_nothing
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_convert_permission_failure_changes_nothing (test_atomicity.TestConvertAtomicity.test_convert_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 75, in test_convert_permission_failure_changes_nothing
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_unqualified_lead_changes_nothing (test_atomicity.TestConvertAtomicity.test_unqualified_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 86, in test_unqualified_lead_changes_nothing
    crm.convert(lead_id, 100, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 165, in convert
    raise PermissionError("actor may not convert this lead")
PermissionError: actor may not convert this lead

======================================================================
ERROR: test_final_stage_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_final_stage_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 145, in test_final_stage_failure_changes_nothing
    crm.advance(opp_id, "lost", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 205, in test_every_failure_preserves_the_log
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_failed_convert_does_not_consume_opp_id (test_atomicity.TestIdCountersAreTransactional.test_failed_convert_does_not_consume_opp_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 197, in test_failed_convert_does_not_consume_opp_id
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_failed_qualify_changes_nothing (test_atomicity.TestQualifyAtomicity.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 37, in test_failed_qualify_changes_nothing
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_low_score_failure_changes_nothing (test_atomicity.TestQualifyAtomicity.test_low_score_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 56, in test_low_score_failure_changes_nothing
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_any_open_stage_may_go_lost (test_rules.TestAdvance.test_any_open_stage_may_go_lost) (steps=())
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 240, in test_any_open_stage_may_go_lost
    crm.advance(opp_id, "lost", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_any_open_stage_may_go_lost (test_rules.TestAdvance.test_any_open_stage_may_go_lost) (steps=('proposal',))
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 239, in test_any_open_stage_may_go_lost
    crm.advance(opp_id, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_any_open_stage_may_go_lost (test_rules.TestAdvance.test_any_open_stage_may_go_lost) (steps=('proposal', 'negotiation'))
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 239, in test_any_open_stage_may_go_lost
    crm.advance(opp_id, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_big_deal_check_only_applies_to_negotiation (test_rules.TestAdvance.test_big_deal_check_only_applies_to_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 334, in test_big_deal_check_only_applies_to_negotiation
    crm.advance(opp_id, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_big_deal_gate_reads_current_amount_after_discount (test_rules.TestAdvance.test_big_deal_gate_reads_current_amount_after_discount)
Spec line 30: the 50000 gate measures the current amount, not the original.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 325, in test_big_deal_gate_reads_current_amount_after_discount
    crm.advance(opp_id, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_big_deal_requires_manager_for_negotiation (test_rules.TestAdvance.test_big_deal_requires_manager_for_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 307, in test_big_deal_requires_manager_for_negotiation
    crm.advance(opp_id, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_big_deal_threshold_is_strictly_greater_than_50000 (test_rules.TestAdvance.test_big_deal_threshold_is_strictly_greater_than_50000)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 317, in test_big_deal_threshold_is_strictly_greater_than_50000
    crm.advance(opp_id, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_final_stage_cannot_advance (test_rules.TestAdvance.test_final_stage_cannot_advance) (final='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 282, in test_final_stage_cannot_advance
    crm.advance(opp_id, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_final_stage_cannot_advance (test_rules.TestAdvance.test_final_stage_cannot_advance) (final='lost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 284, in test_final_stage_cannot_advance
    crm.advance(opp_id, final, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_happy_path_through_won (test_rules.TestAdvance.test_happy_path_through_won)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 229, in test_happy_path_through_won
    crm.advance(opp_id, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_permission_checked_before_final_state (test_rules.TestAdvance.test_permission_checked_before_final_state)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 300, in test_permission_checked_before_final_state
    crm.advance(opp_id, "lost", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=(), target='negotiation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 273, in test_stage_must_be_immediate_next_or_lost
    crm.advance(opp_id, target, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=(), target='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 273, in test_stage_must_be_immediate_next_or_lost
    crm.advance(opp_id, target, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=('proposal',), target='prospect')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 270, in test_stage_must_be_immediate_next_or_lost
    crm.advance(opp_id, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=('proposal',), target='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 270, in test_stage_must_be_immediate_next_or_lost
    crm.advance(opp_id, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=('proposal', 'negotiation'), target='proposal')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 270, in test_stage_must_be_immediate_next_or_lost
    crm.advance(opp_id, stage, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_amount_must_be_positive_int_not_bool (test_rules.TestConvert.test_amount_must_be_positive_int_not_bool)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 148, in test_amount_must_be_positive_int_not_bool
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_failed_conversion_does_not_consume_opp_id (test_rules.TestConvert.test_failed_conversion_does_not_consume_opp_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 206, in test_failed_conversion_does_not_consume_opp_id
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_lead_must_be_qualified (test_rules.TestConvert.test_lead_must_be_qualified)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 165, in test_lead_must_be_qualified
    crm.convert(lead_id, 100, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 165, in convert
    raise PermissionError("actor may not convert this lead")
PermissionError: actor may not convert this lead

======================================================================
ERROR: test_permission_is_checked_before_status (test_rules.TestConvert.test_permission_is_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 178, in test_permission_is_checked_before_status
    crm.convert(lead_id, 100, "r2")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 167, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_successful_conversion_sets_fields_and_log (test_rules.TestConvert.test_successful_conversion_sets_fields_and_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 183, in test_successful_conversion_sets_fields_and_log
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_final_stage_cannot_be_discounted (test_rules.TestDiscount.test_final_stage_cannot_be_discounted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 370, in test_final_stage_cannot_be_discounted
    crm.advance(opp_id, "lost", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_final_stage_is_checked_before_non_manager_cap (test_rules.TestDiscount.test_final_stage_is_checked_before_non_manager_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 423, in test_final_stage_is_checked_before_non_manager_cap
    crm.advance(opp_id, "lost", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_non_manager_discount_cap (test_rules.TestDiscount.test_non_manager_discount_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 381, in test_non_manager_discount_cap
    crm.discount(opp_id, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 219, in discount
    raise PermissionError("actor may not discount this opportunity")
PermissionError: actor may not discount this opportunity

======================================================================
ERROR: test_non_manager_floor_still_applies (test_rules.TestDiscount.test_non_manager_floor_still_applies)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 412, in test_non_manager_floor_still_applies
    crm.discount(opp_id, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 219, in discount
    raise PermissionError("actor may not discount this opportunity")
PermissionError: actor may not discount this opportunity

======================================================================
ERROR: test_permission_checked_before_final_stage (test_rules.TestDiscount.test_permission_checked_before_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 430, in test_permission_checked_before_final_stage
    crm.advance(opp_id, "lost", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_manager_may_act_on_any_work (test_rules.TestPermissionChecks.test_manager_may_act_on_any_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 13, in setUp
    self.crm.qualify(self.lead_id, "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_non_owner_cannot_qualify_a_new_lead (test_rules.TestPermissionChecks.test_non_owner_cannot_qualify_a_new_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 13, in setUp
    self.crm.qualify(self.lead_id, "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_non_owner_rep_cannot_act_on_someone_elses_work (test_rules.TestPermissionChecks.test_non_owner_rep_cannot_act_on_someone_elses_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 13, in setUp
    self.crm.qualify(self.lead_id, "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_qualify_permission_checked_before_score (test_rules.TestPermissionChecks.test_qualify_permission_checked_before_score)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 13, in setUp
    self.crm.qualify(self.lead_id, "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_unknown_actor_is_checked_before_entity_and_payload (test_rules.TestPermissionChecks.test_unknown_actor_is_checked_before_entity_and_payload)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 13, in setUp
    self.crm.qualify(self.lead_id, "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_rules.TestPermissionChecks.test_unknown_actor_rejected_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 13, in setUp
    self.crm.qualify(self.lead_id, "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_converted_lead_cannot_be_qualified (test_rules.TestQualify.test_converted_lead_cannot_be_qualified)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 138, in test_converted_lead_cannot_be_qualified
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_lead_must_be_new (test_rules.TestQualify.test_lead_must_be_new)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 128, in test_lead_must_be_new
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_referral_with_free_domain_meets_threshold (test_rules.TestQualify.test_referral_with_free_domain_meets_threshold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 116, in test_referral_with_free_domain_meets_threshold
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='web', email='a@gmail.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 100, in test_score_below_threshold_rejected
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='web', email='b@corp.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 100, in test_score_below_threshold_rejected
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='event', email='c@gmail.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 100, in test_score_below_threshold_rejected
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 109, in test_score_below_threshold_rejected
    crm.qualify(lead_id, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 149, in qualify
    raise PermissionError("actor may not qualify this lead")
PermissionError: actor may not qualify this lead

======================================================================
ERROR: test_final_opportunity_cannot_be_transferred (test_rules.TestTransfer.test_final_opportunity_cannot_be_transferred)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 479, in test_final_opportunity_cannot_be_transferred
    self.crm.advance(self.opp_id, "lost", "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_manager_permission_checked_before_final_stage (test_rules.TestTransfer.test_manager_permission_checked_before_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 446, in test_manager_permission_checked_before_final_stage
    self.crm.advance(self.opp_id, "lost", "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 193, in advance
    raise PermissionError("actor may not advance this opportunity")
PermissionError: actor may not advance this opportunity

======================================================================
ERROR: test_successful_transfer_updates_owner_and_logs (test_rules.TestTransfer.test_successful_transfer_updates_owner_and_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 505, in test_successful_transfer_updates_owner_and_logs
    self.crm.transfer(self.opp_id, "r2", "m1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 244, in transfer
    raise ValueError("new owner is already the owner")
ValueError: new owner is already the owner

======================================================================
ERROR: test_transfer_to_rep_with_free_capacity_succeeds (test_rules.TestTransfer.test_transfer_to_rep_with_free_capacity_succeeds)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 517, in test_transfer_to_rep_with_free_capacity_succeeds
    crm.transfer(opp_id, "r2", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 244, in transfer
    raise ValueError("new owner is already the owner")
ValueError: new owner is already the owner

======================================================================
FAIL: test_failing_advances_change_nothing (test_atomicity.TestAdvanceAtomicity.test_failing_advances_change_nothing) (stage='proposal', actor='r2')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 102, in test_failing_advances_change_nothing
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_failing_advances_change_nothing (test_atomicity.TestAdvanceAtomicity.test_failing_advances_change_nothing) (stage='won', actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 104, in test_failing_advances_change_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[253 chars] 'proposal'}}, 'log': [('add_lead', 'L1', 'm1'[73 chars]2')]} != {'lea[253 chars] 'prospect'}}, 'log': [('add_lead', 'L1', 'm1'[48 chars]1')]}
Diff is 833 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_qualify_permission_failure_changes_nothing (test_atomicity.TestQualifyAtomicity.test_qualify_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 47, in test_qualify_permission_failure_changes_nothing
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_failing_transfers_change_nothing (test_atomicity.TestTransferAtomicity.test_failing_transfers_change_nothing) (target='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 164, in test_failing_transfers_change_nothing
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_stage_name_is_validated_before_permission (test_rules.TestAdvance.test_stage_name_is_validated_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 294, in test_stage_name_is_validated_before_permission
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_owner_rep_cannot_discount (test_rules.TestDiscount.test_non_owner_rep_cannot_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 364, in test_non_owner_rep_cannot_discount
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_only_manager_may_transfer (test_rules.TestTransfer.test_only_manager_may_transfer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 443, in test_only_manager_may_transfer
    self.assertEqual(self.crm.opps[self.opp_id]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


======================================================================
FAIL: test_same_owner_rejected (test_rules.TestTransfer.test_same_owner_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 484, in test_same_owner_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_target_must_have_capacity (test_rules.TestTransfer.test_target_must_have_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 501, in test_target_must_have_capacity
    self.assertEqual(crm.opps[opp_id]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


======================================================================
FAIL: test_full_capacity_queues_lead (test_validation.TestAssignmentAndCapacity.test_full_capacity_queues_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 199, in test_full_capacity_queues_lead
    self.assertEqual(crm.leads[first]["owner"], "a")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'b' != 'a'
- b
+ a


======================================================================
FAIL: test_lowest_load_wins (test_validation.TestAssignmentAndCapacity.test_lowest_load_wins)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 169, in test_lowest_load_wins
    self.assertEqual(crm.leads[first]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


======================================================================
FAIL: test_open_opportunities_count_against_capacity (test_validation.TestAssignmentAndCapacity.test_open_opportunities_count_against_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 185, in test_open_opportunities_count_against_capacity
    self.assertEqual(crm.leads[second]["owner"], "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' != 'r2'
- r1
+ r2


======================================================================
FAIL: test_owned_leads_never_join_the_waiting_queue (test_validation.TestAssignmentAndCapacity.test_owned_leads_never_join_the_waiting_queue)
Spec step 6: only leads left without an owner join the queue.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 266, in test_owned_leads_never_join_the_waiting_queue
    self.assertEqual(crm.leads[first]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


======================================================================
FAIL: test_tie_broken_by_smallest_id (test_validation.TestAssignmentAndCapacity.test_tie_broken_by_smallest_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 163, in test_tie_broken_by_smallest_id
    self.assertEqual(crm.leads[lead_id]["owner"], "a")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'b' != 'a'
- b
+ a


----------------------------------------------------------------------
Ran 106 tests in 0.011s

FAILED (failures=14, errors=52)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 11. `break_managers_no_work` — G3 rep assignment and capacity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_managers_no_work.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_managers_never_receive_work' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-i30zgf3f/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_managers_no_work.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_managers_never_receive_work/
.........................................................................F........F.......................
======================================================================
FAIL: test_target_must_be_a_rep (test_rules.TestTransfer.test_target_must_be_a_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 466, in test_target_must_be_a_rep
    self.assertEqual(crm.opps[opp_id]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'm1' != 'r1'
- m1
+ r1


======================================================================
FAIL: test_managers_never_receive_work (test_validation.TestAssignmentAndCapacity.test_managers_never_receive_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 212, in test_managers_never_receive_work
    self.assertEqual(crm.leads[first]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'm1' != 'r1'
- m1
+ r1


----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 12. `break_queue_membership` — G3 rep assignment and capacity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_queue_membership.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_owned_leads_never_join_the_waiting_queue' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-wz0h7fn_/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_queue_membership.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_owned_leads_never_join_the_waiting_queue/
.........................F..............................................F...........F.....................
======================================================================
FAIL: test_happy_path_through_won (test_rules.TestAdvance.test_happy_path_through_won)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 231, in test_happy_path_through_won
    self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ('assign', 'L1', 'system') != ('advance', 'O1', 'r1')

First differing element 0:
'assign'
'advance'

- ('assign', 'L1', 'system')
+ ('advance', 'O1', 'r1')

======================================================================
FAIL: test_successful_transfer_updates_owner_and_logs (test_rules.TestTransfer.test_successful_transfer_updates_owner_and_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 507, in test_successful_transfer_updates_owner_and_logs
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        self.crm.log, before_log + [("transfer", self.opp_id, "m1")]
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: Lists differ: [('ad[62 chars]', 'm1'), ('transfer', 'O1', 'm1'), ('assign', 'L1', 'system')] != [('ad[62 chars]', 'm1'), ('transfer', 'O1', 'm1')]

First list contains 1 additional elements.
First extra element 4:
('assign', 'L1', 'system')

  [('add_lead', 'L1', 'm1'),
   ('qualify', 'L1', 'm1'),
   ('convert', 'O1', 'm1'),
-  ('transfer', 'O1', 'm1'),
?                          ^

+  ('transfer', 'O1', 'm1')]
?                          ^

-  ('assign', 'L1', 'system')]

======================================================================
FAIL: test_owned_leads_never_join_the_waiting_queue (test_validation.TestAssignmentAndCapacity.test_owned_leads_never_join_the_waiting_queue)
Spec step 6: only leads left without an owner join the queue.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 270, in test_owned_leads_never_join_the_waiting_queue
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        [entry for entry in crm.log if entry[0] == "assign"], []
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: Lists differ: [('assign', 'L1', 'system')] != []

First list contains 1 additional elements.
First extra element 0:
('assign', 'L1', 'system')

- [('assign', 'L1', 'system')]
+ []

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 13. `break_waiting_queue` — G3 rep assignment and capacity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_waiting_queue.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_final_stage_frees_slot_and_assigns_waiting_lead' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-15kh__9u/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_waiting_queue.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_final_stage_frees_slot_and_assigns_waiting_lead/
..............................................................................F..F.....FF.................
======================================================================
FAIL: test_final_stage_frees_slot_and_assigns_waiting_lead (test_validation.TestAssignmentAndCapacity.test_final_stage_frees_slot_and_assigns_waiting_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 223, in test_final_stage_frees_slot_and_assigns_waiting_lead
    self.assertEqual(crm.leads[waiting]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_manager_finalization_assigns_waiting_lead_to_the_owner (test_validation.TestAssignmentAndCapacity.test_manager_finalization_assigns_waiting_lead_to_the_owner)
Spec line 31: the drain targets the opportunity owner, not the actor.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 259, in test_manager_finalization_assigns_waiting_lead_to_the_owner
    self.assertEqual(crm.leads[waiting]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_waiting_queue_is_fifo_and_drains_multiple_slots (test_validation.TestAssignmentAndCapacity.test_waiting_queue_is_fifo_and_drains_multiple_slots)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 292, in test_waiting_queue_is_fifo_and_drains_multiple_slots
    self.assertEqual(crm.leads[l3]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_won_frees_slot_and_assigns_waiting_lead (test_validation.TestAssignmentAndCapacity.test_won_frees_slot_and_assigns_waiting_lead)
Spec line 31: every final stage frees the slot, not just 'lost'.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 241, in test_won_frees_slot_and_assigns_waiting_lead
    self.assertEqual(crm.leads[waiting]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 14. `break_won_frees_slot` — G3 rep assignment and capacity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_won_frees_slot.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_won_frees_slot_and_assigns_waiting_lead' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-erwl5eu5/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_won_frees_slot.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_won_frees_slot_and_assigns_waiting_lead/
........................................................................................F.................
======================================================================
FAIL: test_won_frees_slot_and_assigns_waiting_lead (test_validation.TestAssignmentAndCapacity.test_won_frees_slot_and_assigns_waiting_lead)
Spec line 31: every final stage frees the slot, not just 'lost'.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 241, in test_won_frees_slot_and_assigns_waiting_lead
    self.assertEqual(crm.leads[waiting]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 106 tests in 0.003s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 15. `break_advance_assign_target` — G3 rep assignment and capacity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_advance_assign_target.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_manager_finalization_assigns_waiting_lead_to_the_owner' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fgb037a0/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_advance_assign_target.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_manager_finalization_assigns_waiting_lead_to_the_owner/
.................................................................................F........................
======================================================================
FAIL: test_manager_finalization_assigns_waiting_lead_to_the_owner (test_validation.TestAssignmentAndCapacity.test_manager_finalization_assigns_waiting_lead_to_the_owner)
Spec line 31: the drain targets the opportunity owner, not the actor.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 259, in test_manager_finalization_assigns_waiting_lead_to_the_owner
    self.assertEqual(crm.leads[waiting]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 106 tests in 0.003s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 16. `break_unknown_actor` — G4 permission checks

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_unknown_actor.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_unknown_actor_rejected_everywhere' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3qn2gg2f/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_unknown_actor.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_unknown_actor_rejected_everywhere/
............................................................EFEEEEE............................................
======================================================================
ERROR: test_unknown_actor_is_checked_before_entity_and_payload (test_rules.TestPermissionChecks.test_unknown_actor_is_checked_before_entity_and_payload)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 34, in test_unknown_actor_is_checked_before_entity_and_payload
    crm.add_lead(None, None, "bogus", "ghost")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 111, in add_lead
    normalized = _normalize_email(email)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 19, in _normalize_email
    raise ValueError("email must be a string")
ValueError: email must be a string

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_rules.TestPermissionChecks.test_unknown_actor_rejected_everywhere) (call=1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 29, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 20, in <lambda>
    lambda: crm.qualify(self.lead_id, "ghost"),
            ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 147, in qualify
    if lead["owner"] != actor and not self._is_manager(actor):
                                      ~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 68, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_rules.TestPermissionChecks.test_unknown_actor_rejected_everywhere) (call=2)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 29, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 21, in <lambda>
    lambda: crm.convert(self.lead_id, 100, "ghost"),
            ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 163, in convert
    if lead["owner"] != actor and not self._is_manager(actor):
                                      ~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 68, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_rules.TestPermissionChecks.test_unknown_actor_rejected_everywhere) (call=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 29, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 22, in <lambda>
    lambda: crm.advance(self.opp_id, "proposal", "ghost"),
            ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 191, in advance
    if opp["owner"] != actor and not self._is_manager(actor):
                                     ~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 68, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_rules.TestPermissionChecks.test_unknown_actor_rejected_everywhere) (call=4)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 29, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 23, in <lambda>
    lambda: crm.discount(self.opp_id, 5, "ghost"),
            ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 217, in discount
    if opp["owner"] != actor and not self._is_manager(actor):
                                     ~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 68, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_rules.TestPermissionChecks.test_unknown_actor_rejected_everywhere) (call=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 29, in test_unknown_actor_rejected_everywhere
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 24, in <lambda>
    lambda: crm.transfer(self.opp_id, "r2", "ghost"),
            ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 235, in transfer
    if not self._is_manager(actor):
           ~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 68, in _is_manager
    return self._users[actor]["role"] == "manager"
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
FAIL: test_unknown_actor_rejected_everywhere (test_rules.TestPermissionChecks.test_unknown_actor_rejected_everywhere) (call=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 28, in test_unknown_actor_rejected_everywhere
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.005s

FAILED (failures=1, errors=6)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 17. `break_non_owner_permission` — G4 permission checks

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_non_owner_permission.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_non_owner_cannot_qualify_a_new_lead' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xjiizjv9/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_non_owner_permission.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_non_owner_cannot_qualify_a_new_lead/
................F........................................FEE..............................................
======================================================================
ERROR: test_non_owner_rep_cannot_act_on_someone_elses_work (test_rules.TestPermissionChecks.test_non_owner_rep_cannot_act_on_someone_elses_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 49, in test_non_owner_rep_cannot_act_on_someone_elses_work
    crm.qualify(self.lead_id, "r2")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 151, in qualify
    raise ValueError("lead is not new")
ValueError: lead is not new

======================================================================
ERROR: test_qualify_permission_checked_before_score (test_rules.TestPermissionChecks.test_qualify_permission_checked_before_score)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 72, in test_qualify_permission_checked_before_score
    crm.qualify(lead_id, "r2")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 153, in qualify
    raise ValueError("lead score is below the qualification threshold")
ValueError: lead score is below the qualification threshold

======================================================================
FAIL: test_qualify_permission_failure_changes_nothing (test_atomicity.TestQualifyAtomicity.test_qualify_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 47, in test_qualify_permission_failure_changes_nothing
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_owner_cannot_qualify_a_new_lead (test_rules.TestPermissionChecks.test_non_owner_cannot_qualify_a_new_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 64, in test_non_owner_cannot_qualify_a_new_lead
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=2, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 18. `break_transfer_manager_only` — G4 permission checks

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_manager_only.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_only_manager_may_transfer' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-u_hnidbw/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_manager_only.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_only_manager_may_transfer/
..................FFFF.......................................F.........EEF...................................
======================================================================
ERROR: test_manager_permission_checked_before_final_stage (test_rules.TestTransfer.test_manager_permission_checked_before_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 448, in test_manager_permission_checked_before_final_stage
    self.crm.transfer(self.opp_id, "r2", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 242, in transfer
    raise ValueError("opportunity is already final")
ValueError: opportunity is already final

======================================================================
ERROR: test_manager_permission_checked_before_target (test_rules.TestTransfer.test_manager_permission_checked_before_target)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 476, in test_manager_permission_checked_before_target
    self.crm.transfer(self.opp_id, "ghost", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 240, in transfer
    raise ValueError("new owner must be a rep")
ValueError: new owner must be a rep

======================================================================
FAIL: test_failing_transfers_change_nothing (test_atomicity.TestTransferAtomicity.test_failing_transfers_change_nothing) (target='r2', actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 164, in test_failing_transfers_change_nothing
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_failing_transfers_change_nothing (test_atomicity.TestTransferAtomicity.test_failing_transfers_change_nothing) (target='ghost', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 166, in test_failing_transfers_change_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[193 chars]': 'r2', 'amount': 1000, 'original_amount': 10[132 chars]1')]} != {'lea[193 chars]': 'r1', 'amount': 1000, 'original_amount': 10[106 chars]1')]}
Diff is 812 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_failing_transfers_change_nothing (test_atomicity.TestTransferAtomicity.test_failing_transfers_change_nothing) (target='m1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 166, in test_failing_transfers_change_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[193 chars]': 'r2', 'amount': 1000, 'original_amount': 10[132 chars]1')]} != {'lea[193 chars]': 'r1', 'amount': 1000, 'original_amount': 10[106 chars]1')]}
Diff is 812 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_failing_transfers_change_nothing (test_atomicity.TestTransferAtomicity.test_failing_transfers_change_nothing) (target='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 164, in test_failing_transfers_change_nothing
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_non_owner_rep_cannot_act_on_someone_elses_work (test_rules.TestPermissionChecks.test_non_owner_rep_cannot_act_on_someone_elses_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 56, in test_non_owner_rep_cannot_act_on_someone_elses_work
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_only_manager_may_transfer (test_rules.TestTransfer.test_only_manager_may_transfer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 441, in test_only_manager_may_transfer
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.006s

FAILED (failures=6, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 19. `break_score` — G5 qualification score threshold

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_score.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_score_below_threshold_rejected' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-e4vs6cxc/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_score.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_score_below_threshold_rejected/
...............F.................................................FFF........................................
======================================================================
FAIL: test_low_score_failure_changes_nothing (test_atomicity.TestQualifyAtomicity.test_low_score_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 55, in test_low_score_failure_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='web', email='a@gmail.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 99, in test_score_below_threshold_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='web', email='b@corp.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 99, in test_score_below_threshold_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='event', email='c@gmail.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 99, in test_score_below_threshold_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 20. `break_stage_transition` — G6 stage-transition rules

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_stage_transition.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_stage_must_be_immediate_next_or_lost' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-n4d1og8j/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_stage_transition.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_stage_must_be_immediate_next_or_lost/
..F.................F.......FFFFF.............................................................................
======================================================================
FAIL: test_failing_advances_change_nothing (test_atomicity.TestAdvanceAtomicity.test_failing_advances_change_nothing) (stage='won', actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 102, in test_failing_advances_change_nothing
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_big_deal_check_only_applies_to_negotiation (test_rules.TestAdvance.test_big_deal_check_only_applies_to_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 336, in test_big_deal_check_only_applies_to_negotiation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=(), target='negotiation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 272, in test_stage_must_be_immediate_next_or_lost
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=(), target='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 272, in test_stage_must_be_immediate_next_or_lost
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=('proposal',), target='prospect')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 272, in test_stage_must_be_immediate_next_or_lost
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=('proposal',), target='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 272, in test_stage_must_be_immediate_next_or_lost
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=('proposal', 'negotiation'), target='proposal')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 272, in test_stage_must_be_immediate_next_or_lost
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=7)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 21. `break_big_deal` — G7 big-deal approval

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_big_deal.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_big_deal_requires_manager_for_negotiation' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-m6quojri/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_big_deal.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_big_deal_requires_manager_for_negotiation/
......................F...................................................................................
======================================================================
FAIL: test_big_deal_requires_manager_for_negotiation (test_rules.TestAdvance.test_big_deal_requires_manager_for_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 308, in test_big_deal_requires_manager_for_negotiation
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.003s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 22. `break_bigdeal_original_amount` — G7 big-deal approval

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_bigdeal_original_amount.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_big_deal_gate_reads_current_amount_after_discount' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-txb367oi/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_bigdeal_original_amount.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_big_deal_gate_reads_current_amount_after_discount/
.....................E....................................................................................
======================================================================
ERROR: test_big_deal_gate_reads_current_amount_after_discount (test_rules.TestAdvance.test_big_deal_gate_reads_current_amount_after_discount)
Spec line 30: the 50000 gate measures the current amount, not the original.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 328, in test_big_deal_gate_reads_current_amount_after_discount
    crm.advance(opp_id, "negotiation", "r1")  # no manager required any more
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 204, in advance
    raise PermissionError("a manager is required for big deals")
PermissionError: a manager is required for big deals

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 23. `break_discount_cap` — G8 discount limits

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_discount_cap.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_non_manager_discount_cap' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-82ij601v/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_discount_cap.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_non_manager_discount_cap/
.........F..................................F.............................................................
======================================================================
FAIL: test_discount_permission_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_discount_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 129, in test_discount_permission_failure_changes_nothing
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_manager_discount_cap (test_rules.TestDiscount.test_non_manager_discount_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 378, in test_non_manager_discount_cap
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 24. `break_pct_range` — G8 discount limits

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_pct_range.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_pct_must_be_int_in_range' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0pvg9m56/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_pct_range.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_pct_must_be_int_in_range/
........F..FF...................................FFFFFFFFE.........................................................
======================================================================
ERROR: test_pct_validated_before_permission (test_rules.TestDiscount.test_pct_validated_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 359, in test_pct_validated_before_permission
    crm.discount(opp_id, 99, "r2")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 219, in discount
    raise PermissionError("actor may not discount this opportunity")
PermissionError: actor may not discount this opportunity

======================================================================
FAIL: test_discount_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_discount_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 121, in test_discount_failure_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 219, in test_every_failure_preserves_the_log
    with self.assertRaises(
         ~~~~~~~~~~~~~~~~~^
        (ValueError, PermissionError, DuplicateLeadError)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>, <class 'crm.DuplicateLeadError'>) not raised

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=6)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('discount', 'O1', 'm1')] != [('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 3:
('discount', 'O1', 'm1')

+ [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')]
- [('add_lead', 'L1', 'r1'),
-  ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
-  ('discount', 'O1', 'm1')]

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 346, in test_pct_must_be_int_in_range
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 346, in test_pct_must_be_int_in_range
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 1010 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=10.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 1010 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 1010 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 1010 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 1010 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 1010 != 1000

----------------------------------------------------------------------
Ran 106 tests in 0.005s

FAILED (failures=11, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 25. `break_discount_floor` — G9 cumulative discount floor

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_discount_floor.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_cumulative_discount_floor_is_enforced' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-sqzleysm/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_discount_floor.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_cumulative_discount_floor_is_enforced/
.......F...............................F.....F............................................................
======================================================================
FAIL: test_cumulative_floor_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_cumulative_floor_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 138, in test_cumulative_floor_failure_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cumulative_discount_floor_is_enforced (test_rules.TestDiscount.test_cumulative_discount_floor_is_enforced)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 398, in test_cumulative_discount_floor_is_enforced
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_non_manager_floor_still_applies (test_rules.TestDiscount.test_non_manager_floor_still_applies)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 416, in test_non_manager_floor_still_applies
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 26. `break_transfer_role` — G10 transfer rules

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_role.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_target_must_be_a_rep' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-y03_heza/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_role.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_target_must_be_a_rep/
.........................................................................F................................
======================================================================
FAIL: test_target_must_be_a_rep (test_rules.TestTransfer.test_target_must_be_a_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 464, in test_target_must_be_a_rep
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 27. `break_transfer_capacity` — G10 transfer rules

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_capacity.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_target_must_have_capacity' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jt13uwpl/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_capacity.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_target_must_have_capacity/
.................F........................................................F...............................
======================================================================
FAIL: test_capacity_failure_leaves_queue_untouched (test_atomicity.TestTransferAtomicity.test_capacity_failure_leaves_queue_untouched)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 181, in test_capacity_failure_leaves_queue_untouched
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_target_must_have_capacity (test_rules.TestTransfer.test_target_must_have_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 499, in test_target_must_have_capacity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 28. `break_transfer_final` — G10 transfer rules

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_final.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_final_opportunity_cannot_be_transferred' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ibjc1nak/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_final.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_final_opportunity_cannot_be_transferred/
...................................................................F......................................
======================================================================
FAIL: test_final_opportunity_cannot_be_transferred (test_rules.TestTransfer.test_final_opportunity_cannot_be_transferred)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 480, in test_final_opportunity_cannot_be_transferred
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 29. `break_transfer_same_owner` — G10 transfer rules

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_same_owner.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_same_owner_rejected' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-yrgexof_/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_transfer_same_owner.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_same_owner_rejected/
..................F....................................................F..................................
======================================================================
FAIL: test_failing_transfers_change_nothing (test_atomicity.TestTransferAtomicity.test_failing_transfers_change_nothing) (target='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 164, in test_failing_transfers_change_nothing
    with self.assertRaises((ValueError, PermissionError)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: (<class 'ValueError'>, <class 'PermissionError'>) not raised

======================================================================
FAIL: test_same_owner_rejected (test_rules.TestTransfer.test_same_owner_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 484, in test_same_owner_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 30. `break_atomicity_discount` — G11 atomicity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_atomicity_discount.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_discount_failure_changes_nothing' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-954m69o7/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_atomicity_discount.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_discount_failure_changes_nothing/
.......EFFF..........E.................EEF.EFE.FFFFFFFFF.......EE.................................................
======================================================================
ERROR: test_cumulative_floor_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_cumulative_floor_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 136, in test_cumulative_floor_failure_changes_nothing
    crm.discount(opp_id, 30, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 227, in discount
    raise ValueError("cumulative discount exceeds 30 percent")
ValueError: cumulative discount exceeds 30 percent

======================================================================
ERROR: test_big_deal_gate_reads_current_amount_after_discount (test_rules.TestAdvance.test_big_deal_gate_reads_current_amount_after_discount)
Spec line 30: the 50000 gate measures the current amount, not the original.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 326, in test_big_deal_gate_reads_current_amount_after_discount
    crm.discount(opp_id, 30, "m1")  # 60000 -> 42000
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 227, in discount
    raise ValueError("cumulative discount exceeds 30 percent")
ValueError: cumulative discount exceeds 30 percent

======================================================================
ERROR: test_cumulative_discount_floor_is_enforced (test_rules.TestDiscount.test_cumulative_discount_floor_is_enforced)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 395, in test_cumulative_discount_floor_is_enforced
    crm.discount(opp_id, 30, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 227, in discount
    raise ValueError("cumulative discount exceeds 30 percent")
ValueError: cumulative discount exceeds 30 percent

======================================================================
ERROR: test_exactly_thirty_percent_total_is_allowed (test_rules.TestDiscount.test_exactly_thirty_percent_total_is_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 406, in test_exactly_thirty_percent_total_is_allowed
    crm.discount(opp_id, 30, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 227, in discount
    raise ValueError("cumulative discount exceeds 30 percent")
ValueError: cumulative discount exceeds 30 percent

======================================================================
ERROR: test_manager_may_discount_up_to_thirty (test_rules.TestDiscount.test_manager_may_discount_up_to_thirty)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 387, in test_manager_may_discount_up_to_thirty
    crm.discount(opp_id, 30, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 227, in discount
    raise ValueError("cumulative discount exceeds 30 percent")
ValueError: cumulative discount exceeds 30 percent

======================================================================
ERROR: test_non_manager_floor_still_applies (test_rules.TestDiscount.test_non_manager_floor_still_applies)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 412, in test_non_manager_floor_still_applies
    crm.discount(opp_id, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 227, in discount
    raise ValueError("cumulative discount exceeds 30 percent")
ValueError: cumulative discount exceeds 30 percent

======================================================================
ERROR: test_weighted_value_uses_current_amount_after_discount (test_rules.TestForecast.test_weighted_value_uses_current_amount_after_discount)
Spec line 42: weighting applies to the current amount, not the original.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 555, in test_weighted_value_uses_current_amount_after_discount
    crm.discount(opp_id, 30, "m1")  # 10000 -> 7000
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 227, in discount
    raise ValueError("cumulative discount exceeds 30 percent")
ValueError: cumulative discount exceeds 30 percent

======================================================================
ERROR: test_manager_may_act_on_any_work (test_rules.TestPermissionChecks.test_manager_may_act_on_any_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 81, in test_manager_may_act_on_any_work
    crm.discount(opp_id, 5, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 227, in discount
    raise ValueError("cumulative discount exceeds 30 percent")
ValueError: cumulative discount exceeds 30 percent

======================================================================
FAIL: test_discount_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_discount_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 123, in test_discount_failure_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[207 chars]nt': -1, 'original_amount': 1000, 'stage': 'pr[90 chars]1')]} != {'lea[207 chars]nt': 1000, 'original_amount': 1000, 'stage': '[92 chars]1')]}
Diff is 701 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_discount_permission_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_discount_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 131, in test_discount_permission_failure_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[207 chars]nt': -1, 'original_amount': 1000, 'stage': 'pr[90 chars]1')]} != {'lea[207 chars]nt': 1000, 'original_amount': 1000, 'stage': '[92 chars]1')]}
Diff is 701 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_final_stage_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_final_stage_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 149, in test_final_stage_failure_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[207 chars]nt': -1, 'original_amount': 1000, 'stage': 'lo[111 chars]1')]} != {'lea[207 chars]nt': 1000, 'original_amount': 1000, 'stage': '[113 chars]1')]}
Diff is 733 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_final_stage_cannot_be_discounted (test_rules.TestDiscount.test_final_stage_cannot_be_discounted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 373, in test_final_stage_cannot_be_discounted
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_non_manager_discount_cap (test_rules.TestDiscount.test_non_manager_discount_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 380, in test_non_manager_discount_cap
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=31)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=10.0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

======================================================================
FAIL: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range) (pct=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 348, in test_pct_must_be_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: -1 != 1000

----------------------------------------------------------------------
Ran 106 tests in 0.007s

FAILED (failures=14, errors=8)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 31. `break_atomicity_convert` — G11 atomicity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_atomicity_convert.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_convert_permission_failure_changes_nothing' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-egax0y43/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_atomicity_convert.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_convert_permission_failure_changes_nothing/
..EE.FFEEEEE.E...EEEEEEEEEEEEEEEEEEEE...E..F.EEEEEEEEEEEE..EEEEEEEEEEE....EEEEEEEEEEEE..E.EE..EE.................
======================================================================
ERROR: test_failing_advances_change_nothing (test_atomicity.TestAdvanceAtomicity.test_failing_advances_change_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 93, in test_failing_advances_change_nothing
    opp_id, _ = make_opp(crm, amount=60000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_final_opportunity_failure_changes_nothing (test_atomicity.TestAdvanceAtomicity.test_final_opportunity_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 108, in test_final_opportunity_failure_changes_nothing
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_cumulative_floor_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_cumulative_floor_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 135, in test_cumulative_floor_failure_changes_nothing
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_discount_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_discount_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 119, in test_discount_failure_changes_nothing
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_discount_permission_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_discount_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 127, in test_discount_permission_failure_changes_nothing
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_final_stage_failure_changes_nothing (test_atomicity.TestDiscountAtomicity.test_final_stage_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 144, in test_final_stage_failure_changes_nothing
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 206, in test_every_failure_preserves_the_log
    opp_id = crm.convert(lead_id, 1000, "r1")
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_failed_convert_does_not_consume_opp_id (test_atomicity.TestIdCountersAreTransactional.test_failed_convert_does_not_consume_opp_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 200, in test_failed_convert_does_not_consume_opp_id
    self.assertEqual(crm.convert(lead_id, 100, "r1"), "O1")
                     ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_capacity_failure_leaves_queue_untouched (test_atomicity.TestTransferAtomicity.test_capacity_failure_leaves_queue_untouched)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 179, in test_capacity_failure_leaves_queue_untouched
    opp_id = crm.convert(first, 1000, "m1")
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_failing_transfers_change_nothing (test_atomicity.TestTransferAtomicity.test_failing_transfers_change_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 155, in test_failing_transfers_change_nothing
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_any_open_stage_may_go_lost (test_rules.TestAdvance.test_any_open_stage_may_go_lost) (steps=())
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 237, in test_any_open_stage_may_go_lost
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_any_open_stage_may_go_lost (test_rules.TestAdvance.test_any_open_stage_may_go_lost) (steps=('proposal',))
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 237, in test_any_open_stage_may_go_lost
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_any_open_stage_may_go_lost (test_rules.TestAdvance.test_any_open_stage_may_go_lost) (steps=('proposal', 'negotiation'))
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 237, in test_any_open_stage_may_go_lost
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_big_deal_check_only_applies_to_negotiation (test_rules.TestAdvance.test_big_deal_check_only_applies_to_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 333, in test_big_deal_check_only_applies_to_negotiation
    opp_id, _ = make_opp(crm, amount=90000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_big_deal_gate_reads_current_amount_after_discount (test_rules.TestAdvance.test_big_deal_gate_reads_current_amount_after_discount)
Spec line 30: the 50000 gate measures the current amount, not the original.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 324, in test_big_deal_gate_reads_current_amount_after_discount
    opp_id, _ = make_opp(crm, amount=60000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_big_deal_requires_manager_for_negotiation (test_rules.TestAdvance.test_big_deal_requires_manager_for_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 306, in test_big_deal_requires_manager_for_negotiation
    opp_id, _ = make_opp(crm, amount=50001)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_big_deal_threshold_is_strictly_greater_than_50000 (test_rules.TestAdvance.test_big_deal_threshold_is_strictly_greater_than_50000)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 316, in test_big_deal_threshold_is_strictly_greater_than_50000
    opp_id, _ = make_opp(crm, amount=50000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_final_stage_cannot_advance (test_rules.TestAdvance.test_final_stage_cannot_advance) (final='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 280, in test_final_stage_cannot_advance
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_final_stage_cannot_advance (test_rules.TestAdvance.test_final_stage_cannot_advance) (final='lost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 280, in test_final_stage_cannot_advance
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_happy_path_through_won (test_rules.TestAdvance.test_happy_path_through_won)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 227, in test_happy_path_through_won
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_invalid_stage_name (test_rules.TestAdvance.test_invalid_stage_name)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 245, in test_invalid_stage_name
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_permission_checked_before_final_state (test_rules.TestAdvance.test_permission_checked_before_final_state)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 299, in test_permission_checked_before_final_state
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=(), target='negotiation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 268, in test_stage_must_be_immediate_next_or_lost
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=(), target='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 268, in test_stage_must_be_immediate_next_or_lost
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=('proposal',), target='prospect')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 268, in test_stage_must_be_immediate_next_or_lost
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=('proposal',), target='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 268, in test_stage_must_be_immediate_next_or_lost
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_stage_must_be_immediate_next_or_lost (test_rules.TestAdvance.test_stage_must_be_immediate_next_or_lost) (steps=('proposal', 'negotiation'), target='proposal')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 268, in test_stage_must_be_immediate_next_or_lost
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_stage_name_is_validated_before_permission (test_rules.TestAdvance.test_stage_name_is_validated_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 291, in test_stage_name_is_validated_before_permission
    opp_id, _ = make_opp(crm)
                ~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_failed_conversion_does_not_consume_opp_id (test_rules.TestConvert.test_failed_conversion_does_not_consume_opp_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 209, in test_failed_conversion_does_not_consume_opp_id
    self.assertEqual(crm.convert(lead_id, 100, "r1"), "O1")
                     ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_successful_conversion_sets_fields_and_log (test_rules.TestConvert.test_successful_conversion_sets_fields_and_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 184, in test_successful_conversion_sets_fields_and_log
    opp_id = crm.convert(lead_id, 1234, "r1")
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_cumulative_discount_floor_is_enforced (test_rules.TestDiscount.test_cumulative_discount_floor_is_enforced)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 394, in test_cumulative_discount_floor_is_enforced
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_exactly_thirty_percent_total_is_allowed (test_rules.TestDiscount.test_exactly_thirty_percent_total_is_allowed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 405, in test_exactly_thirty_percent_total_is_allowed
    opp_id, _ = make_opp(crm, amount=100)
                ~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_final_stage_cannot_be_discounted (test_rules.TestDiscount.test_final_stage_cannot_be_discounted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 369, in test_final_stage_cannot_be_discounted
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_final_stage_is_checked_before_non_manager_cap (test_rules.TestDiscount.test_final_stage_is_checked_before_non_manager_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 422, in test_final_stage_is_checked_before_non_manager_cap
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_manager_may_discount_up_to_thirty (test_rules.TestDiscount.test_manager_may_discount_up_to_thirty)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 386, in test_manager_may_discount_up_to_thirty
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_non_manager_discount_cap (test_rules.TestDiscount.test_non_manager_discount_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 377, in test_non_manager_discount_cap
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_non_manager_floor_still_applies (test_rules.TestDiscount.test_non_manager_floor_still_applies)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 411, in test_non_manager_floor_still_applies
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_non_owner_rep_cannot_discount (test_rules.TestDiscount.test_non_owner_rep_cannot_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 363, in test_non_owner_rep_cannot_discount
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_pct_must_be_int_in_range (test_rules.TestDiscount.test_pct_must_be_int_in_range)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 343, in test_pct_must_be_int_in_range
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_pct_validated_before_permission (test_rules.TestDiscount.test_pct_validated_before_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 357, in test_pct_validated_before_permission
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_permission_checked_before_final_stage (test_rules.TestDiscount.test_permission_checked_before_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 429, in test_permission_checked_before_final_stage
    opp_id, _ = make_opp(crm, amount=1000)
                ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_final_stages_excluded_and_won_summed (test_rules.TestForecast.test_final_stages_excluded_and_won_summed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 540, in test_final_stages_excluded_and_won_summed
    o1, _ = make_opp(crm, amount=100, email="a@corp.com")
            ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_forecast_does_not_log (test_rules.TestForecast.test_forecast_does_not_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 561, in test_forecast_does_not_log
    make_opp(crm, amount=1000)
    ~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_weighted_value_by_stage (test_rules.TestForecast.test_weighted_value_by_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 527, in test_weighted_value_by_stage
    o1, _ = make_opp(crm, amount=105, email="a@corp.com")
            ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_weighted_value_uses_current_amount_after_discount (test_rules.TestForecast.test_weighted_value_uses_current_amount_after_discount)
Spec line 42: weighting applies to the current amount, not the original.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 553, in test_weighted_value_uses_current_amount_after_discount
    opp_id, _ = make_opp(crm, amount=10000, email="a@corp.com")
                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_manager_may_act_on_any_work (test_rules.TestPermissionChecks.test_manager_may_act_on_any_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 14, in setUp
    self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")
                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_non_owner_cannot_qualify_a_new_lead (test_rules.TestPermissionChecks.test_non_owner_cannot_qualify_a_new_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 14, in setUp
    self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")
                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_non_owner_rep_cannot_act_on_someone_elses_work (test_rules.TestPermissionChecks.test_non_owner_rep_cannot_act_on_someone_elses_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 14, in setUp
    self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")
                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_qualify_permission_checked_before_score (test_rules.TestPermissionChecks.test_qualify_permission_checked_before_score)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 14, in setUp
    self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")
                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_unknown_actor_is_checked_before_entity_and_payload (test_rules.TestPermissionChecks.test_unknown_actor_is_checked_before_entity_and_payload)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 14, in setUp
    self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")
                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_unknown_actor_rejected_everywhere (test_rules.TestPermissionChecks.test_unknown_actor_rejected_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 14, in setUp
    self.opp_id = self.crm.convert(self.lead_id, 1000, "r1")
                  ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_converted_lead_cannot_be_qualified (test_rules.TestQualify.test_converted_lead_cannot_be_qualified)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 139, in test_converted_lead_cannot_be_qualified
    crm.convert(lead_id, 1000, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_final_opportunity_cannot_be_transferred (test_rules.TestTransfer.test_final_opportunity_cannot_be_transferred)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_manager_permission_checked_before_final_stage (test_rules.TestTransfer.test_manager_permission_checked_before_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_manager_permission_checked_before_target (test_rules.TestTransfer.test_manager_permission_checked_before_target)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_only_manager_may_transfer (test_rules.TestTransfer.test_only_manager_may_transfer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_same_owner_rejected (test_rules.TestTransfer.test_same_owner_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_successful_transfer_updates_owner_and_logs (test_rules.TestTransfer.test_successful_transfer_updates_owner_and_logs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_target_must_be_a_rep (test_rules.TestTransfer.test_target_must_be_a_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_target_must_have_capacity (test_rules.TestTransfer.test_target_must_have_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_transfer_to_rep_with_free_capacity_succeeds (test_rules.TestTransfer.test_transfer_to_rep_with_free_capacity_succeeds)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_unknown_opportunity (test_rules.TestTransfer.test_unknown_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_unknown_target (test_rules.TestTransfer.test_unknown_target)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 438, in setUp
    self.opp_id, self.lead_id = make_opp(self.crm, amount=1000)
                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm_fixtures.py", line 27, in make_opp
    opp_id = crm.convert(lead_id, amount, actor)
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_final_stage_frees_slot_and_assigns_waiting_lead (test_validation.TestAssignmentAndCapacity.test_final_stage_frees_slot_and_assigns_waiting_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 221, in test_final_stage_frees_slot_and_assigns_waiting_lead
    opp_id = crm.convert(first, 1000, "r1")
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_manager_finalization_assigns_waiting_lead_to_the_owner (test_validation.TestAssignmentAndCapacity.test_manager_finalization_assigns_waiting_lead_to_the_owner)
Spec line 31: the drain targets the opportunity owner, not the actor.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 256, in test_manager_finalization_assigns_waiting_lead_to_the_owner
    opp_id = crm.convert(first, 1000, "m1")
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_open_opportunities_count_against_capacity (test_validation.TestAssignmentAndCapacity.test_open_opportunities_count_against_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 182, in test_open_opportunities_count_against_capacity
    crm.convert(first, 1000, "m1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_owned_leads_never_join_the_waiting_queue (test_validation.TestAssignmentAndCapacity.test_owned_leads_never_join_the_waiting_queue)
Spec step 6: only leads left without an owner join the queue.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 268, in test_owned_leads_never_join_the_waiting_queue
    opp_id = crm.convert(first, 1000, "r1")
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_waiting_queue_is_fifo_and_drains_multiple_slots (test_validation.TestAssignmentAndCapacity.test_waiting_queue_is_fifo_and_drains_multiple_slots)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 287, in test_waiting_queue_is_fifo_and_drains_multiple_slots
    o1 = crm.convert(l1, 1000, "r1")
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
ERROR: test_won_frees_slot_and_assigns_waiting_lead (test_validation.TestAssignmentAndCapacity.test_won_frees_slot_and_assigns_waiting_lead)
Spec line 31: every final stage frees the slot, not just 'lost'.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 238, in test_won_frees_slot_and_assigns_waiting_lead
    opp_id = crm.convert(first, 1000, "r1")
  File "/tmp/aep-lab/pilot2/AE-neutral-2/crm.py", line 168, in convert
    raise ValueError("lead is not qualified")
ValueError: lead is not qualified

======================================================================
FAIL: test_convert_permission_failure_changes_nothing (test_atomicity.TestConvertAtomicity.test_convert_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 79, in test_convert_permission_failure_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[120 chars]s': 'converted'}}, 'opps': {}, 'log': [('add_l[39 chars]1')]} != {'lea[120 chars]s': 'qualified'}}, 'opps': {}, 'log': [('add_l[39 chars]1')]}
  {'leads': {'L1': {'email': 'a@corp.com',
                    'id': 'L1',
                    'name': 'Lead',
                    'owner': 'r1',
                    'score': 45,
                    'source': 'referral',
-                   'status': 'converted'}},
?                              ^^^^^^^

+                   'status': 'qualified'}},
?                              ^^^^^^^

   'log': [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')],
   'opps': {}}

======================================================================
FAIL: test_unqualified_lead_changes_nothing (test_atomicity.TestConvertAtomicity.test_unqualified_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 87, in test_unqualified_lead_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[120 chars]s': 'converted'}}, 'opps': {}, 'log': [('add_l[14 chars]1')]} != {'lea[120 chars]s': 'new'}}, 'opps': {}, 'log': [('add_lead', 'L1', 'r1')]}
  {'leads': {'L1': {'email': 'a@corp.com',
                    'id': 'L1',
                    'name': 'Lead',
                    'owner': 'r1',
                    'score': 45,
                    'source': 'referral',
-                   'status': 'converted'}},
?                              -- - ^^^^

+                   'status': 'new'}},
?                                ^

   'log': [('add_lead', 'L1', 'r1')],
   'opps': {}}

======================================================================
FAIL: test_lead_without_owner_cannot_be_converted (test_rules.TestConvert.test_lead_without_owner_cannot_be_converted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 220, in test_lead_without_owner_cannot_be_converted
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[246 chars]s': 'converted'}}, 'opps': {}, 'log': [('add_l[65 chars]1')]} != {'lea[246 chars]s': 'qualified'}}, 'opps': {}, 'log': [('add_l[65 chars]1')]}
Diff is 776 characters long. Set self.maxDiff to None to see it.

----------------------------------------------------------------------
Ran 106 tests in 0.015s

FAILED (failures=3, errors=69)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 32. `break_atomicity_log` — G11 atomicity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_atomicity_log.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_qualify_permission_failure_changes_nothing' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-e8wsu4hq/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_atomicity_log.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_qualify_permission_failure_changes_nothing/
...........FFFFF..FFF..............................................F.FFF........................................
======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=2)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1'), ('qualify', 'L1', 'r1')] != [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 4:
('qualify', 'L1', 'r1')

  [('add_lead', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
?                         ^

+  ('convert', 'O1', 'r1')]
?                         ^

-  ('qualify', 'L1', 'r1')]

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1'), ('qualify', 'L1', 'r1')] != [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 4:
('qualify', 'L1', 'r1')

  [('add_lead', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
?                         ^

+  ('convert', 'O1', 'r1')]
?                         ^

-  ('qualify', 'L1', 'r1')]

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=4)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1'), ('qualify', 'L1', 'r1')] != [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 4:
('qualify', 'L1', 'r1')

  [('add_lead', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
?                         ^

+  ('convert', 'O1', 'r1')]
?                         ^

-  ('qualify', 'L1', 'r1')]

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1'), ('qualify', 'L1', 'r1')] != [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 4:
('qualify', 'L1', 'r1')

  [('add_lead', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
?                         ^

+  ('convert', 'O1', 'r1')]
?                         ^

-  ('qualify', 'L1', 'r1')]

======================================================================
FAIL: test_every_failure_preserves_the_log (test_atomicity.TestIdCountersAreTransactional.test_every_failure_preserves_the_log) (call=6)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 223, in test_every_failure_preserves_the_log
    self.assertEqual(crm.log, before_log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1'), ('qualify', 'L1', 'r1')] != [('ad[58 chars] 'L1', 'r1'), ('convert', 'O1', 'r1')]

First list contains 1 additional elements.
First extra element 4:
('qualify', 'L1', 'r1')

  [('add_lead', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
-  ('convert', 'O1', 'r1'),
?                         ^

+  ('convert', 'O1', 'r1')]
?                         ^

-  ('qualify', 'L1', 'r1')]

======================================================================
FAIL: test_failed_qualify_changes_nothing (test_atomicity.TestQualifyAtomicity.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 41, in test_failed_qualify_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[197 chars]'L1', 'r1'), ('qualify', 'L1', 'r1'), ('qualify', 'L1', 'r1')]} != {'lea[197 chars]'L1', 'r1'), ('qualify', 'L1', 'r1')]}
  {'leads': {'L1': {'email': 'a@corp.com',
                    'id': 'L1',
                    'name': 'Lead',
                    'owner': 'r1',
                    'score': 45,
                    'source': 'referral',
                    'status': 'qualified'}},
   'log': [('add_lead', 'L1', 'r1'),
           ('qualify', 'L1', 'r1'),
-          ('qualify', 'L1', 'r1'),
           ('qualify', 'L1', 'r1')],
   'opps': {}}

======================================================================
FAIL: test_low_score_failure_changes_nothing (test_atomicity.TestQualifyAtomicity.test_low_score_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 57, in test_low_score_failure_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[137 chars]{}, 'log': [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')]} != {'lea[137 chars]{}, 'log': [('add_lead', 'L1', 'r1')]}
  {'leads': {'L1': {'email': 'a@gmail.com',
                    'id': 'L1',
                    'name': 'Lead',
                    'owner': 'r1',
                    'score': 10,
                    'source': 'web',
                    'status': 'new'}},
-  'log': [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')],
+  'log': [('add_lead', 'L1', 'r1')],
   'opps': {}}

======================================================================
FAIL: test_qualify_permission_failure_changes_nothing (test_atomicity.TestQualifyAtomicity.test_qualify_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 49, in test_qualify_permission_failure_changes_nothing
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'lea[141 chars]{}, 'log': [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r2')]} != {'lea[141 chars]{}, 'log': [('add_lead', 'L1', 'r1')]}
  {'leads': {'L1': {'email': 'a@corp.com',
                    'id': 'L1',
                    'name': 'Lead',
                    'owner': 'r1',
                    'score': 45,
                    'source': 'referral',
                    'status': 'new'}},
-  'log': [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r2')],
+  'log': [('add_lead', 'L1', 'r1')],
   'opps': {}}

======================================================================
FAIL: test_lead_must_be_new (test_rules.TestQualify.test_lead_must_be_new)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 131, in test_lead_must_be_new
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.log.count(("qualify", lead_id, "r1")), 1
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: 3 != 1

======================================================================
FAIL: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='web', email='a@gmail.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 102, in test_score_below_threshold_rejected
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.log, [("add_lead", lead_id, "r1")]
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: Lists differ: [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')] != [('add_lead', 'L1', 'r1')]

First list contains 1 additional elements.
First extra element 1:
('qualify', 'L1', 'r1')

- [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')]
+ [('add_lead', 'L1', 'r1')]

======================================================================
FAIL: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='web', email='b@corp.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 102, in test_score_below_threshold_rejected
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.log, [("add_lead", lead_id, "r1")]
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: Lists differ: [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')] != [('add_lead', 'L1', 'r1')]

First list contains 1 additional elements.
First extra element 1:
('qualify', 'L1', 'r1')

- [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')]
+ [('add_lead', 'L1', 'r1')]

======================================================================
FAIL: test_score_below_threshold_rejected (test_rules.TestQualify.test_score_below_threshold_rejected) (source='event', email='c@gmail.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 102, in test_score_below_threshold_rejected
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.log, [("add_lead", lead_id, "r1")]
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: Lists differ: [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')] != [('add_lead', 'L1', 'r1')]

First list contains 1 additional elements.
First extra element 1:
('qualify', 'L1', 'r1')

- [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1')]
+ [('add_lead', 'L1', 'r1')]

----------------------------------------------------------------------
Ran 106 tests in 0.006s

FAILED (failures=12)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 33. `break_atomicity_counter` — G11 atomicity

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_atomicity_counter.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_failed_add_does_not_consume_lead_id' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5jy5acjw/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_atomicity_counter.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_failed_add_does_not_consume_lead_id/
............F..............................................................................F.......F......
======================================================================
FAIL: test_failed_add_does_not_consume_lead_id (test_atomicity.TestIdCountersAreTransactional.test_failed_add_does_not_consume_lead_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_atomicity.py", line 192, in test_failed_add_does_not_consume_lead_id
    self.assertEqual(crm.add_lead("a@corp.com", "Lead", "web", "r1"), "L1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'L3' != 'L1'
- L3
+ L1


======================================================================
FAIL: test_failed_duplicate_does_not_consume_id_or_log (test_validation.TestDuplicateDetection.test_failed_duplicate_does_not_consume_id_or_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 150, in test_failed_duplicate_does_not_consume_id_or_log
    self.assertEqual(second, "L2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
AssertionError: 'L5' != 'L2'
- L5
+ L2


======================================================================
FAIL: test_failed_validation_does_not_consume_lead_id (test_validation.TestEmailValidation.test_failed_validation_does_not_consume_lead_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_validation.py", line 74, in test_failed_validation_does_not_consume_lead_id
    self.assertEqual(crm.add_lead("a@b.com", "Lead", "web", "r1"), "L1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'L3' != 'L1'
- L3
+ L1


----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 34. `break_forecast_weights` — G12 forecast weighting

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_forecast_weights.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_weighted_value_by_stage' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-p961m02g/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_forecast_weights.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_weighted_value_by_stage/
......................................................F...................................................
======================================================================
FAIL: test_weighted_value_by_stage (test_rules.TestForecast.test_weighted_value_by_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 533, in test_weighted_value_by_stage
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.forecast(), {"open": 3, "weighted": 10 + 60 + 180, "won": 0}
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
AssertionError: {'open': 3, 'weighted': 240, 'won': 0} != {'open': 3, 'weighted': 250, 'won': 0}
- {'open': 3, 'weighted': 240, 'won': 0}
?                          ^

+ {'open': 3, 'weighted': 250, 'won': 0}
?                          ^


----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

### 35. `break_forecast_original_amount` — G12 forecast weighting

Command:

```bash
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-2/crm.py --break-cmd 'python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_forecast_original_amount.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"' --expect 'test_weighted_value_uses_current_amount_after_discount' --timeout 20
```

Verbatim output:

```text
$ backed up /tmp/aep-lab/pilot2/AE-neutral-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-y414d0ok/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-neutral-2/breaks/break_forecast_original_amount.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect FAILURE matching /test_weighted_value_uses_current_amount_after_discount/
.......................................................F..................................................
======================================================================
FAIL: test_weighted_value_uses_current_amount_after_discount (test_rules.TestForecast.test_weighted_value_uses_current_amount_after_discount)
Spec line 42: weighting applies to the current amount, not the original.
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-neutral-2/test_rules.py", line 557, in test_weighted_value_uses_current_amount_after_discount
    self.assertEqual(crm.forecast(), {"open": 1, "weighted": 2100, "won": 0})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'open': 1, 'weighted': 3000, 'won': 0} != {'open': 1, 'weighted': 2100, 'won': 0}
- {'open': 1, 'weighted': 3000, 'won': 0}
?                         ^^

+ {'open': 1, 'weighted': 2100, 'won': 0}
?                         ^^


----------------------------------------------------------------------
Ran 106 tests in 0.004s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-neutral-2 -p "test*.py"   # expect SUCCESS
..........................................................................................................
----------------------------------------------------------------------
Ran 106 tests in 0.003s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: **0** — **PASS**.

