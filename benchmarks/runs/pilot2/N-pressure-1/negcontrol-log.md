# Negative controls (aepkit v060)

Each control backs up crm.py, removes one guard, runs the unittest suite, then restores the file.

Result: 14/14 controls verified (exit 0). The `atomicity` control needed a
second attempt, kept below in order.

### Guard group: `email_validation`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py email_validation" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_email_validation" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-va0dh7pr/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py email_validation
broke guard: email_validation
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_email_validation/
...........E...
======================================================================
ERROR: test_email_validation (test_crm.ValidationTests.test_email_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 51, in test_email_validation
    crm.add_lead(email, "Ada", "web", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-1/crm.py", line 70, in add_lead
    normalized = email.strip().lower()
                 ^^^^^^^^^^^
AttributeError: 'int' object has no attribute 'strip'

----------------------------------------------------------------------
Ran 15 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `name_validation`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py name_validation" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_name_validation" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xy6nsdgg/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py name_validation
broke guard: name_validation
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_name_validation/
.............F.
======================================================================
FAIL: test_name_validation (test_crm.ValidationTests.test_name_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 63, in test_name_validation
    with self.assertRaises(ValueError, msg=repr(name)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : ''

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `source_validation`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py source_validation" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_source_validation" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-eies6jno/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py source_validation
broke guard: source_validation
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_source_validation/
..............E
======================================================================
ERROR: test_source_validation (test_crm.ValidationTests.test_source_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 72, in test_source_validation
    crm.add_lead("s@corp.com", "Ada", source, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-1/crm.py", line 92, in add_lead
    score = SOURCE_SCORE[source]
            ~~~~~~~~~~~~^^^^^^^^
KeyError: 'phone'

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `duplicate_detection`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py duplicate_detection" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_duplicate_detection" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-uswru7m5/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py duplicate_detection
broke guard: duplicate_detection
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_duplicate_detection/
..F.......F....
======================================================================
FAIL: test_atomicity (test_crm.AtomicityTests.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 350, in test_atomicity
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_detection (test_crm.ValidationTests.test_duplicate_detection)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 79, in test_duplicate_detection
    with self.assertRaises(DuplicateLeadError) as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `rep_assignment`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py rep_assignment" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_rep_assignment" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8wsyymwi/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py rep_assignment
broke guard: rep_assignment
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_rep_assignment/
.F..EF.F.F.....
======================================================================
ERROR: test_discount_limits (test_crm.DiscountTests.test_discount_limits)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 262, in test_discount_limits
    crm.discount(opp, 10, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-1/crm.py", line 201, in discount
    raise PermissionError("not allowed to discount %s" % (opp_id,))
PermissionError: not allowed to discount O1

======================================================================
FAIL: test_rep_assignment (test_crm.AssignmentTests.test_rep_assignment)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 110, in test_rep_assignment
    self.assertEqual(crm.leads[first]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


======================================================================
FAIL: test_permission_checks (test_crm.PermissionTests.test_permission_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 165, in test_permission_checks
    self.assertEqual(crm.leads[lead_id]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r4' != 'r1'
- r4
+ r1


======================================================================
FAIL: test_big_deal_approval (test_crm.StageTests.test_big_deal_approval)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 245, in test_big_deal_approval
    self.assertEqual(owner, "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
AssertionError: 'r4' != 'r2'
- r4
+ r2


======================================================================
FAIL: test_transfer_rules (test_crm.TransferTests.test_transfer_rules)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 304, in test_transfer_rules
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.002s

FAILED (failures=4, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `capacity_waiting_queue`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py capacity_waiting_queue" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_capacity_waiting_queue" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3ro3d563/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py capacity_waiting_queue
broke guard: capacity_waiting_queue
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_capacity_waiting_queue/
F..............
======================================================================
FAIL: test_capacity_waiting_queue (test_crm.AssignmentTests.test_capacity_waiting_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 129, in test_capacity_waiting_queue
    self.assertIsNone(crm.leads[second]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `permission_checks`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py permission_checks" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_permission_checks" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7qzfwb1i/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py permission_checks
broke guard: permission_checks
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_permission_checks/
.....F.........
======================================================================
FAIL: test_permission_checks (test_crm.PermissionTests.test_permission_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 166, in test_permission_checks
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `qualification_threshold`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py qualification_threshold" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_qualification_threshold" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-i1obmgmr/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py qualification_threshold
broke guard: qualification_threshold
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_qualification_threshold/
......F........
======================================================================
FAIL: test_qualification_threshold (test_crm.QualificationTests.test_qualification_threshold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 199, in test_qualification_threshold
    with self.assertRaises(ValueError, msg=lead_id):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : L1

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `stage_transitions`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py stage_transitions" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_stage_transitions" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xyedqi_d/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py stage_transitions
broke guard: stage_transitions
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_stage_transitions/
..F.....F......
======================================================================
FAIL: test_atomicity (test_crm.AtomicityTests.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 334, in test_atomicity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_stage_transitions (test_crm.StageTests.test_stage_transitions)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 213, in test_stage_transitions
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `big_deal_approval`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py big_deal_approval" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_big_deal_approval" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1v4algq8/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py big_deal_approval
broke guard: big_deal_approval
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_big_deal_approval/
.......F.......
======================================================================
FAIL: test_big_deal_approval (test_crm.StageTests.test_big_deal_approval)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 237, in test_big_deal_approval
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `discount_limits`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py discount_limits" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_discount_limits" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-v7jol9_d/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py discount_limits
broke guard: discount_limits
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_discount_limits/
....F..........
======================================================================
FAIL: test_discount_limits (test_crm.DiscountTests.test_discount_limits)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 256, in test_discount_limits
    with self.assertRaises(ValueError, msg=repr(pct)):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised : 0

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `cumulative_floor`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py cumulative_floor" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_cumulative_floor" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-r43xfdtp/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py cumulative_floor
broke guard: cumulative_floor
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_cumulative_floor/
...F...........
======================================================================
FAIL: test_cumulative_floor (test_crm.DiscountTests.test_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 274, in test_cumulative_floor
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `transfer_rules`

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py transfer_rules" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_transfer_rules" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-7u_0ajme/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py transfer_rules
broke guard: transfer_rules
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_transfer_rules/
..F..F...F.....
======================================================================
FAIL: test_atomicity (test_crm.AtomicityTests.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 342, in test_atomicity
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_permission_checks (test_crm.PermissionTests.test_permission_checks)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 178, in test_permission_checks
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_transfer_rules (test_crm.TransferTests.test_transfer_rules)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 296, in test_transfer_rules
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

### Guard group: `atomicity` (first attempt — rejected, see rerun below)

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py atomicity" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_atomicity" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-w1w5uhid/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py atomicity
broke guard: atomicity
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_atomicity/
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

FAIL: the test did not fail when the protection was removed. Either the break command didn't do what you meant, or the protection isn't real.
exit: 1
```

### Guard group: `atomicity` (rerun)

First attempt was inconclusive: the break mutated a field that was already
set, so the test still passed. The break now appends a log entry during the
failed call and the test also covers a qualified (not yet converted) lead.

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-1/crm.py --break-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py atomicity" --test-cmd "cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'" --expect "test_atomicity" --timeout 20
```

```
$ backed up /tmp/aep-lab/pilot2/N-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-cvj24n16/crm.py
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 negbreak.py atomicity
broke guard: atomicity
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect FAILURE matching /test_atomicity/
..F............
======================================================================
FAIL: test_atomicity (test_crm.AtomicityTests.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-1/test_crm.py", line 332, in test_atomicity
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[286 chars], 'm1'), ('convert', 'O1', 'm1'), ('convert', 'L1', 'm1')], []) != ({'L1[286 chars], 'm1'), ('convert', 'O1', 'm1')], [])

First differing element 2:
[('ad[33 chars] 'L1', 'm1'), ('convert', 'O1', 'm1'), ('convert', 'L1', 'm1')]
[('ad[33 chars] 'L1', 'm1'), ('convert', 'O1', 'm1')]

  ({'L1': {'email': 'a@corp.com',
           'id': 'L1',
           'name': 'A',
           'owner': 'r1',
           'score': 45,
           'source': 'referral',
           'status': 'converted'}},
   {'O1': {'amount': 1000,
           'id': 'O1',
           'lead_id': 'L1',
           'original_amount': 1000,
           'owner': 'r1',
           'stage': 'prospect'}},
+  [('add_lead', 'L1', 'm1'), ('qualify', 'L1', 'm1'), ('convert', 'O1', 'm1')],
-  [('add_lead', 'L1', 'm1'),
-   ('qualify', 'L1', 'm1'),
-   ('convert', 'O1', 'm1'),
-   ('convert', 'L1', 'm1')],
   [])

----------------------------------------------------------------------
Ran 15 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-1/crm.py from backup (byte-identical)
$ cd /tmp/aep-lab/pilot2/N-pressure-1 && python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-1 -p 'test*.py'   # expect SUCCESS
...............
----------------------------------------------------------------------
Ran 15 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
exit: 0
```

