# Negative-control log

Project: /tmp/aep-lab/pilot2/AE-neutral-1
Tool: /tmp/aep-lab/v060/bin/aepkit
Mutator: mutate.py (applies one named guard removal to crm.py)
Date: 2026-10-25T07:25:16Z

Each control backs up `crm.py`, removes exactly one guard, runs the targeted
test (it must fail with output matching `FAILED`), restores `crm.py` from the
backup, and re-runs the same test (it must pass).

## 1. Email validation: exactly one @

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py email_format" --test-cmd "python3 -m unittest test_crm.ValidationTests.test_email_requires_exactly_one_at" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-yrfkz6vs/crm.py
$ python3 mutate.py email_format
applied email_format
$ python3 -m unittest test_crm.ValidationTests.test_email_requires_exactly_one_at   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_email_requires_exactly_one_at (test_crm.ValidationTests.test_email_requires_exactly_one_at)
----------------------------------------------------------------------
ValueError: not enough values to unpack (expected 2, got 1)

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 43, in test_email_requires_exactly_one_at
    with self.assertRaisesRegex(ValueError, "exactly one @"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: "exactly one @" does not match "not enough values to unpack (expected 2, got 1)"

----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ValidationTests.test_email_requires_exactly_one_at   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 2. Email validation: must be a str

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py email_is_str" --test-cmd "python3 -m unittest test_crm.ValidationTests.test_email_must_be_string" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-cw4avsye/crm.py
$ python3 mutate.py email_is_str
applied email_is_str
$ python3 -m unittest test_crm.ValidationTests.test_email_must_be_string   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_email_must_be_string (test_crm.ValidationTests.test_email_must_be_string)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 37, in test_email_must_be_string
    self.crm.add_lead(bad, "N", "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 119, in add_lead
    normalized = email.strip().lower()
                 ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ValidationTests.test_email_must_be_string   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 3. Name validation

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py name_required" --test-cmd "python3 -m unittest test_crm.ValidationTests.test_name_required" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-trhl76kx/crm.py
$ python3 mutate.py name_required
applied name_required
$ python3 -m unittest test_crm.ValidationTests.test_name_required   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_name_required (test_crm.ValidationTests.test_name_required)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 57, in test_name_required
    with self.assertRaisesRegex(ValueError, "name"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ValidationTests.test_name_required   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 4. Source validation

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py source_enum" --test-cmd "python3 -m unittest test_crm.ValidationTests.test_source_enum" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-irhco3et/crm.py
$ python3 mutate.py source_enum
applied source_enum
$ python3 -m unittest test_crm.ValidationTests.test_source_enum   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_source_enum (test_crm.ValidationTests.test_source_enum)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 65, in test_source_enum
    self.crm.add_lead("a@b.com", "N", bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 143, in add_lead
    score = BASE_SCORES[source]
            ~~~~~~~~~~~^^^^^^^^
KeyError: 'tv'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ValidationTests.test_source_enum   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 5. Duplicate detection

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py duplicate_check" --test-cmd "python3 -m unittest test_crm.DuplicateTests.test_duplicate_email_raises_with_existing_id" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-mb9dt6gu/crm.py
$ python3 mutate.py duplicate_check
applied duplicate_check
$ python3 -m unittest test_crm.DuplicateTests.test_duplicate_email_raises_with_existing_id   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_duplicate_email_raises_with_existing_id (test_crm.DuplicateTests.test_duplicate_email_raises_with_existing_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 120, in test_duplicate_email_raises_with_existing_id
    with self.assertRaises(DuplicateLeadError) as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.DuplicateTests.test_duplicate_email_raises_with_existing_id   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 6. Rep assignment: lowest load, smallest id

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py assign_lowest_load" --test-cmd "python3 -m unittest test_crm.AssignmentTests.test_lowest_load_then_smallest_id" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-67fio05f/crm.py
$ python3 mutate.py assign_lowest_load
applied assign_lowest_load
$ python3 -m unittest test_crm.AssignmentTests.test_lowest_load_then_smallest_id   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_lowest_load_then_smallest_id (test_crm.AssignmentTests.test_lowest_load_then_smallest_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 138, in test_lowest_load_then_smallest_id
    self.assertEqual([crm.leads[i]["owner"] for i in ids], ["r1", "r2", "r1", "r2"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ['r1', 'r1', 'r1', 'r1'] != ['r1', 'r2', 'r1', 'r2']

First differing element 1:
'r1'
'r2'

- ['r1', 'r1', 'r1', 'r1']
+ ['r1', 'r2', 'r1', 'r2']

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AssignmentTests.test_lowest_load_then_smallest_id   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 7. Rep assignment: capacity enforcement

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py assign_capacity" --test-cmd "python3 -m unittest test_crm.AssignmentTests.test_capacity_enforced" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-q6l1cdz1/crm.py
$ python3 mutate.py assign_capacity
applied assign_capacity
$ python3 -m unittest test_crm.AssignmentTests.test_capacity_enforced   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_capacity_enforced (test_crm.AssignmentTests.test_capacity_enforced)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 150, in test_capacity_enforced
    self.assertIsNone(crm.leads[second]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AssignmentTests.test_capacity_enforced   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 8. Rep assignment: only role rep receives work

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py rep_role_skip" --test-cmd "python3 -m unittest test_crm.AssignmentTests.test_manager_never_owns" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8k58s1h6/crm.py
$ python3 mutate.py rep_role_skip
applied rep_role_skip
$ python3 -m unittest test_crm.AssignmentTests.test_manager_never_owns   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_manager_never_owns (test_crm.AssignmentTests.test_manager_never_owns)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 143, in test_manager_never_owns
    self.assertIsNone(crm.leads[lid]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'm1' is not None

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AssignmentTests.test_manager_never_owns   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 9. Rep assignment: waiting queue FIFO refill

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py refill_queue" --test-cmd "python3 -m unittest test_crm.AssignmentTests.test_waiting_queue_fifo_and_refill" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bj4wot_n/crm.py
$ python3 mutate.py refill_queue
applied refill_queue
$ python3 -m unittest test_crm.AssignmentTests.test_waiting_queue_fifo_and_refill   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_waiting_queue_fifo_and_refill (test_crm.AssignmentTests.test_waiting_queue_fifo_and_refill)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 165, in test_waiting_queue_fifo_and_refill
    self.assertEqual(crm.leads[second]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AssignmentTests.test_waiting_queue_fifo_and_refill   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 10. Permission: unknown actor checked first

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py actor_known" --test-cmd "python3 -m unittest test_crm.PermissionTests.test_unknown_actor_is_permission_error_first" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-wlr9qzsg/crm.py
$ python3 mutate.py actor_known
applied actor_known
$ python3 -m unittest test_crm.PermissionTests.test_unknown_actor_is_permission_error_first   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_unknown_actor_is_permission_error_first (test_crm.PermissionTests.test_unknown_actor_is_permission_error_first)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 187, in test_unknown_actor_is_permission_error_first
    self.crm.qualify("L404", "ghost")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 166, in qualify
    raise ValueError("unknown lead: %r" % (lead_id,))
ValueError: unknown lead: 'L404'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.PermissionTests.test_unknown_actor_is_permission_error_first   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 11. Permission: qualify owner-or-manager

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py qualify_permission" --test-cmd "python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_qualify" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-hs4nv111/crm.py
$ python3 mutate.py qualify_permission
applied qualify_permission
$ python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_qualify   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_non_owner_rep_cannot_qualify (test_crm.PermissionTests.test_non_owner_rep_cannot_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 204, in test_non_owner_rep_cannot_qualify
    self.crm.qualify(self.lid, "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 170, in qualify
    raise ValueError("lead is not new")
ValueError: lead is not new

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_qualify   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 12. Permission: convert owner-or-manager (F1)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py convert_permission" --test-cmd "python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_convert" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-gfioibrf/crm.py
$ python3 mutate.py convert_permission
applied convert_permission
$ python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_convert   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_non_owner_rep_cannot_convert (test_crm.PermissionTests.test_non_owner_rep_cannot_convert)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 232, in test_non_owner_rep_cannot_convert
    with self.assertRaisesRegex(PermissionError, "convert"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_convert   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 13. Permission: advance owner-or-manager

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py advance_permission" --test-cmd "python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_advance" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-er1vyaes/crm.py
$ python3 mutate.py advance_permission
applied advance_permission
$ python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_advance   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_non_owner_rep_cannot_advance (test_crm.PermissionTests.test_non_owner_rep_cannot_advance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 208, in test_non_owner_rep_cannot_advance
    with self.assertRaisesRegex(PermissionError, "advance"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_advance   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 14. Permission: discount owner-or-manager

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py discount_permission" --test-cmd "python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_discount" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-wj77pthy/crm.py
$ python3 mutate.py discount_permission
applied discount_permission
$ python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_discount   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_non_owner_rep_cannot_discount (test_crm.PermissionTests.test_non_owner_rep_cannot_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 213, in test_non_owner_rep_cannot_discount
    with self.assertRaisesRegex(PermissionError, "discount"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.PermissionTests.test_non_owner_rep_cannot_discount   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 15. Permission: transfer manager-only

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py transfer_manager" --test-cmd "python3 -m unittest test_crm.TransferTests.test_only_manager_can_transfer" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-6pog5ilt/crm.py
$ python3 mutate.py transfer_manager
applied transfer_manager
$ python3 -m unittest test_crm.TransferTests.test_only_manager_can_transfer   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_only_manager_can_transfer (test_crm.TransferTests.test_only_manager_can_transfer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 487, in test_only_manager_can_transfer
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.TransferTests.test_only_manager_can_transfer   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 16. Qualification: score threshold

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py qualify_score" --test-cmd "python3 -m unittest test_crm.QualifyTests.test_score_below_threshold_rejected" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-owr601d0/crm.py
$ python3 mutate.py qualify_score
applied qualify_score
$ python3 -m unittest test_crm.QualifyTests.test_score_below_threshold_rejected   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_score_below_threshold_rejected (test_crm.QualifyTests.test_score_below_threshold_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 263, in test_score_below_threshold_rejected
    with self.assertRaisesRegex(ValueError, "score"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.QualifyTests.test_score_below_threshold_rejected   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 17. Qualification: status must be new

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py qualify_status" --test-cmd "python3 -m unittest test_crm.QualifyTests.test_status_must_be_new" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-wg72k89x/crm.py
$ python3 mutate.py qualify_status
applied qualify_status
$ python3 -m unittest test_crm.QualifyTests.test_status_must_be_new   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_status_must_be_new (test_crm.QualifyTests.test_status_must_be_new)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 279, in test_status_must_be_new
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.QualifyTests.test_status_must_be_new   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 18. Qualification: unknown lead

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py qualify_exists" --test-cmd "python3 -m unittest test_crm.QualifyTests.test_unknown_lead" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-lhetdi65/crm.py
$ python3 mutate.py qualify_exists
applied qualify_exists
$ python3 -m unittest test_crm.QualifyTests.test_unknown_lead   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_unknown_lead (test_crm.QualifyTests.test_unknown_lead)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 285, in test_unknown_lead
    self.crm.qualify("L404", "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 167, in qualify
    if not self._can_act_on(actor, lead["owner"]):
                                   ~~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.QualifyTests.test_unknown_lead   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 19. Stage transition: order

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py stage_transition" --test-cmd "python3 -m unittest test_crm.AdvanceTests.test_illegal_transitions_rejected" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-cdldn_k5/crm.py
$ python3 mutate.py stage_transition
applied stage_transition
$ python3 -m unittest test_crm.AdvanceTests.test_illegal_transitions_rejected   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_illegal_transitions_rejected (test_crm.AdvanceTests.test_illegal_transitions_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 360, in test_illegal_transitions_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AdvanceTests.test_illegal_transitions_rejected   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 20. Stage transition: final stage immutable

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py final_stage" --test-cmd "python3 -m unittest test_crm.AdvanceTests.test_final_stage_immutable" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-rh2loo21/crm.py
$ python3 mutate.py final_stage
applied final_stage
$ python3 -m unittest test_crm.AdvanceTests.test_final_stage_immutable   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_final_stage_immutable (test_crm.AdvanceTests.test_final_stage_immutable)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 406, in test_final_stage_immutable
    with self.assertRaisesRegex(ValueError, "final"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AdvanceTests.test_final_stage_immutable   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 21. Stage transition: unknown opportunity

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py advance_exists" --test-cmd "python3 -m unittest test_crm.AdvanceTests.test_unknown_stage_and_opportunity" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-_h1vbtdw/crm.py
$ python3 mutate.py advance_exists
applied advance_exists
$ python3 -m unittest test_crm.AdvanceTests.test_unknown_stage_and_opportunity   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_unknown_stage_and_opportunity (test_crm.AdvanceTests.test_unknown_stage_and_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 415, in test_unknown_stage_and_opportunity
    self.crm.advance("O404", "proposal", "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 212, in advance
    if not self._can_act_on(actor, opp["owner"]):
                                   ~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AdvanceTests.test_unknown_stage_and_opportunity   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 22. Stage transition: lost frees the slot (F3)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py lost_refill" --test-cmd "python3 -m unittest test_crm.AdvanceTests.test_lost_frees_slot_and_refills_queue" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ici918vx/crm.py
$ python3 mutate.py lost_refill
applied lost_refill
$ python3 -m unittest test_crm.AdvanceTests.test_lost_frees_slot_and_refills_queue   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_lost_frees_slot_and_refills_queue (test_crm.AdvanceTests.test_lost_frees_slot_and_refills_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 396, in test_lost_frees_slot_and_refills_queue
    self.assertEqual(crm.leads[waiting]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AdvanceTests.test_lost_frees_slot_and_refills_queue   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 23. Big-deal approval: manager needed

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py big_deal_manager" --test-cmd "python3 -m unittest test_crm.AdvanceTests.test_big_deal_needs_manager" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8gbok44k/crm.py
$ python3 mutate.py big_deal_manager
applied big_deal_manager
$ python3 -m unittest test_crm.AdvanceTests.test_big_deal_needs_manager   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_big_deal_needs_manager (test_crm.AdvanceTests.test_big_deal_needs_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 421, in test_big_deal_needs_manager
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AdvanceTests.test_big_deal_needs_manager   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 24. Convert: amount positive int, not bool

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py amount_positive" --test-cmd "python3 -m unittest test_crm.ConvertTests.test_amount_validation" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-z9fbo6wo/crm.py
$ python3 mutate.py amount_positive
applied amount_positive
$ python3 -m unittest test_crm.ConvertTests.test_amount_validation   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_amount_validation (test_crm.ConvertTests.test_amount_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 297, in test_amount_validation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ConvertTests.test_amount_validation   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 25. Convert: requires qualified status

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py convert_status" --test-cmd "python3 -m unittest test_crm.ConvertTests.test_requires_qualified" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-wmqcmkw4/crm.py
$ python3 mutate.py convert_status
applied convert_status
$ python3 -m unittest test_crm.ConvertTests.test_requires_qualified   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_requires_qualified (test_crm.ConvertTests.test_requires_qualified)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 304, in test_requires_qualified
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ConvertTests.test_requires_qualified   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 26. Convert: requires an owner

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py convert_owner" --test-cmd "python3 -m unittest test_crm.ConvertTests.test_requires_owner" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-oehqojjd/crm.py
$ python3 mutate.py convert_owner
applied convert_owner
$ python3 -m unittest test_crm.ConvertTests.test_requires_owner   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_requires_owner (test_crm.ConvertTests.test_requires_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 312, in test_requires_owner
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ConvertTests.test_requires_owner   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 27. Convert: unknown lead (F4)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py convert_exists" --test-cmd "python3 -m unittest test_crm.ConvertTests.test_unknown_lead_with_valid_actor" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-98otuf5i/crm.py
$ python3 mutate.py convert_exists
applied convert_exists
$ python3 -m unittest test_crm.ConvertTests.test_unknown_lead_with_valid_actor   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_unknown_lead_with_valid_actor (test_crm.ConvertTests.test_unknown_lead_with_valid_actor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 320, in test_unknown_lead_with_valid_actor
    self.crm.convert("L404", 100, "m1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 184, in convert
    if not self._can_act_on(actor, lead["owner"]):
                                   ~~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ConvertTests.test_unknown_lead_with_valid_actor   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 28. Discount: non-manager limit

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py discount_manager_limit" --test-cmd "python3 -m unittest test_crm.DiscountTests.test_non_manager_limit" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-u33me7ad/crm.py
$ python3 mutate.py discount_manager_limit
applied discount_manager_limit
$ python3 -m unittest test_crm.DiscountTests.test_non_manager_limit   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_non_manager_limit (test_crm.DiscountTests.test_non_manager_limit)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 449, in test_non_manager_limit
    with self.assertRaisesRegex(PermissionError, "10"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.DiscountTests.test_non_manager_limit   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 29. Discount: cumulative floor

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py discount_cumulative_floor" --test-cmd "python3 -m unittest test_crm.DiscountTests.test_manager_max_and_cumulative_floor" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-h9lt9ohd/crm.py
$ python3 mutate.py discount_cumulative_floor
applied discount_cumulative_floor
$ python3 -m unittest test_crm.DiscountTests.test_manager_max_and_cumulative_floor   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_manager_max_and_cumulative_floor (test_crm.DiscountTests.test_manager_max_and_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 460, in test_manager_max_and_cumulative_floor
    with self.assertRaisesRegex(ValueError, "30"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.DiscountTests.test_manager_max_and_cumulative_floor   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 30. Discount: pct bounds, not bool

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py pct_bounds" --test-cmd "python3 -m unittest test_crm.DiscountTests.test_pct_bounds" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-h88pboy7/crm.py
$ python3 mutate.py pct_bounds
applied pct_bounds
$ python3 -m unittest test_crm.DiscountTests.test_pct_bounds   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_pct_bounds (test_crm.DiscountTests.test_pct_bounds)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 442, in test_pct_bounds
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.DiscountTests.test_pct_bounds   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 31. Discount: final stage rejected

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py discount_final" --test-cmd "python3 -m unittest test_crm.DiscountTests.test_final_stage_rejected" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7vb37bt4/crm.py
$ python3 mutate.py discount_final
applied discount_final
$ python3 -m unittest test_crm.DiscountTests.test_final_stage_rejected   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_final_stage_rejected (test_crm.DiscountTests.test_final_stage_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 475, in test_final_stage_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.DiscountTests.test_final_stage_rejected   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 32. Discount: unknown opportunity (F4)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py discount_exists" --test-cmd "python3 -m unittest test_crm.DiscountTests.test_unknown_opportunity_with_valid_actor" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jp800q2l/crm.py
$ python3 mutate.py discount_exists
applied discount_exists
$ python3 -m unittest test_crm.DiscountTests.test_unknown_opportunity_with_valid_actor   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_unknown_opportunity_with_valid_actor (test_crm.DiscountTests.test_unknown_opportunity_with_valid_actor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 468, in test_unknown_opportunity_with_valid_actor
    self.crm.discount("O404", 5, "m1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 236, in discount
    if not self._can_act_on(actor, opp["owner"]):
                                   ~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.DiscountTests.test_unknown_opportunity_with_valid_actor   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 33. Transfer: target must be a known rep

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py transfer_target" --test-cmd "python3 -m unittest test_crm.TransferTests.test_target_must_be_known_rep" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-sbec8ilj/crm.py
$ python3 mutate.py transfer_target
applied transfer_target
$ python3 -m unittest test_crm.TransferTests.test_target_must_be_known_rep   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_target_must_be_known_rep (test_crm.TransferTests.test_target_must_be_known_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 494, in test_target_must_be_known_rep
    self.crm.transfer(self.oid, "nope", "m1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 263, in transfer
    if self.load(new_owner) >= target["capacity"]:
                               ~~~~~~^^^^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.TransferTests.test_target_must_be_known_rep   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 34. Transfer: target must differ

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py transfer_differ" --test-cmd "python3 -m unittest test_crm.TransferTests.test_target_must_differ" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-32jihqp2/crm.py
$ python3 mutate.py transfer_differ
applied transfer_differ
$ python3 -m unittest test_crm.TransferTests.test_target_must_differ   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_target_must_differ (test_crm.TransferTests.test_target_must_differ)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 502, in test_target_must_differ
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.TransferTests.test_target_must_differ   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 35. Transfer: target capacity

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py transfer_capacity" --test-cmd "python3 -m unittest test_crm.TransferTests.test_target_at_capacity" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nnoxhr6f/crm.py
$ python3 mutate.py transfer_capacity
applied transfer_capacity
$ python3 -m unittest test_crm.TransferTests.test_target_at_capacity   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_target_at_capacity (test_crm.TransferTests.test_target_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 509, in test_target_at_capacity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.TransferTests.test_target_at_capacity   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 36. Transfer: final stage rejected

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py transfer_final" --test-cmd "python3 -m unittest test_crm.TransferTests.test_final_stage_cannot_transfer" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7v1zq3xi/crm.py
$ python3 mutate.py transfer_final
applied transfer_final
$ python3 -m unittest test_crm.TransferTests.test_final_stage_cannot_transfer   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_final_stage_cannot_transfer (test_crm.TransferTests.test_final_stage_cannot_transfer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 548, in test_final_stage_cannot_transfer
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.TransferTests.test_final_stage_cannot_transfer   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 37. Transfer: unknown opportunity (F4)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py transfer_exists" --test-cmd "python3 -m unittest test_crm.TransferTests.test_unknown_opportunity_with_valid_actor" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-wo5_1ue3/crm.py
$ python3 mutate.py transfer_exists
applied transfer_exists
$ python3 -m unittest test_crm.TransferTests.test_unknown_opportunity_with_valid_actor   # expect FAILURE matching /FAILED/
E
======================================================================
ERROR: test_unknown_opportunity_with_valid_actor (test_crm.TransferTests.test_unknown_opportunity_with_valid_actor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 516, in test_unknown_opportunity_with_valid_actor
    self.crm.transfer("O404", "r2", "m1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/crm.py", line 259, in transfer
    if opp["stage"] in FINAL_STAGES:
       ~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.TransferTests.test_unknown_opportunity_with_valid_actor   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 38. Transfer: frees previous owner's slot (F2/F6)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py transfer_refill" --test-cmd "python3 -m unittest test_crm.TransferTests.test_transfer_refills_previous_owner_and_log_order" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jo7l5mix/crm.py
$ python3 mutate.py transfer_refill
applied transfer_refill
$ python3 -m unittest test_crm.TransferTests.test_transfer_refills_previous_owner_and_log_order   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_transfer_refills_previous_owner_and_log_order (test_crm.TransferTests.test_transfer_refills_previous_owner_and_log_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 534, in test_transfer_refills_previous_owner_and_log_order
    self.assertEqual(crm.leads[waiting]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.TransferTests.test_transfer_refills_previous_owner_and_log_order   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 39. Forecast: stage weights

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py forecast_weights" --test-cmd "python3 -m unittest test_crm.ForecastTests.test_weights_by_stage" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ftovn8p4/crm.py
$ python3 mutate.py forecast_weights
applied forecast_weights
$ python3 -m unittest test_crm.ForecastTests.test_weights_by_stage   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_weights_by_stage (test_crm.ForecastTests.test_weights_by_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 562, in test_weights_by_stage
    self.assertEqual(crm.forecast()["weighted"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 900 != 1000

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ForecastTests.test_weights_by_stage   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 40. Forecast: open-count bookkeeping

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py forecast_open" --test-cmd "python3 -m unittest test_crm.ForecastTests.test_open_count_excludes_final" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-gjealt8p/crm.py
$ python3 mutate.py forecast_open
applied forecast_open
$ python3 -m unittest test_crm.ForecastTests.test_open_count_excludes_final   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_open_count_excludes_final (test_crm.ForecastTests.test_open_count_excludes_final)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 572, in test_open_count_excludes_final
    self.assertEqual(forecast["open"], 3)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 != 3

----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.ForecastTests.test_open_count_excludes_final   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 41. Atomicity: failed call changes nothing

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-neutral-1/crm.py --break-cmd "python3 mutate.py atomic_rollback" --test-cmd "python3 -m unittest test_crm.AtomicityTests.test_late_failure_rolls_back_everything" --expect "FAILED" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-neutral-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-m0c0emh6/crm.py
$ python3 mutate.py atomic_rollback
applied atomic_rollback
$ python3 -m unittest test_crm.AtomicityTests.test_late_failure_rolls_back_everything   # expect FAILURE matching /FAILED/
F
======================================================================
FAIL: test_late_failure_rolls_back_everything (test_crm.AtomicityTests.test_late_failure_rolls_back_everything)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/private/tmp/aep-lab/pilot2/AE-neutral-1/test_crm.py", line 646, in test_late_failure_rolls_back_everything
    self.assertEqual(crm.opps, opps_before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: {'O1'[49 chars]mount': 1000, 'original_amount': 1000, 'stage': 'won'}} != {'O1'[49 chars]mount': 1000, 'original_amount': 1000, 'stage': 'negotiation'}}
  {'O1': {'amount': 1000,
          'id': 'O1',
          'lead_id': 'L1',
          'original_amount': 1000,
          'owner': 'r1',
-         'stage': 'won'}}
?                   ^

+         'stage': 'negotiation'}}
?                   ^^^^^^^^^


----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-neutral-1/crm.py from backup (byte-identical)
$ python3 -m unittest test_crm.AtomicityTests.test_late_failure_rolls_back_everything   # expect SUCCESS
.
----------------------------------------------------------------------
Ran 1 test in 0.000s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0
