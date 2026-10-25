# Negative-control log — crm.py

Guard removal is performed by `_break.py <guard>`, which deletes the marked
`# >>> guard:<name>` block from crm.py (the atomicity controls instead move the
mutation ahead of a validation, which is the bug those tests exist to catch).
The `check order:` controls are permutations: `_break.py order-*` reorders two
checks that `crm.md` fixes in sequence, so the suite must notice when the first
failing check stops deciding the exception.

`aepkit negcontrol` backs the file up, applies the break, runs the suite — which
must fail with output matching the expected regex — and reruns the suite after
restoring the file, which must pass.

## Baseline suite

```console
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)
```

## Guard removals (24 controls)

## guard: email — email validation

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py email" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_email_validation" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-655pw3_i/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py email

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_email_validation/
....F...............................FFFFFFFFFF......................
======================================================================
FAIL: test_failed_add_changes_nothing (test_crm.TestAtomicity.test_failed_add_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 372, in test_failed_add_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed) (bad='plain')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 42, in test_email_validation_rejects_malformed
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed) (bad='a@@b.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 42, in test_email_validation_rejects_malformed
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed) (bad='@b.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 42, in test_email_validation_rejects_malformed
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed) (bad='a@.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 42, in test_email_validation_rejects_malformed
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed) (bad='a@com.')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 42, in test_email_validation_rejects_malformed
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed) (bad='a@bcom')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 42, in test_email_validation_rejects_malformed
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed) (bad='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 42, in test_email_validation_rejects_malformed
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed) (bad=123)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 42, in test_email_validation_rejects_malformed
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 42, in test_email_validation_rejects_malformed
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_malformed (test_crm.TestEmailNameSourceValidation.test_email_validation_rejects_malformed)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 44, in test_email_validation_rejects_malformed
    self.assertEqual(self.crm.leads, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: {'L1': {'id': 'L1', 'email': 'plain', 'nam[991 chars]ew'}} != {}
Diff is 1610 characters long. Set self.maxDiff to None to see it.

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (failures=11)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: name — name validation

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py name" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_name_validation" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bfsqhf8a/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py name

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_name_validation/
.....................................FEEEF.....................
======================================================================
ERROR: test_name_validation_rejects_blank (test_crm.TestEmailNameSourceValidation.test_name_validation_rejects_blank) (bad='   ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 60, in test_name_validation_rejects_blank
    self.crm.add_lead("a@b.com", bad, "web", "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 117, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_validation_rejects_blank (test_crm.TestEmailNameSourceValidation.test_name_validation_rejects_blank) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 60, in test_name_validation_rejects_blank
    self.crm.add_lead("a@b.com", bad, "web", "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 117, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_validation_rejects_blank (test_crm.TestEmailNameSourceValidation.test_name_validation_rejects_blank) (bad=7)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 60, in test_name_validation_rejects_blank
    self.crm.add_lead("a@b.com", bad, "web", "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 117, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
FAIL: test_name_validation_rejects_blank (test_crm.TestEmailNameSourceValidation.test_name_validation_rejects_blank) (bad='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 59, in test_name_validation_rejects_blank
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_name_validation_rejects_blank (test_crm.TestEmailNameSourceValidation.test_name_validation_rejects_blank)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 61, in test_name_validation_rejects_blank
    self.assertEqual(self.crm.leads, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: {'L1': {'id': 'L1', 'email': 'a@b.com', 'n[66 chars]ew'}} != {}
+ {}
- {'L1': {'email': 'a@b.com',
-         'id': 'L1',
-         'name': '',
-         'owner': 'A',
-         'score': 25,
-         'source': 'web',
-         'status': 'new'}}

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (failures=2, errors=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: source — source validation

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py source" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_source_validation" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8rf8phx4/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py source

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_source_validation/
...................E..................FEEEEF....................
======================================================================
ERROR: test_add_lead_source_checked_before_duplicate (test_crm.TestCheckOrder.test_add_lead_source_checked_before_duplicate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 534, in test_add_lead_source_checked_before_duplicate
    self.crm.add_lead("OWNER@corp.com", "Dup", "nope", "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 117, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_source_validation_rejects_unknown (test_crm.TestEmailNameSourceValidation.test_source_validation_rejects_unknown) (bad='Web')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 67, in test_source_validation_rejects_unknown
    self.crm.add_lead("a@b.com", "Name", bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 117, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_source_validation_rejects_unknown (test_crm.TestEmailNameSourceValidation.test_source_validation_rejects_unknown) (bad='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 67, in test_source_validation_rejects_unknown
    self.crm.add_lead("a@b.com", "Name", bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 117, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_source_validation_rejects_unknown (test_crm.TestEmailNameSourceValidation.test_source_validation_rejects_unknown) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 67, in test_source_validation_rejects_unknown
    self.crm.add_lead("a@b.com", "Name", bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 117, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_source_validation_rejects_unknown (test_crm.TestEmailNameSourceValidation.test_source_validation_rejects_unknown) (bad=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 67, in test_source_validation_rejects_unknown
    self.crm.add_lead("a@b.com", "Name", bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 117, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
FAIL: test_source_validation_rejects_unknown (test_crm.TestEmailNameSourceValidation.test_source_validation_rejects_unknown) (bad='email')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 66, in test_source_validation_rejects_unknown
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_source_validation_rejects_unknown (test_crm.TestEmailNameSourceValidation.test_source_validation_rejects_unknown)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 68, in test_source_validation_rejects_unknown
    self.assertEqual(self.crm.leads, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: {'L1': {'id': 'L1', 'email': 'a@b.com', 'n[72 chars]ew'}} != {}
+ {}
- {'L1': {'email': 'a@b.com',
-         'id': 'L1',
-         'name': 'Name',
-         'owner': 'A',
-         'score': 15,
-         'source': 'email',
-         'status': 'new'}}

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (failures=2, errors=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: duplicate — duplicate detection

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py duplicate" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_duplicate_detection" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ncyzvnvh/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py duplicate

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_duplicate_detection/
...F..............................F........................
======================================================================
FAIL: test_duplicate_failure_changes_nothing (test_crm.TestAtomicity.test_duplicate_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 382, in test_duplicate_failure_changes_nothing
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_detection_after_normalization (test_crm.TestEmailNameSourceValidation.test_duplicate_detection_after_normalization)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 72, in test_duplicate_detection_after_normalization
    with self.assertRaises(DuplicateLeadError) as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: capacity — rep assignment and capacity

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py capacity" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_capacity_exhaustion" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-la53kcap/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py capacity

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_capacity_exhaustion/
F.F...........F...........................................F
======================================================================
FAIL: test_capacity_exhaustion_queues_and_managers_never_own (test_crm.TestAssignmentCapacityAndQueue.test_capacity_exhaustion_queues_and_managers_never_own)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 96, in test_capacity_exhaustion_queues_and_managers_never_own
    self.assertIsNone(crm.leads[second]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'A' is not None

======================================================================
FAIL: test_waiting_queue_fifo_drained_when_opportunity_won (test_crm.TestAssignmentCapacityAndQueue.test_waiting_queue_fifo_drained_when_opportunity_won)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 106, in test_waiting_queue_fifo_drained_when_opportunity_won
    self.assertEqual(crm.waiting, [queued_first, queued_second])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L3', 'L4']

Second list contains 2 additional elements.
First extra element 0:
'L3'

- []
+ ['L3', 'L4']

======================================================================
FAIL: test_lost_frees_slot_and_drains_waiting_queue (test_crm.TestBehaviourEdges.test_lost_frees_slot_and_drains_waiting_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 552, in test_lost_frees_slot_and_drains_waiting_queue
    self.assertEqual(crm.waiting, [queued])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_transfer_moves_owner_and_drains_previous_owner_queue (test_crm.TestTransferRules.test_transfer_moves_owner_and_drains_previous_owner_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 359, in test_transfer_moves_owner_and_drains_previous_owner_queue
    self.assertEqual(crm.waiting, [queued])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L4']

Second list contains 1 additional elements.
First extra element 0:
'L4'

- []
+ ['L4']

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: queue — waiting-queue membership

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py queue" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_capacity_exhaustion" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-iylgsgu5/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py queue

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_capacity_exhaustion/
F.F...........F...........................................F
======================================================================
FAIL: test_capacity_exhaustion_queues_and_managers_never_own (test_crm.TestAssignmentCapacityAndQueue.test_capacity_exhaustion_queues_and_managers_never_own)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 97, in test_capacity_exhaustion_queues_and_managers_never_own
    self.assertEqual(crm.waiting, [second])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_waiting_queue_fifo_drained_when_opportunity_won (test_crm.TestAssignmentCapacityAndQueue.test_waiting_queue_fifo_drained_when_opportunity_won)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 106, in test_waiting_queue_fifo_drained_when_opportunity_won
    self.assertEqual(crm.waiting, [queued_first, queued_second])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L3', 'L4']

Second list contains 2 additional elements.
First extra element 0:
'L3'

- []
+ ['L3', 'L4']

======================================================================
FAIL: test_lost_frees_slot_and_drains_waiting_queue (test_crm.TestBehaviourEdges.test_lost_frees_slot_and_drains_waiting_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 552, in test_lost_frees_slot_and_drains_waiting_queue
    self.assertEqual(crm.waiting, [queued])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_transfer_moves_owner_and_drains_previous_owner_queue (test_crm.TestTransferRules.test_transfer_moves_owner_and_drains_previous_owner_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 359, in test_transfer_moves_owner_and_drains_previous_owner_queue
    self.assertEqual(crm.waiting, [queued])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L4']

Second list contains 1 additional elements.
First extra element 0:
'L4'

- []
+ ['L4']

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: drain — waiting-queue drain (FIFO)

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py drain" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_waiting_queue_fifo" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-os7ulw5w/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py drain

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_waiting_queue_fifo/
..F...........F...........................................F
======================================================================
FAIL: test_waiting_queue_fifo_drained_when_opportunity_won (test_crm.TestAssignmentCapacityAndQueue.test_waiting_queue_fifo_drained_when_opportunity_won)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 112, in test_waiting_queue_fifo_drained_when_opportunity_won
    self.assertEqual(crm.leads[queued_first]["owner"], "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'A'

======================================================================
FAIL: test_lost_frees_slot_and_drains_waiting_queue (test_crm.TestBehaviourEdges.test_lost_frees_slot_and_drains_waiting_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 557, in test_lost_frees_slot_and_drains_waiting_queue
    self.assertEqual(crm.leads[queued]["owner"], "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'A'

======================================================================
FAIL: test_transfer_moves_owner_and_drains_previous_owner_queue (test_crm.TestTransferRules.test_transfer_moves_owner_and_drains_previous_owner_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 365, in test_transfer_moves_owner_and_drains_previous_owner_queue
    self.assertEqual(crm.leads[queued]["owner"], "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'A'

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: actor — unknown actor checked first

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py actor" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_unknown_actor" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jg5qh96i/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py actor

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_unknown_actor/
...........................................F...............
======================================================================
FAIL: test_unknown_actor_rejected_first_by_every_method (test_crm.TestPermissions.test_unknown_actor_rejected_first_by_every_method)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 128, in test_unknown_actor_rejected_first_by_every_method
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: permission — permission checks

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py permission" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_non_owner_rep_cannot_mutate" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-g8nefb9e/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py permission

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_non_owner_rep_cannot_mutate/
....................EE....E................E................
======================================================================
ERROR: test_advance_permission_checked_before_final_stage (test_crm.TestCheckOrder.test_advance_permission_checked_before_final_stage) (stage='proposal')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 480, in test_advance_permission_checked_before_final_stage
    self.crm.advance(self.opp, stage, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 193, in advance
    raise ValueError("opportunity is already in a final stage")
ValueError: opportunity is already in a final stage

======================================================================
ERROR: test_advance_permission_checked_before_final_stage (test_crm.TestCheckOrder.test_advance_permission_checked_before_final_stage) (stage='lost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 480, in test_advance_permission_checked_before_final_stage
    self.crm.advance(self.opp, stage, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 193, in advance
    raise ValueError("opportunity is already in a final stage")
ValueError: opportunity is already in a final stage

======================================================================
ERROR: test_discount_permission_checked_before_final_stage (test_crm.TestCheckOrder.test_discount_permission_checked_before_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 506, in test_discount_permission_checked_before_final_stage
    self.crm.discount(self.opp, 5, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 216, in discount
    raise ValueError("opportunity is already in a final stage")
ValueError: opportunity is already in a final stage

======================================================================
ERROR: test_non_owner_rep_cannot_mutate (test_crm.TestPermissions.test_non_owner_rep_cannot_mutate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 149, in test_non_owner_rep_cannot_mutate
    self.crm.qualify(self.lead, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 148, in qualify
    raise ValueError("lead is not new")
ValueError: lead is not new

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: score — qualification score threshold

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py score" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_web_and_event" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ht9j9yth/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py score

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_web_and_event/
........F......................................F...........
======================================================================
FAIL: test_failed_qualify_logs_nothing (test_crm.TestAtomicity.test_failed_qualify_logs_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 390, in test_failed_qualify_logs_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_web_and_event_on_free_mail_fail_threshold (test_crm.TestQualificationThreshold.test_web_and_event_on_free_mail_fail_threshold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 175, in test_web_and_event_on_free_mail_fail_threshold
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: transition — stage-transition rules

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transition" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_skipping_stages" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-irm12ukx/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transition

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_skipping_stages/
................................................FF.FFF.......
======================================================================
FAIL: test_backwards_rejected (test_crm.TestStageTransitions.test_backwards_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 222, in test_backwards_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_full_path_and_lost (test_crm.TestStageTransitions.test_full_path_and_lost)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 232, in test_full_path_and_lost
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_skipping_stages_rejected (test_crm.TestStageTransitions.test_skipping_stages_rejected) (bad='negotiation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 216, in test_skipping_stages_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_skipping_stages_rejected (test_crm.TestStageTransitions.test_skipping_stages_rejected) (bad='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 216, in test_skipping_stages_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_skipping_stages_rejected (test_crm.TestStageTransitions.test_skipping_stages_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 218, in test_skipping_stages_rejected
    self.assertEqual(self.crm.opps[self.opp]["stage"], "prospect")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'won' != 'prospect'
- won
+ prospect


----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: bigdeal — big-deal approval

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py bigdeal" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_rep_needs_manager" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-mrzded5s/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py bigdeal

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_rep_needs_manager/
.....F............F........................................
======================================================================
FAIL: test_failed_advance_leaves_stage_and_log (test_crm.TestAtomicity.test_failed_advance_leaves_stage_and_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 410, in test_failed_advance_leaves_stage_and_log
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_rep_needs_manager_for_negotiation_above_50000 (test_crm.TestBigDealApproval.test_rep_needs_manager_for_negotiation_above_50000)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 254, in test_rep_needs_manager_for_negotiation_above_50000
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: pct-range — discount pct range/type

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py pct-range" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_pct_range_and_type" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-gekrw0wr/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py pct-range

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_pct_range_and_type/
........................EEEEEEE.......FFFEFEF..........................
======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=31)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=-5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_pct_range_and_type (test_crm.TestDiscountLimits.test_pct_range_and_type) (bad='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 280, in test_pct_range_and_type
    self.crm.discount(self.opp, bad, "M")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 220, in discount
    new_amount = opp["amount"] * (100 - pct) // 100
                                  ~~~~^~~~~
TypeError: unsupported operand type(s) for -: 'int' and 'str'

======================================================================
ERROR: test_pct_range_and_type (test_crm.TestDiscountLimits.test_pct_range_and_type) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 280, in test_pct_range_and_type
    self.crm.discount(self.opp, bad, "M")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 220, in discount
    new_amount = opp["amount"] * (100 - pct) // 100
                                  ~~~~^~~~~
TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'

======================================================================
FAIL: test_pct_range_and_type (test_crm.TestDiscountLimits.test_pct_range_and_type) (bad=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 279, in test_pct_range_and_type
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_range_and_type (test_crm.TestDiscountLimits.test_pct_range_and_type) (bad=-5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 279, in test_pct_range_and_type
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_range_and_type (test_crm.TestDiscountLimits.test_pct_range_and_type) (bad=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 279, in test_pct_range_and_type
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_range_and_type (test_crm.TestDiscountLimits.test_pct_range_and_type) (bad=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 279, in test_pct_range_and_type
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_range_and_type (test_crm.TestDiscountLimits.test_pct_range_and_type)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 281, in test_pct_range_and_type
    self.assertEqual(self.crm.opps[self.opp]["amount"], 10000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 10239.0 != 10000

----------------------------------------------------------------------
Ran 59 tests in 0.004s

FAILED (failures=5, errors=9)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: rep-cap — per-rep discount cap

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py rep-cap" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_rep_discount_cap_is_10" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-f3ra0ceb/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py rep-cap

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_rep_discount_cap_is_10/
..........................F......F.........................
======================================================================
FAIL: test_discount_rep_cap_still_applies_to_owner (test_crm.TestCheckOrder.test_discount_rep_cap_still_applies_to_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 520, in test_discount_rep_cap_still_applies_to_owner
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_rep_discount_cap_is_10 (test_crm.TestDiscountLimits.test_rep_discount_cap_is_10)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 284, in test_rep_discount_cap_is_10
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: floor — cumulative discount floor

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py floor" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_cumulative_floor" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bb0ggt5q/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py floor

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_cumulative_floor/
.......F....................F..............................
======================================================================
FAIL: test_failed_discount_leaves_amount_and_log (test_crm.TestAtomicity.test_failed_discount_leaves_amount_and_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 420, in test_failed_discount_leaves_amount_and_log
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cumulative_floor_blocks_further_discount (test_crm.TestDiscountLimits.test_cumulative_floor_blocks_further_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 298, in test_cumulative_floor_blocks_further_discount
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: transfer-manager — transfer: manager-only

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transfer-manager" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_only_manager_may_transfer" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1ikq8n5j/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transfer-manager

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_only_manager_may_transfer/
.........F.................EEEE..........................F....
======================================================================
ERROR: test_transfer_manager_checked_before_target (test_crm.TestCheckOrder.test_transfer_manager_checked_before_target) (bad='ghost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 528, in test_transfer_manager_checked_before_target
    self.crm.transfer(self.opp, bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 238, in transfer
    raise ValueError("new owner must be a rep")
ValueError: new owner must be a rep

======================================================================
ERROR: test_transfer_manager_checked_before_target (test_crm.TestCheckOrder.test_transfer_manager_checked_before_target) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 528, in test_transfer_manager_checked_before_target
    self.crm.transfer(self.opp, bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 238, in transfer
    raise ValueError("new owner must be a rep")
ValueError: new owner must be a rep

======================================================================
ERROR: test_transfer_manager_checked_before_target (test_crm.TestCheckOrder.test_transfer_manager_checked_before_target) (bad=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 528, in test_transfer_manager_checked_before_target
    self.crm.transfer(self.opp, bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 238, in transfer
    raise ValueError("new owner must be a rep")
ValueError: new owner must be a rep

======================================================================
ERROR: test_transfer_manager_checked_before_target (test_crm.TestCheckOrder.test_transfer_manager_checked_before_target) (bad='M')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 528, in test_transfer_manager_checked_before_target
    self.crm.transfer(self.opp, bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 238, in transfer
    raise ValueError("new owner must be a rep")
ValueError: new owner must be a rep

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_crm.TestAtomicity.test_failed_transfer_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 429, in test_failed_transfer_changes_nothing
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_only_manager_may_transfer (test_crm.TestTransferRules.test_only_manager_may_transfer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 322, in test_only_manager_may_transfer
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (failures=2, errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: transfer-target — transfer: target must be a known rep

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transfer-target" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_target_must_be_known_rep" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-sm1cke53/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transfer-target

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_target_must_be_known_rep/
.........................................................FEEEF.
======================================================================
ERROR: test_target_must_be_known_rep (test_crm.TestTransferRules.test_target_must_be_known_rep) (bad='ghost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 330, in test_target_must_be_known_rep
    self.crm.transfer(self.opp, bad, "M")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 246, in transfer
    if self._load(new_owner) >= self.users[new_owner]["capacity"]:
                                ~~~~~~~~~~^^^^^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_target_must_be_known_rep (test_crm.TestTransferRules.test_target_must_be_known_rep) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 330, in test_target_must_be_known_rep
    self.crm.transfer(self.opp, bad, "M")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 246, in transfer
    if self._load(new_owner) >= self.users[new_owner]["capacity"]:
                                ~~~~~~~~~~^^^^^^^^^^^
KeyError: None

======================================================================
ERROR: test_target_must_be_known_rep (test_crm.TestTransferRules.test_target_must_be_known_rep) (bad=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 330, in test_target_must_be_known_rep
    self.crm.transfer(self.opp, bad, "M")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 246, in transfer
    if self._load(new_owner) >= self.users[new_owner]["capacity"]:
                                ~~~~~~~~~~^^^^^^^^^^^
KeyError: 5

======================================================================
FAIL: test_target_must_be_known_rep (test_crm.TestTransferRules.test_target_must_be_known_rep) (bad='M')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 329, in test_target_must_be_known_rep
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_target_must_be_known_rep (test_crm.TestTransferRules.test_target_must_be_known_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 331, in test_target_must_be_known_rep
    self.assertEqual(self.crm.opps[self.opp]["owner"], "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'M' != 'A'
- M
+ A


----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (failures=2, errors=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: transfer-same — transfer: same-owner rejected

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transfer-same" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_same_owner_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8bi1fmi3/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transfer-same

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_same_owner_rejected/
.......................................................F...
======================================================================
FAIL: test_same_owner_rejected (test_crm.TestTransferRules.test_same_owner_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 334, in test_same_owner_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: transfer-capacity — transfer: target capacity

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transfer-capacity" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_target_at_capacity_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ry4pfg0d/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py transfer-capacity

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_target_at_capacity_rejected/
........................................................F..
======================================================================
FAIL: test_target_at_capacity_rejected (test_crm.TestTransferRules.test_target_at_capacity_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 342, in test_target_at_capacity_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: atomicity — atomicity: advance

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py atomicity" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_failed_advance" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-vfgf0yth/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py atomicity

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_failed_advance/
.....F............F........................................
======================================================================
FAIL: test_failed_advance_leaves_stage_and_log (test_crm.TestAtomicity.test_failed_advance_leaves_stage_and_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 412, in test_failed_advance_leaves_stage_and_log
    self.assertEqual(crm.opps[opp]["stage"], "proposal")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'negotiation' != 'proposal'
- negotiation
+ proposal


======================================================================
FAIL: test_rep_needs_manager_for_negotiation_above_50000 (test_crm.TestBigDealApproval.test_rep_needs_manager_for_negotiation_above_50000)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 256, in test_rep_needs_manager_for_negotiation_above_50000
    self.assertEqual(self.crm.opps[self.big]["stage"], "proposal")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'negotiation' != 'proposal'
- negotiation
+ proposal


----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: atomicity-add — atomicity: add_lead

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py atomicity-add" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_failed_add_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xu8az56r/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py atomicity-add

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_failed_add_changes_nothing/
.F..F......................................................
======================================================================
FAIL: test_lowest_load_then_smallest_id (test_crm.TestAssignmentCapacityAndQueue.test_lowest_load_then_smallest_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 82, in test_lowest_load_then_smallest_id
    self.assertEqual(add(crm, email="1@corp.com"), "L1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'L2' != 'L1'
- L2
+ L1


======================================================================
FAIL: test_failed_add_changes_nothing (test_crm.TestAtomicity.test_failed_add_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 376, in test_failed_add_changes_nothing
    self.assertEqual(add(crm, email="ok@corp.com"), "L1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'L3' != 'L1'
- L3
+ L1


----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: status-new — qualify: status must be new

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py status-new" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_cannot_qualify_twice" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-q3024did/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py status-new

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_cannot_qualify_twice/
............................................F..............
======================================================================
FAIL: test_cannot_qualify_twice (test_crm.TestQualificationThreshold.test_cannot_qualify_twice)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 197, in test_cannot_qualify_twice
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: amount — convert: amount validation

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py amount" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_failed_convert_creates_no_opportunity" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ffn0y7f7/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py amount

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_failed_convert_creates_no_opportunity/
......F...FF...........EEEEE....................................
======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

======================================================================
FAIL: test_failed_convert_creates_no_opportunity (test_crm.TestAtomicity.test_failed_convert_creates_no_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 399, in test_failed_convert_creates_no_opportunity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_convert_rejects_non_int_amounts (test_crm.TestBehaviourEdges.test_convert_rejects_non_int_amounts) (bad=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 574, in test_convert_rejects_non_int_amounts
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_convert_rejects_non_int_amounts (test_crm.TestBehaviourEdges.test_convert_rejects_non_int_amounts)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 576, in test_convert_rejects_non_int_amounts
    self.assertEqual(crm.opps, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
AssertionError: {'O1': {'id': 'O1', 'lead_id': 'L1', 'owne[66 chars]ct'}} != {}
+ {}
- {'O1': {'amount': True,
-         'id': 'O1',
-         'lead_id': 'L1',
-         'original_amount': True,
-         'owner': 'A',
-         'stage': 'prospect'}}

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (failures=3, errors=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## guard: stage-name — advance: stage-name validation

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py stage-name" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_advance_stage_name_checked_before_permission" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-37ax8rx6/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py stage-name

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_advance_stage_name_checked_before_permission/
.....................EEEEE.....................................
======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad='closed')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad='PROSPECT')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (errors=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## Check-order permutations (8 controls)

## check order: order-advance-stage — advance: stage name before permission

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-advance-stage" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_advance_stage_name_checked_before_permission" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-6lk55zeh/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-advance-stage

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_advance_stage_name_checked_before_permission/
.....................EEEEE.....................................
======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad='closed')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad='PROSPECT')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_advance_stage_name_checked_before_permission (test_crm.TestCheckOrder.test_advance_stage_name_checked_before_permission) (bad=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 472, in test_advance_stage_name_checked_before_permission
    self.crm.advance(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 189, in advance
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (errors=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## check order: order-advance-final — advance: permission before final-stage

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-advance-final" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_advance_permission_checked_before_final_stage" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nvt7swk3/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-advance-final

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_advance_permission_checked_before_final_stage/
....................EE......................................
======================================================================
ERROR: test_advance_permission_checked_before_final_stage (test_crm.TestCheckOrder.test_advance_permission_checked_before_final_stage) (stage='proposal')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 480, in test_advance_permission_checked_before_final_stage
    self.crm.advance(self.opp, stage, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 195, in advance
    raise ValueError("opportunity is already in a final stage")
ValueError: opportunity is already in a final stage

======================================================================
ERROR: test_advance_permission_checked_before_final_stage (test_crm.TestCheckOrder.test_advance_permission_checked_before_final_stage) (stage='lost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 480, in test_advance_permission_checked_before_final_stage
    self.crm.advance(self.opp, stage, "B")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 195, in advance
    raise ValueError("opportunity is already in a final stage")
ValueError: opportunity is already in a final stage

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## check order: order-convert-amount — convert: amount before permission

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-convert-amount" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_convert_amount_checked_before_permission" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-eld3o0zr/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-convert-amount

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_convert_amount_checked_before_permission/
......................EEEEE....................................
======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

======================================================================
ERROR: test_convert_amount_checked_before_permission (test_crm.TestCheckOrder.test_convert_amount_checked_before_permission) (bad='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 490, in test_convert_amount_checked_before_permission
    self.crm.convert(lead, bad, "A")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 163, in convert
    self._allowed(lead["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: A may not act on this record

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (errors=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## check order: order-discount-pct — discount: pct before permission

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-discount-pct" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_discount_pct_checked_before_permission" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bxvj_6t4/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-discount-pct

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_discount_pct_checked_before_permission/
........................EEEEEEE..................................
======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=31)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=-5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

======================================================================
ERROR: test_discount_pct_checked_before_permission (test_crm.TestCheckOrder.test_discount_pct_checked_before_permission) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 498, in test_discount_pct_checked_before_permission
    self.crm.discount(self.opp, bad, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 213, in discount
    self._allowed(opp["owner"], actor)
    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 47, in _allowed
    raise PermissionError("%s may not act on this record" % (actor,))
PermissionError: B may not act on this record

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (errors=7)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## check order: order-discount-permission — discount: permission before final-stage and rep-cap

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-discount-permission" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_discount_permission_checked_before_final_stage" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-gzcn4ur8/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-discount-permission

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_discount_permission_checked_before_final_stage/
.........................E.................................
======================================================================
ERROR: test_discount_permission_checked_before_final_stage (test_crm.TestCheckOrder.test_discount_permission_checked_before_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 506, in test_discount_permission_checked_before_final_stage
    self.crm.discount(self.opp, 5, "B")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 218, in discount
    raise ValueError("opportunity is already in a final stage")
ValueError: opportunity is already in a final stage

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## check order: order-discount-final — discount: final-stage before rep-cap

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-discount-final" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_discount_final_stage_checked_before_rep_cap" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-h2g0buc8/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-discount-final

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_discount_final_stage_checked_before_rep_cap/
.......................E...................................
======================================================================
ERROR: test_discount_final_stage_checked_before_rep_cap (test_crm.TestCheckOrder.test_discount_final_stage_checked_before_rep_cap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 516, in test_discount_final_stage_checked_before_rep_cap
    self.crm.discount(self.opp, 11, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 220, in discount
    raise PermissionError("reps may discount at most 10 percent")
PermissionError: reps may discount at most 10 percent

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## check order: order-transfer-target — transfer: manager before target

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-transfer-target" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_transfer_manager_checked_before_target" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ko_ik4ym/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-transfer-target

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_transfer_manager_checked_before_target/
...........................EEEE...............................
======================================================================
ERROR: test_transfer_manager_checked_before_target (test_crm.TestCheckOrder.test_transfer_manager_checked_before_target) (bad='ghost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 528, in test_transfer_manager_checked_before_target
    self.crm.transfer(self.opp, bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 238, in transfer
    raise ValueError("new owner must be a rep")
ValueError: new owner must be a rep

======================================================================
ERROR: test_transfer_manager_checked_before_target (test_crm.TestCheckOrder.test_transfer_manager_checked_before_target) (bad=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 528, in test_transfer_manager_checked_before_target
    self.crm.transfer(self.opp, bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 238, in transfer
    raise ValueError("new owner must be a rep")
ValueError: new owner must be a rep

======================================================================
ERROR: test_transfer_manager_checked_before_target (test_crm.TestCheckOrder.test_transfer_manager_checked_before_target) (bad=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 528, in test_transfer_manager_checked_before_target
    self.crm.transfer(self.opp, bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 238, in transfer
    raise ValueError("new owner must be a rep")
ValueError: new owner must be a rep

======================================================================
ERROR: test_transfer_manager_checked_before_target (test_crm.TestCheckOrder.test_transfer_manager_checked_before_target) (bad='M')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 528, in test_transfer_manager_checked_before_target
    self.crm.transfer(self.opp, bad, "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 238, in transfer
    raise ValueError("new owner must be a rep")
ValueError: new owner must be a rep

----------------------------------------------------------------------
Ran 59 tests in 0.003s

FAILED (errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## check order: order-add-source — add_lead: source before duplicate

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-add-source" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"' --expect "test_add_lead_source_checked_before_duplicate" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5w3jgb49/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-3/_break.py order-add-source

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect FAILURE matching /test_add_lead_source_checked_before_duplicate/
...................E.......................................
======================================================================
ERROR: test_add_lead_source_checked_before_duplicate (test_crm.TestCheckOrder.test_add_lead_source_checked_before_duplicate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-3/test_crm.py", line 534, in test_add_lead_source_checked_before_duplicate
    self.crm.add_lead("OWNER@corp.com", "Dup", "nope", "A")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-3/crm.py", line 117, in add_lead
    raise DuplicateLeadError(existing["id"])
crm.DuplicateLeadError: duplicate lead: L1

----------------------------------------------------------------------
Ran 59 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-3 -p "test*.py"   # expect SUCCESS
...........................................................
----------------------------------------------------------------------
Ran 59 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

## Shipped-file inventory

```console
$ shasum -a 256 crm.py test_crm.py _break.py
f9d1beb20e29d967c194c0e4bfd96321e8f348f7ec1960b465afe2d642a3066f  crm.py
21d162117844ebe16837005ce8127822a1a885699ca5c73342599158843ac765  test_crm.py
4c248f594f7d9da828bd03c7fb7a185645539e845720ce0cc64c8bc3e3626ec4  _break.py
```
