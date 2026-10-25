# Negative-control log

Every entry below removes exactly one guard from `crm.py` with `_break.py`
(which asserts that the guard line it patches exists exactly once), runs the
full unit suite with `aepkit negcontrol`, and requires three things: the suite
fails under the break, the failure output matches `/FAILED/`, and the suite
passes again after the byte-identical restore. Exit code 0 means the control
held.

Test command used throughout:

```sh
python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"
```

Baseline before any control: `Ran 86 tests ... OK`.


```
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
```


## 1. Email validation: malformed email must be rejected

Guard removed: `email-type` (mode `email-type`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py email-type" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fwnvzb3b/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py email-type
guard removed: email-type
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
...........................E..........................................................
======================================================================
ERROR: test_non_string_email (test_leads.TestEmailValidation.test_non_string_email)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 62, in test_non_string_email
    self.assert_rejected(bad)
    ~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 56, in assert_rejected
    self.crm.add_lead(email, "Name", "web", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 74, in add_lead
    normalized = email.strip().lower()
                 ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 2. Email validation: exactly one @ and a non-empty local part

Guard removed: `email-local` (mode `email-local`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py email-local" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-_0fwndfw/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py email-local
guard removed: email-local
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.........................FF...........................................................
======================================================================
FAIL: test_missing_local_part (test_leads.TestEmailValidation.test_missing_local_part)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 70, in test_missing_local_part
    self.assert_rejected(bad)
    ~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 55, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_missing_or_multiple_at_signs (test_leads.TestEmailValidation.test_missing_or_multiple_at_signs)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 66, in test_missing_or_multiple_at_signs
    self.assert_rejected(bad)
    ~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 55, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 3. Email validation: domain must contain an inner dot

Guard removed: `email-domain` (mode `email-domain`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py email-domain" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-skuvibnp/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py email-domain
guard removed: email-domain
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.......................FF.............................................................
======================================================================
FAIL: test_dot_that_is_first_or_last_character_of_domain (test_leads.TestEmailValidation.test_dot_that_is_first_or_last_character_of_domain)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 78, in test_dot_that_is_first_or_last_character_of_domain
    self.assert_rejected(bad)
    ~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 55, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_missing_dot_in_domain (test_leads.TestEmailValidation.test_missing_dot_in_domain)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 74, in test_missing_dot_in_domain
    self.assert_rejected(bad)
    ~~~~~~~~~~~~~~~~~~~~^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 55, in assert_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 4. Name validation: non-empty string after strip()

Guard removed: `name` (mode `name`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py name" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bu5j7b6y/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py name
guard removed: name
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.F............................F.......................................................
======================================================================
FAIL: test_failed_add_lead_does_not_burn_an_id (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_add_lead_does_not_burn_an_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 19, in test_failed_add_lead_does_not_burn_an_id
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_names (test_leads.TestNameAndSourceValidation.test_invalid_names)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 93, in test_invalid_names
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 5. Source validation: web/referral/event only

Guard removed: `source` (mode `source`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py source" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-qye9vvwh/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py source
guard removed: source
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
...............................E......................................................
======================================================================
ERROR: test_invalid_sources (test_leads.TestNameAndSourceValidation.test_invalid_sources)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 101, in test_invalid_sources
    self.crm.add_lead("buyer@acme.com", "Ada", bad, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 83, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'ads'

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 6. Duplicate detection on the normalized email

Guard removed: `duplicate` (mode `duplicate`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py duplicate" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-mqeue3cy/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py duplicate
guard removed: duplicate
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
F....................FF...............................................................
======================================================================
FAIL: test_duplicate_does_not_burn_an_id_or_log (test_atomicity.TestFailedCallsLeaveNoTrace.test_duplicate_does_not_burn_an_id_or_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 29, in test_duplicate_does_not_burn_an_id_or_log
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_check_happens_before_id_allocation (test_leads.TestDuplicates.test_duplicate_check_happens_before_id_allocation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 127, in test_duplicate_check_happens_before_id_allocation
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_normalized_email_is_rejected (test_leads.TestDuplicates.test_duplicate_normalized_email_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 118, in test_duplicate_normalized_email_is_rejected
    with self.assertRaises(DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 7. Rep assignment: capacity filter decides who may receive work

Guard removed: `assign-capacity` (mode `assign-capacity`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py assign-capacity" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-huygpju3/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py assign-capacity
guard removed: assign-capacity
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
..........F....F....F..................F....................F....................FF...
======================================================================
FAIL: test_winning_assigns_exactly_one_waiting_lead_per_freed_slot (test_atomicity.TestFailedCallsLeaveNoTrace.test_winning_assigns_exactly_one_waiting_lead_per_freed_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 156, in test_winning_assigns_exactly_one_waiting_lead_per_freed_slot
    self.assertEqual(crm.waiting, [waiting])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_leads_queue_when_every_rep_is_at_capacity (test_leads.TestAssignment.test_leads_queue_when_every_rep_is_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 197, in test_leads_queue_when_every_rep_is_at_capacity
    self.assertIsNone(crm.leads[third]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_waiting_queue_is_fifo_and_respects_capacity (test_leads.TestAssignment.test_waiting_queue_is_fifo_and_respects_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 213, in test_waiting_queue_is_fifo_and_respects_capacity
    self.assertEqual(crm.waiting, [second, third])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2', 'L3']

Second list contains 2 additional elements.
First extra element 0:
'L2'

- []
+ ['L2', 'L3']

======================================================================
FAIL: test_unowned_lead_needs_a_manager (test_leads.TestQualify.test_unowned_lead_needs_a_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 301, in test_unowned_lead_needs_a_manager
    self.assertIsNone(crm.leads[lead]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_unowned_qualified_lead_cannot_be_converted (test_opps.TestConvert.test_unowned_qualified_lead_cannot_be_converted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 86, in test_unowned_qualified_lead_cannot_be_converted
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_transfer_is_impossible_while_leads_are_waiting (test_transfers.TestTransfer.test_transfer_is_impossible_while_leads_are_waiting)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 118, in test_transfer_is_impossible_while_leads_are_waiting
    self.assertEqual(crm.waiting, [waiting])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L3']

Second list contains 1 additional elements.
First extra element 0:
'L3'

- []
+ ['L3']

======================================================================
FAIL: test_transfer_releases_the_previous_owner_without_extra_log_entries (test_transfers.TestTransfer.test_transfer_releases_the_previous_owner_without_extra_log_entries)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 103, in test_transfer_releases_the_previous_owner_without_extra_log_entries
    self.assertEqual(crm.load("r1"), 0)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
AssertionError: 1 != 0

----------------------------------------------------------------------
Ran 86 tests in 0.004s

FAILED (failures=7)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 8. Rep assignment: load tie broken by smallest id

Guard removed: `assign-tie` (mode `assign-tie`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py assign-tie" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5f44nc_x/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py assign-tie
guard removed: assign-tie
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
...................F..................................................................
======================================================================
FAIL: test_smallest_id_wins_a_load_tie (test_leads.TestAssignment.test_smallest_id_wins_a_load_tie)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 158, in test_smallest_id_wins_a_load_tie
    self.assertEqual(crm.leads[first]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 9. Rep assignment: unassignable leads join the FIFO queue

Guard removed: `waiting-enqueue` (mode `waiting-enqueue`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py waiting-enqueue" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-s6x72bvv/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py waiting-enqueue
guard removed: waiting-enqueue
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
..........F....F.F..F............................................................F....
======================================================================
FAIL: test_winning_assigns_exactly_one_waiting_lead_per_freed_slot (test_atomicity.TestFailedCallsLeaveNoTrace.test_winning_assigns_exactly_one_waiting_lead_per_freed_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 156, in test_winning_assigns_exactly_one_waiting_lead_per_freed_slot
    self.assertEqual(crm.waiting, [waiting])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2']

Second list contains 1 additional elements.
First extra element 0:
'L2'

- []
+ ['L2']

======================================================================
FAIL: test_leads_queue_when_every_rep_is_at_capacity (test_leads.TestAssignment.test_leads_queue_when_every_rep_is_at_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 199, in test_leads_queue_when_every_rep_is_at_capacity
    self.assertEqual(crm.waiting, [third, fourth])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L3', 'L4']

Second list contains 2 additional elements.
First extra element 0:
'L3'

- []
+ ['L3', 'L4']

======================================================================
FAIL: test_manager_never_receives_work (test_leads.TestAssignment.test_manager_never_receives_work)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 185, in test_manager_never_receives_work
    self.assertEqual(crm.waiting, [lead])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L1']

Second list contains 1 additional elements.
First extra element 0:
'L1'

- []
+ ['L1']

======================================================================
FAIL: test_waiting_queue_is_fifo_and_respects_capacity (test_leads.TestAssignment.test_waiting_queue_is_fifo_and_respects_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 213, in test_waiting_queue_is_fifo_and_respects_capacity
    self.assertEqual(crm.waiting, [second, third])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2', 'L3']

Second list contains 2 additional elements.
First extra element 0:
'L2'

- []
+ ['L2', 'L3']

======================================================================
FAIL: test_transfer_is_impossible_while_leads_are_waiting (test_transfers.TestTransfer.test_transfer_is_impossible_while_leads_are_waiting)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 118, in test_transfer_is_impossible_while_leads_are_waiting
    self.assertEqual(crm.waiting, [waiting])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L3']

Second list contains 1 additional elements.
First extra element 0:
'L3'

- []
+ ['L3']

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 10. Slot freeing: a rep may not be filled past capacity

Guard removed: `free-capacity` (mode `free-capacity`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py free-capacity" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ua47bl8s/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py free-capacity
guard removed: free-capacity
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
....................F.................................................................
======================================================================
FAIL: test_waiting_queue_is_fifo_and_respects_capacity (test_leads.TestAssignment.test_waiting_queue_is_fifo_and_respects_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 220, in test_waiting_queue_is_fifo_and_respects_capacity
    self.assertIsNone(crm.leads[third]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 11. Slot freeing: the waiting queue is FIFO

Guard removed: `queue-fifo` (mode `queue-fifo`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py queue-fifo" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-c4_zem9b/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py queue-fifo
guard removed: queue-fifo
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
....................F.................................................................
======================================================================
FAIL: test_waiting_queue_is_fifo_and_respects_capacity (test_leads.TestAssignment.test_waiting_queue_is_fifo_and_respects_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 219, in test_waiting_queue_is_fifo_and_respects_capacity
    self.assertEqual(crm.leads[second]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 12. Permission: unknown actor is rejected first

Guard removed: `permission-actor` (mode `permission-actor`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py permission-actor" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-f_erj_v2/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py permission-actor
guard removed: permission-actor
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.........E.EEE........................................................................
======================================================================
ERROR: test_unknown_actor_never_mutates (test_atomicity.TestFailedCallsLeaveNoTrace.test_unknown_actor_never_mutates)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 140, in test_unknown_actor_never_mutates
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 132, in <lambda>
    lambda: crm.add_lead("z@acme.com", "Z", "web", "ghost"),
            ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 72, in add_lead
    self._user(actor)
    ~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 46, in _user
    return self._users[actor]
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_non_string_actor_is_a_permission_error (test_leads.TestActorValidation.test_non_string_actor_is_a_permission_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 46, in test_non_string_actor_is_a_permission_error
    crm.add_lead("a@b.com", "A", "web", None)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 72, in add_lead
    self._user(actor)
    ~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 46, in _user
    return self._users[actor]
           ~~~~~~~~~~~^^^^^^^
KeyError: None

======================================================================
ERROR: test_unknown_actor_flagrant_before_any_other_check (test_leads.TestActorValidation.test_unknown_actor_flagrant_before_any_other_check)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 39, in test_unknown_actor_flagrant_before_any_other_check
    crm.add_lead(7, "", "ads", "ghost")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 72, in add_lead
    self._user(actor)
    ~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 46, in _user
    return self._users[actor]
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

======================================================================
ERROR: test_unknown_actor_is_a_permission_error_everywhere (test_leads.TestActorValidation.test_unknown_actor_is_a_permission_error_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 31, in test_unknown_actor_is_a_permission_error_everywhere
    call()
    ~~~~^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 23, in <lambda>
    lambda: crm.add_lead("x@acme.com", "X", "web", "ghost"),
            ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 72, in add_lead
    self._user(actor)
    ~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 46, in _user
    return self._users[actor]
           ~~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 13. Permission: only the owner or a manager may act

Guard removed: `permission-owner` (mode `permission-owner`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py permission-owner" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-o8yckzss/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py permission-owner
guard removed: permission-owner
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
..F.F.............................FE...F.......F.......FE........F....................
======================================================================
ERROR: test_permission_is_checked_before_status (test_leads.TestQualify.test_permission_is_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 251, in test_permission_is_checked_before_status
    self.crm.qualify(self.lead, "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 115, in qualify
    raise ValueError("lead %r is not new" % (lead_id,))
ValueError: lead 'L1' is not new

======================================================================
ERROR: test_permission_is_checked_before_status (test_opps.TestConvert.test_permission_is_checked_before_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 51, in test_permission_is_checked_before_status
    self.crm.convert(unqualified, 100, "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 129, in convert
    raise ValueError("lead %r is not qualified" % (lead_id,))
ValueError: lead 'L2' is not qualified

======================================================================
FAIL: test_failed_advance_keeps_the_stage_and_the_log (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_advance_keeps_the_stage_and_the_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 73, in test_failed_advance_keeps_the_stage_and_the_log
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_failed_convert_by_stranger_leaves_everything_intact (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_convert_by_stranger_leaves_everything_intact)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 61, in test_failed_convert_by_stranger_leaves_everything_intact
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_only_owner_or_manager_may_qualify (test_leads.TestQualify.test_only_owner_or_manager_may_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 243, in test_only_owner_or_manager_may_qualify
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unowned_lead_needs_a_manager (test_leads.TestQualify.test_unowned_lead_needs_a_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 302, in test_unowned_lead_needs_a_manager
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_only_owner_or_manager_may_advance (test_opps.TestAdvance.test_only_owner_or_manager_may_advance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 118, in test_only_owner_or_manager_may_advance
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_only_owner_or_manager_may_convert (test_opps.TestConvert.test_only_owner_or_manager_may_convert)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 43, in test_only_owner_or_manager_may_convert
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_only_owner_or_manager_may_discount (test_opps.TestDiscount.test_only_owner_or_manager_may_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 203, in test_only_owner_or_manager_may_discount
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=7, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 14. Qualification: score threshold of 30

Guard removed: `qualify-score` (mode `qualify-score`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py qualify-score" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-i04yfpnt/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py qualify-score
guard removed: qualify-score
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.......F........................F...F.................................................
======================================================================
FAIL: test_failed_qualify_leaves_the_status_new (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_qualify_leaves_the_status_new)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 39, in test_failed_qualify_leaves_the_status_new
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_event_lead_at_twenty_is_rejected (test_leads.TestQualify.test_event_lead_at_twenty_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 290, in test_event_lead_at_twenty_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_threshold_is_thirty (test_leads.TestQualify.test_score_threshold_is_thirty)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_leads.py", line 271, in test_score_threshold_is_thirty
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 15. Stage transition: only lost or the immediate next stage

Guard removed: `stage-next` (mode `stage-next`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py stage-next" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-59pyt6_8/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py stage-next
guard removed: stage-next
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
..F..........................................E..F.....................................
======================================================================
ERROR: test_illegal_transition_verdict_wins_over_big_deal_gate (test_opps.TestAdvance.test_illegal_transition_verdict_wins_over_big_deal_gate)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 183, in test_illegal_transition_verdict_wins_over_big_deal_gate
    self.crm.advance(self.opp, "negotiation", "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 159, in advance
    if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor): raise PermissionError("negotiation over 50000 needs a manager")  # GC-BIGDEAL
                                                                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: negotiation over 50000 needs a manager

======================================================================
FAIL: test_failed_advance_keeps_the_stage_and_the_log (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_advance_keeps_the_stage_and_the_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 75, in test_failed_advance_keeps_the_stage_and_the_log
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_skipping_or_reversing_a_stage_is_rejected (test_opps.TestAdvance.test_skipping_or_reversing_a_stage_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 145, in test_skipping_or_reversing_a_stage_is_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 16. Stage transition: final stages are frozen

Guard removed: `stage-final` (mode `stage-final`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py stage-final" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-43scar0r/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py stage-final
guard removed: stage-final
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
............................................F.........................................
======================================================================
FAIL: test_final_stage_cannot_move (test_opps.TestAdvance.test_final_stage_cannot_move)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 128, in test_final_stage_cannot_move
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 17. Big-deal approval: negotiation above 50000 needs a manager

Guard removed: `bigdeal` (mode `bigdeal`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py bigdeal" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-vpykeaw2/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py bigdeal
guard removed: bigdeal
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
...F......................................F...........................................
======================================================================
FAIL: test_failed_big_deal_advance_keeps_the_stage (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_big_deal_advance_keeps_the_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 87, in test_failed_big_deal_advance_keeps_the_stage
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_big_deal_needs_a_manager_to_enter_negotiation (test_opps.TestAdvance.test_big_deal_needs_a_manager_to_enter_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 165, in test_big_deal_needs_a_manager_to_enter_negotiation
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 18. Discount: pct must be an int in 1..30

Guard removed: `discount-range` (mode `discount-range`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py discount-range" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9zqyh2wi/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py discount-range
guard removed: discount-range
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
..................................................................F...................
======================================================================
FAIL: test_pct_must_be_an_int_between_one_and_thirty (test_opps.TestDiscount.test_pct_must_be_an_int_between_one_and_thirty)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 198, in test_pct_must_be_an_int_between_one_and_thirty
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 19. Discount: a rep may use at most 10 percent

Guard removed: `discount-rep` (mode `discount-rep`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py discount-rep" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0pdklk3u/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py discount-rep
guard removed: discount-rep
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
......E.............................................................F.................
======================================================================
ERROR: test_failed_discount_keeps_amount_and_log (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_discount_keeps_amount_and_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 102, in test_failed_discount_keeps_amount_and_log
    crm.discount(opp, 15, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 177, in discount
    if new_amount * 100 < opp["original_amount"] * 70: raise ValueError("cumulative discount would exceed 30 percent")  # GC-DISC-FLOOR
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: cumulative discount would exceed 30 percent

======================================================================
FAIL: test_rep_may_not_exceed_ten_percent (test_opps.TestDiscount.test_rep_may_not_exceed_ten_percent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 216, in test_rep_may_not_exceed_ten_percent
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 20. Discount: final opportunities are frozen

Guard removed: `discount-final` (mode `discount-final`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py discount-final" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xjs9ysce/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py discount-final
guard removed: discount-final
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
...............................................................F...E..................
======================================================================
ERROR: test_rep_limit_is_checked_before_the_floor (test_opps.TestDiscount.test_rep_limit_is_checked_before_the_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 251, in test_rep_limit_is_checked_before_the_floor
    self.crm.discount(self.opp, 20, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 174, in discount
    if pct > 10 and not self._is_manager(actor): raise PermissionError("discount over 10 percent needs a manager")  # GC-DISC-REP
                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: discount over 10 percent needs a manager

======================================================================
FAIL: test_final_stage_cannot_be_discounted (test_opps.TestDiscount.test_final_stage_cannot_be_discounted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 211, in test_final_stage_cannot_be_discounted
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 21. Discount: cumulative floor of 70 percent of the original amount

Guard removed: `discount-floor` (mode `discount-floor`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py discount-floor" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-lwscedb0/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py discount-floor
guard removed: discount-floor
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
......F......................................................FF.......................
======================================================================
FAIL: test_failed_discount_keeps_amount_and_log (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_discount_keeps_amount_and_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 99, in test_failed_discount_keeps_amount_and_log
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cumulative_discount_may_not_cross_thirty_percent (test_opps.TestDiscount.test_cumulative_discount_may_not_cross_thirty_percent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 230, in test_cumulative_discount_may_not_cross_thirty_percent
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cumulative_floor_is_exact (test_opps.TestDiscount.test_cumulative_floor_is_exact)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 241, in test_cumulative_floor_is_exact
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 22. Transfer: manager only

Guard removed: `transfer-manager` (mode `transfer-manager`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-manager" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-pp0h3w92/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-manager
guard removed: transfer-manager
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
........E..................................................................EF.........
======================================================================
ERROR: test_failed_transfer_keeps_owner_log_and_queue (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_transfer_keeps_owner_log_and_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 119, in test_failed_transfer_keeps_owner_log_and_queue
    crm.transfer(opp, "r2", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 191, in transfer
    if self.load(new_owner) >= target["capacity"]: raise ValueError("rep %r is at capacity" % (new_owner,))  # GC-TRANSFER-CAP
                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: rep 'r2' is at capacity

======================================================================
ERROR: test_manager_check_precedes_target_validation (test_transfers.TestTransfer.test_manager_check_precedes_target_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 41, in test_manager_check_precedes_target_validation
    self.crm.transfer(self.opp, "nobody", "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-neutral-3/crm.py", line 188, in transfer
    if target is None or target["role"] != "rep": raise ValueError("new owner must be a rep: %r" % (new_owner,))  # GC-TRANSFER-ROLE
                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: new owner must be a rep: 'nobody'

======================================================================
FAIL: test_only_a_manager_may_transfer (test_transfers.TestTransfer.test_only_a_manager_may_transfer)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 34, in test_only_a_manager_may_transfer
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=1, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 23. Transfer: new owner must be a rep

Guard removed: `transfer-role` (mode `transfer-role`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-role" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-x_tcbhg5/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-role
guard removed: transfer-role
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
..............................................................................F.......
======================================================================
FAIL: test_target_must_be_a_rep (test_transfers.TestTransfer.test_target_must_be_a_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 45, in test_target_must_be_a_rep
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 24. Transfer: final opportunities are frozen

Guard removed: `transfer-final` (mode `transfer-final`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-final" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-j8iy3gxo/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-final
guard removed: transfer-final
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
..........................................................................F...........
======================================================================
FAIL: test_final_opportunity_cannot_be_transferred (test_transfers.TestTransfer.test_final_opportunity_cannot_be_transferred)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 52, in test_final_opportunity_cannot_be_transferred
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 25. Transfer: new owner must differ from the current owner

Guard removed: `transfer-same` (mode `transfer-same`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-same" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-pdhco6pv/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-same
guard removed: transfer-same
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
...............................................................................F......
======================================================================
FAIL: test_target_must_differ_from_current_owner (test_transfers.TestTransfer.test_target_must_differ_from_current_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 57, in test_target_must_differ_from_current_owner
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 26. Transfer: new owner must be below capacity

Guard removed: `transfer-cap` (mode `transfer-cap`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-cap" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-v3e1osxo/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py transfer-cap
guard removed: transfer-cap
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
........F.......................................................................FF....
======================================================================
FAIL: test_failed_transfer_keeps_owner_log_and_queue (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_transfer_keeps_owner_log_and_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 116, in test_failed_transfer_keeps_owner_log_and_queue
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_target_must_have_free_capacity (test_transfers.TestTransfer.test_target_must_have_free_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 74, in test_target_must_have_free_capacity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_transfer_is_impossible_while_leads_are_waiting (test_transfers.TestTransfer.test_transfer_is_impossible_while_leads_are_waiting)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_transfers.py", line 121, in test_transfer_is_impossible_while_leads_are_waiting
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 27. Atomicity: a failed add_lead does not burn an id

Guard removed: `atomic-id` (mode `atomic-id`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py atomic-id" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-hc6qeklo/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py atomic-id
guard removed: atomic-id
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.F....................................................................................
======================================================================
FAIL: test_failed_add_lead_does_not_burn_an_id (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_add_lead_does_not_burn_an_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 23, in test_failed_add_lead_does_not_burn_an_id
    self.assertEqual(crm.add_lead("buyer@acme.com", "Ada", "web", "r1"), "L1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'L2' != 'L1'
- L2
+ L1


----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 28. Atomicity: a failed convert does not mutate the lead

Guard removed: `atomic-state` (mode `atomic-state`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py atomic-state" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-46ecwtfy/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py atomic-state
guard removed: atomic-state
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.....F..............................................F.................................
======================================================================
FAIL: test_failed_convert_leaves_the_lead_qualified_and_no_opposition (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_convert_leaves_the_lead_qualified_and_no_opposition)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 52, in test_failed_convert_leaves_the_lead_qualified_and_no_opposition
    self.assertEqual(crm.leads[lead]["status"], "qualified")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'converted' != 'qualified'
- converted
+ qualified


======================================================================
FAIL: test_amount_must_be_a_positive_int_and_not_a_bool (test_opps.TestConvert.test_amount_must_be_a_positive_int_and_not_a_bool)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_opps.py", line 36, in test_amount_must_be_a_positive_int_and_not_a_bool
    self.assertEqual(self.crm.leads[self.lead]["status"], "qualified")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'converted' != 'qualified'
- converted
+ qualified


----------------------------------------------------------------------
Ran 86 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held

## 29. Atomicity: a failed discount does not log

Guard removed: `atomic-log` (mode `atomic-log`).

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-neutral-3/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py atomic-log" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

Verbatim output:

```
$ backed up /tmp/aep-lab/pilot2/N-neutral-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-d7jt85k4/crm.py
$ python3 /tmp/aep-lab/pilot2/N-neutral-3/_break.py atomic-log
guard removed: atomic-log
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect FAILURE matching /FAILED/
......F...............................................................................
======================================================================
FAIL: test_failed_discount_keeps_amount_and_log (test_atomicity.TestFailedCallsLeaveNoTrace.test_failed_discount_keeps_amount_and_log)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-neutral-3/test_atomicity.py", line 104, in test_failed_discount_keeps_amount_and_log
    self.assertEqual(crm.log, log_before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[60 chars]O1', 'r1'), ('discount', 'O1', 'm1'), ('discount', 'O1', 'm1')] != [('ad[60 chars]O1', 'r1'), ('discount', 'O1', 'm1')]

First list contains 1 additional elements.
First extra element 4:
('discount', 'O1', 'm1')

  [('add_lead', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
   ('convert', 'O1', 'r1'),
-  ('discount', 'O1', 'm1'),
   ('discount', 'O1', 'm1')]

----------------------------------------------------------------------
Ran 86 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-neutral-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-neutral-3 -p "test*.py"   # expect SUCCESS
......................................................................................
----------------------------------------------------------------------
Ran 86 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

Exit code: 0 -- control held
