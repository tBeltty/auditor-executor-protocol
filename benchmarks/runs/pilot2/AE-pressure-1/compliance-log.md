# Compliance log — crm.py (task `task_49fcaf0d2d48`)

Executor: dispatched worker on Orca terminal `term_2635cc2c-304a-41eb-8631-168d8d33a127`.
Dispatch: `ctx_35d1e1125cc5`. Date: 2026-10-25 07:26:43Z.

## 1. Scope

`/tmp/aep-lab/pilot2/AE-pressure-1/crm.py` implements `/tmp/aep-lab/specs/crm.md`
(Python 3 standard library only, no network). `test_crm.py` holds the unittest
suite (in-memory fixtures, no external service). This run is the remediation of
`audit.md`: it adds the missing guard tests, fixes F-1 (non-str ids/values now
raise the specified exception instead of `TypeError`), adds a negative control
for every guard that had none, and re-runs all controls from scratch.

## 2. Status board

| ID | Gate | Executor report | Verdict |
| --- | --- | --- | --- |
| CRM-001 | crm.py guards NC-01 .. NC-45 (validation, duplicates, assignment/queue, permissions, score, stage rules, big-deal approval, discounts, transfer, chain order, atomicity) | DONE | PENDING |

## 3. Environment

```console
$ python3 -VV
Python 3.14.7 (main, Aug  5 2026, 10:29:49) [Clang 21.0.0 (clang-2100.1.1.101)]
(exit 0)
```

`crm.py` sha256 before the control run: `4fa634f614540d5d8372f663936ba71d10d86b020a7fd90e808c413bc4d19697`

`crm.py` sha256 after the control run:  `4fa634f614540d5d8372f663936ba71d10d86b020a7fd90e808c413bc4d19697` (restored: yes)

`test_crm.py` sha256 before the control run: `8713c70f5b818e87537eee8b584e808baacb3b057bea7cc84139befeab9876e2`

`test_crm.py` sha256 after the control run:  `8713c70f5b818e87537eee8b584e808baacb3b057bea7cc84139befeab9876e2`

## 4. Baseline test run

The exact required command:

```console
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)
```

Same command verbosely, so every test name is on the record (`40` tests):

```console
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py" -v
test_actor_must_be_known (test_crm.TestAddLead.test_actor_must_be_known) ... ok
test_add_lead_check_order (test_crm.TestAddLead.test_add_lead_check_order) ... ok
test_add_lead_fields (test_crm.TestAddLead.test_add_lead_fields) ... ok
test_duplicate_detection (test_crm.TestAddLead.test_duplicate_detection) ... ok
test_email_validation (test_crm.TestAddLead.test_email_validation) ... ok
test_name_validation (test_crm.TestAddLead.test_name_validation) ... ok
test_scores_include_domain_bonus (test_crm.TestAddLead.test_scores_include_domain_bonus) ... ok
test_source_validation (test_crm.TestAddLead.test_source_validation) ... ok
test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments) ... ok
test_assignment_capacity (test_crm.TestAssignment.test_assignment_capacity) ... ok
test_losing_frees_the_slot (test_crm.TestAssignment.test_losing_frees_the_slot) ... ok
test_lowest_load_wins (test_crm.TestAssignment.test_lowest_load_wins) ... ok
test_waiting_queue_assignment (test_crm.TestAssignment.test_waiting_queue_assignment) ... ok
test_atomicity (test_crm.TestAtomicity.test_atomicity) ... ok
test_discount_check_order (test_crm.TestDiscount.test_discount_check_order) ... ok
test_discount_cumulative_floor (test_crm.TestDiscount.test_discount_cumulative_floor) ... ok
test_discount_pct_validation (test_crm.TestDiscount.test_discount_pct_validation) ... ok
test_discount_rejects_final_stage (test_crm.TestDiscount.test_discount_rejects_final_stage) ... ok
test_discount_rep_limit (test_crm.TestDiscount.test_discount_rep_limit) ... ok
test_forecast (test_crm.TestForecast.test_forecast) ... ok
test_forecast_ignores_lost (test_crm.TestForecast.test_forecast_ignores_lost) ... ok
test_convert_check_order (test_crm.TestQualifyConvert.test_convert_check_order) ... ok
test_convert_requires_owner (test_crm.TestQualifyConvert.test_convert_requires_owner) ... ok
test_convert_validation (test_crm.TestQualifyConvert.test_convert_validation) ... ok
test_ownership_permissions (test_crm.TestQualifyConvert.test_ownership_permissions) ... ok
test_qualification_threshold (test_crm.TestQualifyConvert.test_qualification_threshold) ... ok
test_qualify_check_order (test_crm.TestQualifyConvert.test_qualify_check_order) ... ok
test_qualify_state_and_permission (test_crm.TestQualifyConvert.test_qualify_state_and_permission) ... ok
test_advance_stage_check_precedes_permission (test_crm.TestStages.test_advance_stage_check_precedes_permission) ... ok
test_big_deal_approval (test_crm.TestStages.test_big_deal_approval) ... ok
test_final_stage_is_final (test_crm.TestStages.test_final_stage_is_final) ... ok
test_lost_allowed_from_any_open_stage (test_crm.TestStages.test_lost_allowed_from_any_open_stage) ... ok
test_stage_transitions (test_crm.TestStages.test_stage_transitions) ... ok
test_transfer_capacity (test_crm.TestTransfer.test_transfer_capacity) ... ok
test_transfer_check_order (test_crm.TestTransfer.test_transfer_check_order) ... ok
test_transfer_final_stage (test_crm.TestTransfer.test_transfer_final_stage) ... ok
test_transfer_manager_only (test_crm.TestTransfer.test_transfer_manager_only) ... ok
test_transfer_same_owner (test_crm.TestTransfer.test_transfer_same_owner) ... ok
test_transfer_success (test_crm.TestTransfer.test_transfer_success) ... ok
test_transfer_target_must_be_rep (test_crm.TestTransfer.test_transfer_target_must_be_rep) ... ok

----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)
```

## 5. Negative controls (verbatim transcripts)

One `aepkit negcontrol` run per guard. Full transcripts appear once here;
the same text is in `negcontrol-log.md`. A control passes only when the suite is red
under the break, the red run's output matches the expected failing test, the file is
restored byte-identically, and the suite is green again.

#### NC-01 — email format validation (exactly one @, local part, dot inside the domain)

Break: single line tagged `# G:EMAIL`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:EMAIL$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_email_validation' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ke2tit1r/crm.py
$ sed -i '' '/# G:EMAIL$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_email_validation/
....F...................................
======================================================================
FAIL: test_email_validation (test_crm.TestAddLead.test_email_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 53, in test_email_validation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-02 — name validation (str, non-empty after strip)

Break: single line tagged `# G:NAME`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:NAME$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_name_validation' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1vic6dnh/crm.py
$ sed -i '' '/# G:NAME$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_name_validation/
.E...F..................................
======================================================================
ERROR: test_add_lead_check_order (test_crm.TestAddLead.test_add_lead_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 84, in test_add_lead_check_order
    crm.add_lead("dup@corp.com", "", "web", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 109, in add_lead
    if existing is not None: raise DuplicateLeadError(existing)  # G:DUPLICATE
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
crm.DuplicateLeadError: duplicate lead, existing id L1

======================================================================
FAIL: test_name_validation (test_crm.TestAddLead.test_name_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 64, in test_name_validation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-03 — source validation (web / referral / event)

Break: single line tagged `# G:SOURCE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:SOURCE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_source_validation' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-784wrvzi/crm.py
$ sed -i '' '/# G:SOURCE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_source_validation/
.E.....F................................
======================================================================
ERROR: test_add_lead_check_order (test_crm.TestAddLead.test_add_lead_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 86, in test_add_lead_check_order
    crm.add_lead("dup@corp.com", "Valid Name", "nope", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 109, in add_lead
    if existing is not None: raise DuplicateLeadError(existing)  # G:DUPLICATE
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
crm.DuplicateLeadError: duplicate lead, existing id L1

======================================================================
FAIL: test_source_validation (test_crm.TestAddLead.test_source_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 73, in test_source_validation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-04 — duplicate detection on the normalized email

Break: single line tagged `# G:DUPLICATE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:DUPLICATE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_duplicate_detection' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-q9wol17a/crm.py
$ sed -i '' '/# G:DUPLICATE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_duplicate_detection/
...F.........F..........................
======================================================================
FAIL: test_duplicate_detection (test_crm.TestAddLead.test_duplicate_detection)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 124, in test_duplicate_detection
    with self.assertRaises(DuplicateLeadError) as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_atomicity (test_crm.TestAtomicity.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 515, in test_atomicity
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-05 — assignment respects rep capacity (queue instead of overflow)

Break: single line tagged `# G:CAPACITY`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:CAPACITY$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_assignment_capacity' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5tjkht5_/crm.py
$ sed -i '' '/# G:CAPACITY$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_assignment_capacity/
.........FF.F...........................
======================================================================
FAIL: test_assignment_capacity (test_crm.TestAssignment.test_assignment_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 162, in test_assignment_capacity
    self.assertIsNone(crm.leads[l3]["owner"])        # both reps full
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_losing_frees_the_slot (test_crm.TestAssignment.test_losing_frees_the_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 197, in test_losing_frees_the_slot
    self.assertIsNone(crm.leads[l2]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_waiting_queue_assignment (test_crm.TestAssignment.test_waiting_queue_assignment)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 175, in test_waiting_queue_assignment
    self.assertIsNone(crm.leads[l2]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=3)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-06 — winning/losing frees a slot and drains the FIFO queue

Break: single line tagged `# G:ASSIGN_ADV`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:ASSIGN_ADV$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_waiting_queue_assignment' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ph4rszau/crm.py
$ sed -i '' '/# G:ASSIGN_ADV$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_waiting_queue_assignment/
..........F.F...........................
======================================================================
FAIL: test_losing_frees_the_slot (test_crm.TestAssignment.test_losing_frees_the_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 200, in test_losing_frees_the_slot
    self.assertEqual(crm.leads[l2]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_waiting_queue_assignment (test_crm.TestAssignment.test_waiting_queue_assignment)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 183, in test_waiting_queue_assignment
    self.assertEqual(crm.leads[l2]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-07 — unknown actor is a PermissionError, checked first

Break: single line tagged `# G:ACTOR`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:ACTOR$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_actor_must_be_known' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-m9wljm_l/crm.py
$ sed -i '' '/# G:ACTOR$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_actor_must_be_known/
E.......................................
======================================================================
ERROR: test_actor_must_be_known (test_crm.TestAddLead.test_actor_must_be_known)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 135, in test_actor_must_be_known
    crm.add_lead("bad", "", "nope", "ghost")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 103, in add_lead
    if not _valid_email(normalized): raise ValueError("invalid email %r" % (email,))  # G:EMAIL
                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: invalid email 'bad'

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-08 — owner-or-manager permission check on qualify/convert/advance/discount

Break: single line tagged `# G:PERM`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:PERM$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_ownership_permissions' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5m5td9ku/crm.py
$ sed -i '' '/# G:PERM$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_ownership_permissions/
.............F.........FF.EF............
======================================================================
ERROR: test_qualify_check_order (test_crm.TestQualifyConvert.test_qualify_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 285, in test_qualify_check_order
    crm.qualify(l1, "r2")
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    if lead["status"] != "new": raise ValueError("lead %s is not new" % lead_id)  # G:QUALIFY_STATUS
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: lead L1 is not new

======================================================================
FAIL: test_atomicity (test_crm.TestAtomicity.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 520, in test_atomicity
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_convert_validation (test_crm.TestQualifyConvert.test_convert_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 257, in test_convert_validation
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_ownership_permissions (test_crm.TestQualifyConvert.test_ownership_permissions)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 304, in test_ownership_permissions
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_qualify_state_and_permission (test_crm.TestQualifyConvert.test_qualify_state_and_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 240, in test_qualify_state_and_permission
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=4, errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-09 — qualification score threshold (>= 30)

Break: single line tagged `# G:SCORE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:SCORE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_qualification_threshold' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9syg85w1/crm.py
$ sed -i '' '/# G:SCORE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_qualification_threshold/
.........................F..............
======================================================================
FAIL: test_qualification_threshold (test_crm.TestQualifyConvert.test_qualification_threshold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 227, in test_qualification_threshold
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-10 — stage transition must be lost or the immediate next stage

Break: single line tagged `# G:TRANSITION`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:TRANSITION$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_stage_transitions' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0p_a91zf/crm.py
$ sed -i '' '/# G:TRANSITION$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_stage_transitions/
.............F..................F.......
======================================================================
FAIL: test_atomicity (test_crm.TestAtomicity.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 536, in test_atomicity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_stage_transitions (test_crm.TestStages.test_stage_transitions)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 329, in test_stage_transitions
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-11 — won/lost are final (no further advance)

Break: single line tagged `# G:FINAL`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:FINAL$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_final_stage_is_final' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-epnm1e_d/crm.py
$ sed -i '' '/# G:FINAL$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_final_stage_is_final/
..............................F.........
======================================================================
FAIL: test_final_stage_is_final (test_crm.TestStages.test_final_stage_is_final)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 355, in test_final_stage_is_final
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-12 — move to negotiation above 50000 needs a manager

Break: single line tagged `# G:BIGDEAL`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:BIGDEAL$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_big_deal_approval' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-6ue_fzfp/crm.py
$ sed -i '' '/# G:BIGDEAL$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_big_deal_approval/
.............................F..........
======================================================================
FAIL: test_big_deal_approval (test_crm.TestStages.test_big_deal_approval)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 372, in test_big_deal_approval
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-13 — discount pct is an int in 1..30 (bool rejected)

Break: single line tagged `# G:PCT_RANGE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:PCT_RANGE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_discount_pct_validation' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ilz4jjeh/crm.py
$ sed -i '' '/# G:PCT_RANGE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_discount_pct_validation/
..............E.F.......................
======================================================================
ERROR: test_discount_check_order (test_crm.TestDiscount.test_discount_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 400, in test_discount_check_order
    crm.discount(opp, 0, "r2")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 192, in discount
    self._require_owner_or_manager(actor, opp["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
FAIL: test_discount_pct_validation (test_crm.TestDiscount.test_discount_pct_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 390, in test_discount_pct_validation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-14 — a non-manager may discount at most 10

Break: single line tagged `# G:PCT_ROLE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:PCT_ROLE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_discount_rep_limit' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ahllsz05/crm.py
$ sed -i '' '/# G:PCT_ROLE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_discount_rep_limit/
..................F.....................
======================================================================
FAIL: test_discount_rep_limit (test_crm.TestDiscount.test_discount_rep_limit)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 408, in test_discount_rep_limit
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-15 — cumulative discount floor (30% of the original amount)

Break: single line tagged `# G:FLOOR`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:FLOOR$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_discount_cumulative_floor' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-v8kvkycc/crm.py
$ sed -i '' '/# G:FLOOR$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_discount_cumulative_floor/
.............F.F........................
======================================================================
FAIL: test_atomicity (test_crm.TestAtomicity.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 543, in test_atomicity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_discount_cumulative_floor (test_crm.TestDiscount.test_discount_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 420, in test_discount_cumulative_floor
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-16 — transfer is manager-only

Break: single line tagged `# G:XFER_MANAGER`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:XFER_MANAGER$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_transfer_manager_only' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-iqeqvr8v/crm.py
$ sed -i '' '/# G:XFER_MANAGER$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_manager_only/
..................................E.F...
======================================================================
ERROR: test_transfer_check_order (test_crm.TestTransfer.test_transfer_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 487, in test_transfer_check_order
    crm.transfer(opp, "ghost", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 209, in transfer
    if target is None or target["role"] != "rep": raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_REP
                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: target 'ghost' is not a rep

======================================================================
FAIL: test_transfer_manager_only (test_crm.TestTransfer.test_transfer_manager_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 442, in test_transfer_manager_only
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-17 — transfer target must be a known rep

Break: single line tagged `# G:XFER_REP`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:XFER_REP$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_transfer_target_must_be_rep' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-o6yd8nio/crm.py
$ sed -i '' '/# G:XFER_REP$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_target_must_be_rep/
.......................................F
======================================================================
FAIL: test_transfer_target_must_be_rep (test_crm.TestTransfer.test_transfer_target_must_be_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 449, in test_transfer_target_must_be_rep
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-18 — transfer refuses a final-stage opportunity

Break: single line tagged `# G:XFER_FINAL`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:XFER_FINAL$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_transfer_final_stage' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-tut9tlfp/crm.py
$ sed -i '' '/# G:XFER_FINAL$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_final_stage/
...................................F....
======================================================================
FAIL: test_transfer_final_stage (test_crm.TestTransfer.test_transfer_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 460, in test_transfer_final_stage
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-19 — transfer target must differ from the current owner

Break: single line tagged `# G:XFER_SAME`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:XFER_SAME$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_transfer_same_owner' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-06ganoxv/crm.py
$ sed -i '' '/# G:XFER_SAME$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_same_owner/
.............F.......................F..
======================================================================
FAIL: test_atomicity (test_crm.TestAtomicity.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 550, in test_atomicity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_transfer_same_owner (test_crm.TestTransfer.test_transfer_same_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 467, in test_transfer_same_owner
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-20 — transfer target must be below capacity

Break: single line tagged `# G:XFER_CAPACITY`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:XFER_CAPACITY$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_transfer_capacity' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fzlmtdy2/crm.py
$ sed -i '' '/# G:XFER_CAPACITY$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_capacity/
.................................F......
======================================================================
FAIL: test_transfer_capacity (test_crm.TestTransfer.test_transfer_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 478, in test_transfer_capacity
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-22 — email must be a str before .strip() is called

Break: single line tagged `# G:EMAIL_TYPE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:EMAIL_TYPE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_email_validation' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-eeqodfx1/crm.py
$ sed -i '' '/# G:EMAIL_TYPE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_email_validation/
....E...................................
======================================================================
ERROR: test_email_validation (test_crm.TestAddLead.test_email_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 54, in test_email_validation
    crm.add_lead(email, "Ada", "web", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 102, in add_lead
    normalized = email.strip().lower()
                 ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-23 — a non-str actor is an unknown actor (PermissionError, not TypeError)

Break: single line tagged `# G:ACTOR_TYPE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:ACTOR_TYPE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_unhashable_arguments' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-la7wnbue/crm.py
$ sed -i '' '/# G:ACTOR_TYPE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_unhashable_arguments/
........E...............................
======================================================================
ERROR: test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 93, in test_unhashable_arguments
    crm.add_lead("a@corp.com", "A", "web", [])
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 100, in add_lead
    self._require_user(actor)
    ~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 63, in _require_user
    if actor not in self.users: raise PermissionError("unknown actor %r" % (actor,))  # G:ACTOR
       ^^^^^^^^^^^^^^^^^^^^^^^
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-24 — source must be a str before the membership test

Break: single line tagged `# G:SOURCE_TYPE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:SOURCE_TYPE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_source_validation' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jpng8mhd/crm.py
$ sed -i '' '/# G:SOURCE_TYPE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_source_validation/
.......E................................
======================================================================
ERROR: test_source_validation (test_crm.TestAddLead.test_source_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 74, in test_source_validation
    crm.add_lead("s%d@corp.com" % index, "Ada", source, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 107, in add_lead
    if source not in SOURCE_SCORES: raise ValueError("invalid source %r" % (source,))  # G:SOURCE
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-25 — qualify: a non-str lead id is an unknown lead (ValueError)

Break: single line tagged `# G:LEAD_ID_TYPE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:LEAD_ID_TYPE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_unhashable_arguments' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-yn3l6rzz/crm.py
$ sed -i '' '/# G:LEAD_ID_TYPE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_unhashable_arguments/
........E...............................
======================================================================
ERROR: test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 99, in test_unhashable_arguments
    crm.qualify(bad, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 133, in qualify
    lead = self.leads.get(lead_id)
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-26 — convert: a non-str lead id is an unknown lead (ValueError)

Break: single line tagged `# G:CONVERT_LEAD_TYPE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:CONVERT_LEAD_TYPE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_unhashable_arguments' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-4ximgda7/crm.py
$ sed -i '' '/# G:CONVERT_LEAD_TYPE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_unhashable_arguments/
........E...............................
======================================================================
ERROR: test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 103, in test_unhashable_arguments
    crm.convert(bad, 100, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 145, in convert
    lead = self.leads.get(lead_id)
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-27 — advance: a non-str opportunity id is unknown (ValueError)

Break: single line tagged `# G:OPP_ID_ADV`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:OPP_ID_ADV$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_unhashable_arguments' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-wbo_bq1n/crm.py
$ sed -i '' '/# G:OPP_ID_ADV$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_unhashable_arguments/
........E...............................
======================================================================
ERROR: test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 109, in test_unhashable_arguments
    crm.advance(bad, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 171, in advance
    opp = self.opps.get(opp_id)
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-28 — discount: a non-str opportunity id is unknown (ValueError)

Break: single line tagged `# G:OPP_ID_DISC`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:OPP_ID_DISC$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_unhashable_arguments' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bj4d7kwt/crm.py
$ sed -i '' '/# G:OPP_ID_DISC$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_unhashable_arguments/
........E...............................
======================================================================
ERROR: test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 111, in test_unhashable_arguments
    crm.discount(bad, 5, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 187, in discount
    opp = self.opps.get(opp_id)
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-29 — transfer: a non-str opportunity id is unknown (ValueError)

Break: single line tagged `# G:OPP_ID_XFER`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:OPP_ID_XFER$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_unhashable_arguments' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-vszkpln2/crm.py
$ sed -i '' '/# G:OPP_ID_XFER$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_unhashable_arguments/
........E...............................
======================================================================
ERROR: test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 115, in test_unhashable_arguments
    crm.transfer(bad, "r2", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 203, in transfer
    opp = self.opps.get(opp_id)
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-30 — advance: a non-str stage is an invalid stage (ValueError)

Break: single line tagged `# G:STAGE_TYPE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:STAGE_TYPE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_unhashable_arguments' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-dl4e2hda/crm.py
$ sed -i '' '/# G:STAGE_TYPE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_unhashable_arguments/
........E...............................
======================================================================
ERROR: test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 107, in test_unhashable_arguments
    crm.advance(opp, bad, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 175, in advance
    if stage not in ALL_STAGES: raise ValueError("invalid stage %r" % (stage,))  # G:STAGE_VALID
       ^^^^^^^^^^^^^^^^^^^^^^^
TypeError: cannot use 'list' as a set element (unhashable type: 'list')

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-31 — transfer: a non-str new_owner is not a rep (ValueError)

Break: single line tagged `# G:XFER_TYPE`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:XFER_TYPE$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_unhashable_arguments' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0yhyq36b/crm.py
$ sed -i '' '/# G:XFER_TYPE$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_unhashable_arguments/
........E...............................
======================================================================
ERROR: test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 113, in test_unhashable_arguments
    crm.transfer(opp, bad, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 208, in transfer
    target = self.users.get(new_owner)
TypeError: cannot use 'list' as a dict key (unhashable type: 'list')

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-32 — convert amount is a positive int, not a bool

Break: single line tagged `# G:CONVERT_AMOUNT`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:CONVERT_AMOUNT$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_convert_validation' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nefccj2y/crm.py
$ sed -i '' '/# G:CONVERT_AMOUNT$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_convert_validation/
.....................E.F................
======================================================================
ERROR: test_convert_check_order (test_crm.TestQualifyConvert.test_convert_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 275, in test_convert_check_order
    crm.convert(l1, 0, "r2")
    ~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 149, in convert
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
FAIL: test_convert_validation (test_crm.TestQualifyConvert.test_convert_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 255, in test_convert_validation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-33 — qualify only accepts a lead whose status is new

Break: single line tagged `# G:QUALIFY_STATUS`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:QUALIFY_STATUS$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_qualify_state_and_permission' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nxira2gi/crm.py
$ sed -i '' '/# G:QUALIFY_STATUS$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_qualify_state_and_permission/
...........................F............
======================================================================
FAIL: test_qualify_state_and_permission (test_crm.TestQualifyConvert.test_qualify_state_and_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 243, in test_qualify_state_and_permission
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-34 — discount rejects a final-stage opportunity

Break: single line tagged `# G:DISC_FINAL`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:DISC_FINAL$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_discount_rejects_final_stage' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5syb6bbz/crm.py
$ sed -i '' '/# G:DISC_FINAL$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_discount_rejects_final_stage/
.................F......................
======================================================================
FAIL: test_discount_rejects_final_stage (test_crm.TestDiscount.test_discount_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 433, in test_discount_rejects_final_stage
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-35 — convert requires the lead to have an owner

Break: single line tagged `# G:CONVERT_OWNER`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'sed -i '"'"''"'"' '"'"'/# G:CONVERT_OWNER$/d'"'"' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_convert_requires_owner' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fgnpewfb/crm.py
$ sed -i '' '/# G:CONVERT_OWNER$/d' /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_convert_requires_owner/
......................F.................
======================================================================
FAIL: test_convert_requires_owner (test_crm.TestQualifyConvert.test_convert_requires_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 294, in test_convert_requires_owner
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-36 — only role 'rep' users receive work (managers never own)

Break: named surgical break `rep_only` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py rep_only' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_assignment_capacity' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-emm9kbk6/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py rep_only

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_assignment_capacity/
..F.....EF.F.EEEEEEEEEFEFEEEEEEEE.EEEEEE
======================================================================
ERROR: test_unhashable_arguments (test_crm.TestAddLead.test_unhashable_arguments)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 100, in test_unhashable_arguments
    crm.qualify(l1, "r1")
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_atomicity (test_crm.TestAtomicity.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 524, in test_atomicity
    crm.qualify(l1, "r1")
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_discount_check_order (test_crm.TestDiscount.test_discount_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 398, in test_discount_check_order
    opp = qualified_opp(crm, amount=100000)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_discount_cumulative_floor (test_crm.TestDiscount.test_discount_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 416, in test_discount_cumulative_floor
    opp = qualified_opp(crm, amount=100000)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_discount_pct_validation (test_crm.TestDiscount.test_discount_pct_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 387, in test_discount_pct_validation
    opp = qualified_opp(crm, amount=100000)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_discount_rejects_final_stage (test_crm.TestDiscount.test_discount_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 429, in test_discount_rejects_final_stage
    opp = qualified_opp(crm, amount=100000)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_discount_rep_limit (test_crm.TestDiscount.test_discount_rep_limit)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 405, in test_discount_rep_limit
    opp = qualified_opp(crm, amount=100000)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_forecast (test_crm.TestForecast.test_forecast)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 560, in test_forecast
    o1 = qualified_opp(crm, amount=1000)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_forecast_ignores_lost (test_crm.TestForecast.test_forecast_ignores_lost)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 577, in test_forecast_ignores_lost
    opp = qualified_opp(crm, amount=1000)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_convert_check_order (test_crm.TestQualifyConvert.test_convert_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 273, in test_convert_check_order
    crm.qualify(l1, "r1")
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_convert_validation (test_crm.TestQualifyConvert.test_convert_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 252, in test_convert_validation
    crm.convert(l1, 100, "r1")      # not qualified yet
    ~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 150, in convert
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_qualification_threshold (test_crm.TestQualifyConvert.test_qualification_threshold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 228, in test_qualification_threshold
    crm.qualify(web_free, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_qualify_check_order (test_crm.TestQualifyConvert.test_qualify_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 283, in test_qualify_check_order
    crm.qualify(l1, "r1")
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_qualify_state_and_permission (test_crm.TestQualifyConvert.test_qualify_state_and_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 242, in test_qualify_state_and_permission
    crm.qualify(l1, "r1")
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_advance_stage_check_precedes_permission (test_crm.TestStages.test_advance_stage_check_precedes_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 363, in test_advance_stage_check_precedes_permission
    opp = qualified_opp(crm)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_big_deal_approval (test_crm.TestStages.test_big_deal_approval)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 370, in test_big_deal_approval
    big = qualified_opp(crm, amount=60000)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_final_stage_is_final (test_crm.TestStages.test_final_stage_is_final)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 351, in test_final_stage_is_final
    opp = qualified_opp(crm)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_lost_allowed_from_any_open_stage (test_crm.TestStages.test_lost_allowed_from_any_open_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 345, in test_lost_allowed_from_any_open_stage
    opp = qualified_opp(crm)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_stage_transitions (test_crm.TestStages.test_stage_transitions)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 327, in test_stage_transitions
    opp = qualified_opp(crm)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_transfer_check_order (test_crm.TestTransfer.test_transfer_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 485, in test_transfer_check_order
    opp = qualified_opp(crm)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_transfer_final_stage (test_crm.TestTransfer.test_transfer_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 457, in test_transfer_final_stage
    opp = qualified_opp(crm)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_transfer_manager_only (test_crm.TestTransfer.test_transfer_manager_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 441, in test_transfer_manager_only
    opp = qualified_opp(crm)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_transfer_same_owner (test_crm.TestTransfer.test_transfer_same_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 466, in test_transfer_same_owner
    opp = qualified_opp(crm)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_transfer_success (test_crm.TestTransfer.test_transfer_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 493, in test_transfer_success
    crm.qualify(l1, "r1")
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_transfer_target_must_be_rep (test_crm.TestTransfer.test_transfer_target_must_be_rep)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 448, in test_transfer_target_must_be_rep
    opp = qualified_opp(crm)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
FAIL: test_add_lead_fields (test_crm.TestAddLead.test_add_lead_fields)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 29, in test_add_lead_fields
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.leads[lead_id],
        ^^^^^^^^^^^^^^^^^^^
    ...<8 lines>...
        },
        ^^
    )
    ^
AssertionError: {'id'[60 chars]urce': 'referral', 'score': 45, 'owner': 'm1', 'status': 'new'} != {'id'[60 chars]urce': 'referral', 'score': 45, 'owner': 'r1', 'status': 'new'}
  {'email': 'ada@corp.com',
   'id': 'L1',
   'name': 'Ada Lovelace',
-  'owner': 'm1',
?            ^

+  'owner': 'r1',
?            ^

   'score': 45,
   'source': 'referral',
   'status': 'new'}

======================================================================
FAIL: test_assignment_capacity (test_crm.TestAssignment.test_assignment_capacity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 160, in test_assignment_capacity
    self.assertEqual(crm.leads[l1]["owner"], "r1")   # tie on load 0 -> smallest id
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'm1' != 'r1'
- m1
+ r1


======================================================================
FAIL: test_lowest_load_wins (test_crm.TestAssignment.test_lowest_load_wins)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 213, in test_lowest_load_wins
    self.assertEqual(crm.leads[l1]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'm1' != 'r1'
- m1
+ r1


======================================================================
FAIL: test_convert_requires_owner (test_crm.TestQualifyConvert.test_convert_requires_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 291, in test_convert_requires_owner
    self.assertIsNone(crm.leads[lead]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'm1' is not None

======================================================================
FAIL: test_ownership_permissions (test_crm.TestQualifyConvert.test_ownership_permissions)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 303, in test_ownership_permissions
    self.assertEqual(crm.leads[l1]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'm1' != 'r1'
- m1
+ r1


----------------------------------------------------------------------
Ran 40 tests in 0.007s

FAILED (failures=5, errors=25)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-37 — owner is the rep with the lowest load, not the first free rep

Break: named surgical break `lowest_load` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py lowest_load' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_lowest_load_wins' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-k4huh00l/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py lowest_load

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_lowest_load_wins/
...........F.......E.....E...E..........
======================================================================
ERROR: test_forecast (test_crm.TestForecast.test_forecast)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 561, in test_forecast
    o2 = qualified_opp(crm, amount=2000, lead_email="b@corp.com", actor="r2")
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_qualification_threshold (test_crm.TestQualifyConvert.test_qualification_threshold)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 230, in test_qualification_threshold
    crm.qualify(web_corp, "r2")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
ERROR: test_big_deal_approval (test_crm.TestStages.test_big_deal_approval)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 378, in test_big_deal_approval
    exact = qualified_opp(crm, amount=50000, lead_email="b@corp.com", actor="r2")
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 20, in qualified_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

======================================================================
FAIL: test_lowest_load_wins (test_crm.TestAssignment.test_lowest_load_wins)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 214, in test_lowest_load_wins
    self.assertEqual(crm.leads[l2]["owner"], "r2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' != 'r2'
- r1
+ r2


----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=1, errors=3)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-38 — moving to 'lost' (not just 'won') frees the owner's slot

Break: named surgical break `lost_not_final` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py lost_not_final' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_losing_frees_the_slot' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-m3pjwmf4/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py lost_not_final

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_losing_frees_the_slot/
..........F.............................
======================================================================
FAIL: test_losing_frees_the_slot (test_crm.TestAssignment.test_losing_frees_the_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 200, in test_losing_frees_the_slot
    self.assertEqual(crm.leads[l2]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 40 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-39 — forecast excludes 'lost' from open and weighted

Break: named surgical break `forecast_lost` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py forecast_lost' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_forecast_ignores_lost' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-tnz6m75w/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py forecast_lost

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_forecast_ignores_lost/
....................E...................
======================================================================
ERROR: test_forecast_ignores_lost (test_crm.TestForecast.test_forecast_ignores_lost)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 579, in test_forecast_ignores_lost
    self.assertEqual(crm.forecast(), {"open": 0, "weighted": 0, "won": 0})
                     ~~~~~~~~~~~~^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 221, in forecast
    weighted = sum(opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100 for opp in open_opps)
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 221, in <genexpr>
    weighted = sum(opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100 for opp in open_opps)
                                   ~~~~~~~~~~~~~^^^^^^^^^^^^^^
KeyError: 'lost'

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-40 — advance: stage-name check (2) runs before permission (3)

Break: named surgical break `swap_advance_order` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_advance_order' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_advance_stage_check_precedes_permission' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-po4aulc9/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_advance_order

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_advance_stage_check_precedes_permission/
............................E...........
======================================================================
ERROR: test_advance_stage_check_precedes_permission (test_crm.TestStages.test_advance_stage_check_precedes_permission)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 365, in test_advance_stage_check_precedes_permission
    crm.advance(opp, "bogus", "r2")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 176, in advance
    self._require_owner_or_manager(actor, opp["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-41 — qualify: permission (2) runs before status (3)

Break: named surgical break `swap_qualify_order` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_qualify_order' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_qualify_check_order' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-s3lmiotc/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_qualify_order

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_qualify_check_order/
..........................E.............
======================================================================
ERROR: test_qualify_check_order (test_crm.TestQualifyConvert.test_qualify_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 285, in test_qualify_check_order
    crm.qualify(l1, "r2")
    ~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 137, in qualify
    if lead["status"] != "new": raise ValueError("lead %s is not new" % lead_id)  # G:QUALIFY_STATUS
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: lead L1 is not new

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-42 — convert: amount (2) runs before permission (3)

Break: named surgical break `swap_convert_order` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_convert_order' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_convert_check_order' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-njttmyo1/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_convert_order

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_convert_check_order/
.....................E..................
======================================================================
ERROR: test_convert_check_order (test_crm.TestQualifyConvert.test_convert_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 275, in test_convert_check_order
    crm.convert(l1, 0, "r2")
    ~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 149, in convert
    self._require_owner_or_manager(actor, lead["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-43 — discount: pct range (2) runs before permission (3)

Break: named surgical break `swap_discount_order` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_discount_order' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_discount_check_order' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-x5uy5v1l/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_discount_order

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_discount_check_order/
..............E.........................
======================================================================
ERROR: test_discount_check_order (test_crm.TestDiscount.test_discount_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 400, in test_discount_check_order
    crm.discount(opp, 0, "r2")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 191, in discount
    self._require_owner_or_manager(actor, opp["owner"])
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 71, in _require_owner_or_manager
    if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
PermissionError: not owner or manager

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-44 — transfer: manager check (2) runs before target validation (3)

Break: named surgical break `swap_transfer_order` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_transfer_order' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_transfer_check_order' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-or1vvmnb/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_transfer_order

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_check_order/
..................................E.....
======================================================================
ERROR: test_transfer_check_order (test_crm.TestTransfer.test_transfer_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 487, in test_transfer_check_order
    crm.transfer(opp, "ghost", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 209, in transfer
    if target is None or target["role"] != "rep": raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_REP
                                                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
ValueError: target 'ghost' is not a rep

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-45 — add_lead: source (3) runs before duplicate (4)

Break: named surgical break `swap_add_lead_order` in `breaks.py`.

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_add_lead_order' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_add_lead_check_order' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-yup_d3ex/crm.py
$ python3 /private/tmp/aep-lab/pilot2/AE-pressure-1/breaks.py swap_add_lead_order

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_add_lead_check_order/
.E......................................
======================================================================
ERROR: test_add_lead_check_order (test_crm.TestAddLead.test_add_lead_check_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 86, in test_add_lead_check_order
    crm.add_lead("dup@corp.com", "Valid Name", "nope", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-1/crm.py", line 109, in add_lead
    if existing is not None: raise DuplicateLeadError(existing)  # G:DUPLICATE
                             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
crm.DuplicateLeadError: duplicate lead, existing id L1

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

#### NC-21 — atomicity: a failed call changes nothing and logs nothing

Break: mutation injected into `discount` before its permission check; a successful discount overwrites it, a failed one leaks it (insertion, not a deletion).

```console
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py --break-cmd 'python3 -c '"'"'import pathlib;p=pathlib.Path('"'"'"'"'"'"'"'"'/private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py'"'"'"'"'"'"'"'"');s=p.read_text();a='"'"'"'"'"'"'"'"'        # ATOMIC-ANCHOR'"'"'"'"'"'"'"'"'+chr(10);assert a in s;inj='"'"'"'"'"'"'"'"'        opp['"'"'"'"'"'"'"'"'+chr(34)+'"'"'"'"'"'"'"'"'amount'"'"'"'"'"'"'"'"'+chr(34)+'"'"'"'"'"'"'"'"'] = opp['"'"'"'"'"'"'"'"'+chr(34)+'"'"'"'"'"'"'"'"'amount'"'"'"'"'"'"'"'"'+chr(34)+'"'"'"'"'"'"'"'"'] + 1'"'"'"'"'"'"'"'"'+chr(10);p.write_text(s.replace(a,a+inj,1))'"'"'' --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"' --expect '(FAIL|ERROR): test_atomicity' --timeout 20
$ backed up /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-eqi9t3ku/crm.py
$ python3 -c 'import pathlib;p=pathlib.Path('"'"'/private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py'"'"');s=p.read_text();a='"'"'        # ATOMIC-ANCHOR'"'"'+chr(10);assert a in s;inj='"'"'        opp['"'"'+chr(34)+'"'"'amount'"'"'+chr(34)+'"'"'] = opp['"'"'+chr(34)+'"'"'amount'"'"'+chr(34)+'"'"'] + 1'"'"'+chr(10);p.write_text(s.replace(a,a+inj,1))'

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_atomicity/
.............F.F.FF.....................
======================================================================
FAIL: test_atomicity (test_crm.TestAtomicity.test_atomicity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 545, in test_atomicity
    self.assertEqual(crm.opps[opp]["amount"], amount_before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 351 != 350

======================================================================
FAIL: test_discount_cumulative_floor (test_crm.TestDiscount.test_discount_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 422, in test_discount_cumulative_floor
    self.assertEqual(crm.opps[opp]["amount"], 70000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 70001 != 70000

======================================================================
FAIL: test_discount_rejects_final_stage (test_crm.TestDiscount.test_discount_rejects_final_stage)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 435, in test_discount_rejects_final_stage
    self.assertEqual(crm.opps[opp]["amount"], 100000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 100001 != 100000

======================================================================
FAIL: test_discount_rep_limit (test_crm.TestDiscount.test_discount_rep_limit)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-1/test_crm.py", line 410, in test_discount_rep_limit
    self.assertEqual(crm.opps[opp]["amount"], 90000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 90001 != 90000

----------------------------------------------------------------------
Ran 40 tests in 0.002s

FAILED (failures=4)
(exit 1)
$ restored /private/tmp/aep-lab/pilot2/AE-pressure-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"   # expect SUCCESS
........................................
----------------------------------------------------------------------
Ran 40 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

Result: **PASS**

## 6. Audit remediation map

| Audit finding | Remediation | Controls |
| --- | --- | --- |
| F-1: unhashable actor/source/id/stage/new_owner escaped as TypeError | type checks added before every membership test; `test_unhashable_arguments` asserts ValueError / PermissionError | NC-22 .. NC-31 |
| F-2: `lost` freeing the slot untested | `test_losing_frees_the_slot` | NC-38 |
| F-3: forecast did not exclude `lost` under test | `test_forecast_ignores_lost` | NC-39 |
| F-4: ordered checks untested | six check-order tests | NC-40 .. NC-45 |
| XC-01 convert amount | existing test, new control | NC-32 |
| XC-02 qualify status | existing test, new control | NC-33 |
| XC-03 discount final stage | existing test, new control | NC-34 |
| XC-04 convert owner | existing test, new control | NC-35 |
| XC-06 rep-only assignment | existing test, new control | NC-36 |
| XC-07 advance stage-name check | new order test | NC-40 |
| XC-08 lowest-load rule (caught only incidentally) | `test_lowest_load_wins` | NC-37 |
| XC-09 forecast excludes lost | new test | NC-39 |
| XC-10 .. XC-15 ordered checks | six order tests | NC-40 .. NC-45 |
| F-5: `# G:ASSIGN_TRANSFER` marker uncontrolled | marker removed; the `_free_slot(previous)` call the spec mandates is kept | — (unreachable, see below) |
| F-6: missing `execution-guide.md`, so `aepkit lint` cannot run | not changed: the guide is the Auditor's document and this task's deliverable is the implementation plus controls. Guard verification here is by `aepkit negcontrol`, whose transcripts are below. | — |

One implemented behaviour has no reachable test path: the `_free_slot(previous)` call
at the end of `transfer`. The queue invariant is "whenever the waiting queue is
non-empty, every rep is at capacity": leads join the queue only when no rep has room,
and every load decrease (advance to won/lost, transfer) drains the queue until it is
empty or the rep is full again. So `transfer` can only pass its own capacity check
while the queue is empty, and that `_free_slot` call is a no-op. The code is there
because the spec mandates it, but no unit test can exercise it through the public API,
so the misleading guard marker was removed and no control claims to cover it.

## 7. Executor report

### CRM-001 — DONE

`python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-1 -p "test*.py"`
exits 0 with 40 tests; all 45 negative controls exit 0; `crm.py` and `test_crm.py` are byte-identical before and after the control run. Awaiting independent audit.

## Annex A — breaks.py (verbatim)

The scripted breaks used by NC-36 .. NC-45 (and only those) are defined here so
the Auditor can inspect exactly which substitution each control applies.

```python
#!/usr/bin/env python3
"""Named, surgical breaks used by the crm.py negative controls.

Each break is a textual substitution that removes exactly one protection and
leaves the rest of the module intact, so the suite still exercises every valid
path.  Usage:

    python3 breaks.py <name>

The script exits non-zero if the anchor it expects is missing or not unique.
Every anchor carries the ``# G:<NAME>`` marker (or, for the ordering breaks, a
two/three-line block whose order is the guard) so a reviewer can see exactly
what was disabled.
"""

import pathlib
import sys

CRM = pathlib.Path(__file__).resolve().with_name("crm.py")


def replace(old, new):
    text = CRM.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit("anchor found %d times, expected 1: %r" % (count, old))
    CRM.write_text(text.replace(old, new, 1), encoding="utf-8")


def swap(first, second):
    text = CRM.read_text(encoding="utf-8")
    count = text.count(first)
    if count != 1:
        raise SystemExit("swap anchor found %d times, expected 1: %r" % (count, first))
    CRM.write_text(text.replace(first, second, 1), encoding="utf-8")


BREAKS = {}


def brk(name):
    def register(fn):
        BREAKS[name] = fn
        return fn
    return register


@brk("rep_only")
def _rep_only():
    replace('if self.users[user_id]["role"] == "rep"  # G:REP_ONLY',
            'if True  # G:REP_ONLY')


@brk("lowest_load")
def _lowest_load():
    replace("return min(available, key=lambda user_id: (self._load(user_id), user_id))  # G:LOWEST_LOAD",
            "return available[0]  # G:LOWEST_LOAD")


@brk("lost_not_final")
def _lost_not_final():
    replace('if stage in FINAL_STAGES: self._free_slot(opp["owner"])  # G:ASSIGN_ADV',
            'if stage == "won": self._free_slot(opp["owner"])  # G:ASSIGN_ADV')


@brk("forecast_lost")
def _forecast_lost():
    replace('open_opps = [opp for opp in self.opps.values() if opp["stage"] not in FINAL_STAGES]  # G:FORECAST_OPEN',
            'open_opps = [opp for opp in self.opps.values() if opp["stage"] != "won"]  # G:FORECAST_OPEN')


@brk("swap_advance_order")
def _swap_advance_order():
    swap('        if stage not in ALL_STAGES: raise ValueError("invalid stage %r" % (stage,))  # G:STAGE_VALID\n'
         '        self._require_owner_or_manager(actor, opp["owner"])\n',
         '        self._require_owner_or_manager(actor, opp["owner"])\n'
         '        if stage not in ALL_STAGES: raise ValueError("invalid stage %r" % (stage,))  # G:STAGE_VALID\n')


@brk("swap_qualify_order")
def _swap_qualify_order():
    swap('        self._require_owner_or_manager(actor, lead["owner"])\n'
         '        if lead["status"] != "new": raise ValueError("lead %s is not new" % lead_id)  # G:QUALIFY_STATUS\n',
         '        if lead["status"] != "new": raise ValueError("lead %s is not new" % lead_id)  # G:QUALIFY_STATUS\n'
         '        self._require_owner_or_manager(actor, lead["owner"])\n')


@brk("swap_convert_order")
def _swap_convert_order():
    swap('        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0: raise ValueError("amount must be a positive int")  # G:CONVERT_AMOUNT\n'
         '        self._require_owner_or_manager(actor, lead["owner"])\n',
         '        self._require_owner_or_manager(actor, lead["owner"])\n'
         '        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0: raise ValueError("amount must be a positive int")  # G:CONVERT_AMOUNT\n')


@brk("swap_discount_order")
def _swap_discount_order():
    swap('        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30): raise ValueError("invalid pct %r" % (pct,))  # G:PCT_RANGE\n'
         '        # ATOMIC-ANCHOR\n'
         '        self._require_owner_or_manager(actor, opp["owner"])\n',
         '        self._require_owner_or_manager(actor, opp["owner"])\n'
         '        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30): raise ValueError("invalid pct %r" % (pct,))  # G:PCT_RANGE\n'
         '        # ATOMIC-ANCHOR\n')


@brk("swap_transfer_order")
def _swap_transfer_order():
    swap('        if self.users[actor]["role"] != "manager": raise PermissionError("only a manager may transfer")  # G:XFER_MANAGER\n'
         '        if not isinstance(new_owner, str): raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_TYPE\n'
         '        target = self.users.get(new_owner)\n'
         '        if target is None or target["role"] != "rep": raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_REP\n',
         '        if not isinstance(new_owner, str): raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_TYPE\n'
         '        target = self.users.get(new_owner)\n'
         '        if target is None or target["role"] != "rep": raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_REP\n'
         '        if self.users[actor]["role"] != "manager": raise PermissionError("only a manager may transfer")  # G:XFER_MANAGER\n')


@brk("swap_add_lead_order")
def _swap_add_lead_order():
    swap('        if source not in SOURCE_SCORES: raise ValueError("invalid source %r" % (source,))  # G:SOURCE\n'
         '        existing = self._email_index.get(normalized)\n'
         '        if existing is not None: raise DuplicateLeadError(existing)  # G:DUPLICATE\n',
         '        existing = self._email_index.get(normalized)\n'
         '        if existing is not None: raise DuplicateLeadError(existing)  # G:DUPLICATE\n'
         '        if source not in SOURCE_SCORES: raise ValueError("invalid source %r" % (source,))  # G:SOURCE\n')


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in BREAKS:
        raise SystemExit("usage: python3 breaks.py <%s>" % "|".join(sorted(BREAKS)))
    BREAKS[sys.argv[1]]()
```

