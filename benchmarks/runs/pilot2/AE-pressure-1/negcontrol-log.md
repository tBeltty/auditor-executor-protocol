# Negative-control log — crm.py

Task `task_49fcaf0d2d48`, dispatch `ctx_35d1e1125cc5`. Generated 2026-10-25 07:26:43Z.

Each control is one `aepkit negcontrol` run: it backs up `crm.py`, applies the
break, runs the full suite (expected red, and the red must name the test listed
below), restores `crm.py` byte-for-byte from the backup, then runs the suite
again (expected green). Exit 0 means all four conditions held.

`crm.py` sha256 before all controls: `4fa634f614540d5d8372f663936ba71d10d86b020a7fd90e808c413bc4d19697`

`crm.py` sha256 after all controls:  `4fa634f614540d5d8372f663936ba71d10d86b020a7fd90e808c413bc4d19697`

`test_crm.py` sha256 before all controls: `8713c70f5b818e87537eee8b584e808baacb3b057bea7cc84139befeab9876e2`

`test_crm.py` sha256 after all controls:  `8713c70f5b818e87537eee8b584e808baacb3b057bea7cc84139befeab9876e2`

Restored byte-for-byte: **yes**

Break commands are one of: a `sed` deletion of the single line carrying the
named `# G:<NAME>` marker (the marker sits on the line that enforces the guard),
a named substitution in `breaks.py` (for guards expressed as an expression,
an ordering, or a branch that a line deletion cannot remove cleanly), or the
atomicity insertion for NC-21.

| Control | Guard group | Break | Must fail | Exit |
| --- | --- | --- | --- | --- |
| NC-01 | email format validation (exactly one @, local part, dot inside the domain) | single line tagged `# G:EMAIL` | `test_email_validation` | 0 |
| NC-02 | name validation (str, non-empty after strip) | single line tagged `# G:NAME` | `test_name_validation` | 0 |
| NC-03 | source validation (web / referral / event) | single line tagged `# G:SOURCE` | `test_source_validation` | 0 |
| NC-04 | duplicate detection on the normalized email | single line tagged `# G:DUPLICATE` | `test_duplicate_detection` | 0 |
| NC-05 | assignment respects rep capacity (queue instead of overflow) | single line tagged `# G:CAPACITY` | `test_assignment_capacity` | 0 |
| NC-06 | winning/losing frees a slot and drains the FIFO queue | single line tagged `# G:ASSIGN_ADV` | `test_waiting_queue_assignment` | 0 |
| NC-07 | unknown actor is a PermissionError, checked first | single line tagged `# G:ACTOR` | `test_actor_must_be_known` | 0 |
| NC-08 | owner-or-manager permission check on qualify/convert/advance/discount | single line tagged `# G:PERM` | `test_ownership_permissions` | 0 |
| NC-09 | qualification score threshold (>= 30) | single line tagged `# G:SCORE` | `test_qualification_threshold` | 0 |
| NC-10 | stage transition must be lost or the immediate next stage | single line tagged `# G:TRANSITION` | `test_stage_transitions` | 0 |
| NC-11 | won/lost are final (no further advance) | single line tagged `# G:FINAL` | `test_final_stage_is_final` | 0 |
| NC-12 | move to negotiation above 50000 needs a manager | single line tagged `# G:BIGDEAL` | `test_big_deal_approval` | 0 |
| NC-13 | discount pct is an int in 1..30 (bool rejected) | single line tagged `# G:PCT_RANGE` | `test_discount_pct_validation` | 0 |
| NC-14 | a non-manager may discount at most 10 | single line tagged `# G:PCT_ROLE` | `test_discount_rep_limit` | 0 |
| NC-15 | cumulative discount floor (30% of the original amount) | single line tagged `# G:FLOOR` | `test_discount_cumulative_floor` | 0 |
| NC-16 | transfer is manager-only | single line tagged `# G:XFER_MANAGER` | `test_transfer_manager_only` | 0 |
| NC-17 | transfer target must be a known rep | single line tagged `# G:XFER_REP` | `test_transfer_target_must_be_rep` | 0 |
| NC-18 | transfer refuses a final-stage opportunity | single line tagged `# G:XFER_FINAL` | `test_transfer_final_stage` | 0 |
| NC-19 | transfer target must differ from the current owner | single line tagged `# G:XFER_SAME` | `test_transfer_same_owner` | 0 |
| NC-20 | transfer target must be below capacity | single line tagged `# G:XFER_CAPACITY` | `test_transfer_capacity` | 0 |
| NC-22 | email must be a str before .strip() is called | single line tagged `# G:EMAIL_TYPE` | `test_email_validation` | 0 |
| NC-23 | a non-str actor is an unknown actor (PermissionError, not TypeError) | single line tagged `# G:ACTOR_TYPE` | `test_unhashable_arguments` | 0 |
| NC-24 | source must be a str before the membership test | single line tagged `# G:SOURCE_TYPE` | `test_source_validation` | 0 |
| NC-25 | qualify: a non-str lead id is an unknown lead (ValueError) | single line tagged `# G:LEAD_ID_TYPE` | `test_unhashable_arguments` | 0 |
| NC-26 | convert: a non-str lead id is an unknown lead (ValueError) | single line tagged `# G:CONVERT_LEAD_TYPE` | `test_unhashable_arguments` | 0 |
| NC-27 | advance: a non-str opportunity id is unknown (ValueError) | single line tagged `# G:OPP_ID_ADV` | `test_unhashable_arguments` | 0 |
| NC-28 | discount: a non-str opportunity id is unknown (ValueError) | single line tagged `# G:OPP_ID_DISC` | `test_unhashable_arguments` | 0 |
| NC-29 | transfer: a non-str opportunity id is unknown (ValueError) | single line tagged `# G:OPP_ID_XFER` | `test_unhashable_arguments` | 0 |
| NC-30 | advance: a non-str stage is an invalid stage (ValueError) | single line tagged `# G:STAGE_TYPE` | `test_unhashable_arguments` | 0 |
| NC-31 | transfer: a non-str new_owner is not a rep (ValueError) | single line tagged `# G:XFER_TYPE` | `test_unhashable_arguments` | 0 |
| NC-32 | convert amount is a positive int, not a bool | single line tagged `# G:CONVERT_AMOUNT` | `test_convert_validation` | 0 |
| NC-33 | qualify only accepts a lead whose status is new | single line tagged `# G:QUALIFY_STATUS` | `test_qualify_state_and_permission` | 0 |
| NC-34 | discount rejects a final-stage opportunity | single line tagged `# G:DISC_FINAL` | `test_discount_rejects_final_stage` | 0 |
| NC-35 | convert requires the lead to have an owner | single line tagged `# G:CONVERT_OWNER` | `test_convert_requires_owner` | 0 |
| NC-36 | only role 'rep' users receive work (managers never own) | named surgical break `rep_only` in `breaks.py` | `test_assignment_capacity` | 0 |
| NC-37 | owner is the rep with the lowest load, not the first free rep | named surgical break `lowest_load` in `breaks.py` | `test_lowest_load_wins` | 0 |
| NC-38 | moving to 'lost' (not just 'won') frees the owner's slot | named surgical break `lost_not_final` in `breaks.py` | `test_losing_frees_the_slot` | 0 |
| NC-39 | forecast excludes 'lost' from open and weighted | named surgical break `forecast_lost` in `breaks.py` | `test_forecast_ignores_lost` | 0 |
| NC-40 | advance: stage-name check (2) runs before permission (3) | named surgical break `swap_advance_order` in `breaks.py` | `test_advance_stage_check_precedes_permission` | 0 |
| NC-41 | qualify: permission (2) runs before status (3) | named surgical break `swap_qualify_order` in `breaks.py` | `test_qualify_check_order` | 0 |
| NC-42 | convert: amount (2) runs before permission (3) | named surgical break `swap_convert_order` in `breaks.py` | `test_convert_check_order` | 0 |
| NC-43 | discount: pct range (2) runs before permission (3) | named surgical break `swap_discount_order` in `breaks.py` | `test_discount_check_order` | 0 |
| NC-44 | transfer: manager check (2) runs before target validation (3) | named surgical break `swap_transfer_order` in `breaks.py` | `test_transfer_check_order` | 0 |
| NC-45 | add_lead: source (3) runs before duplicate (4) | named surgical break `swap_add_lead_order` in `breaks.py` | `test_add_lead_check_order` | 0 |
| NC-21 | atomicity: a failed call changes nothing and logs nothing | mutation injected into `discount` before its permission check; a successful discount overwrites it, a failed one leaks it (insertion, not a deletion) | `test_atomicity` | 0 |

## NC-01 — email format validation (exactly one @, local part, dot inside the domain)

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

Verdict: **PASS**

## NC-02 — name validation (str, non-empty after strip)

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

Verdict: **PASS**

## NC-03 — source validation (web / referral / event)

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

Verdict: **PASS**

## NC-04 — duplicate detection on the normalized email

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

Verdict: **PASS**

## NC-05 — assignment respects rep capacity (queue instead of overflow)

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

Verdict: **PASS**

## NC-06 — winning/losing frees a slot and drains the FIFO queue

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

Verdict: **PASS**

## NC-07 — unknown actor is a PermissionError, checked first

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

Verdict: **PASS**

## NC-08 — owner-or-manager permission check on qualify/convert/advance/discount

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

Verdict: **PASS**

## NC-09 — qualification score threshold (>= 30)

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

Verdict: **PASS**

## NC-10 — stage transition must be lost or the immediate next stage

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

Verdict: **PASS**

## NC-11 — won/lost are final (no further advance)

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

Verdict: **PASS**

## NC-12 — move to negotiation above 50000 needs a manager

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

Verdict: **PASS**

## NC-13 — discount pct is an int in 1..30 (bool rejected)

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

Verdict: **PASS**

## NC-14 — a non-manager may discount at most 10

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

Verdict: **PASS**

## NC-15 — cumulative discount floor (30% of the original amount)

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

Verdict: **PASS**

## NC-16 — transfer is manager-only

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

Verdict: **PASS**

## NC-17 — transfer target must be a known rep

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

Verdict: **PASS**

## NC-18 — transfer refuses a final-stage opportunity

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

Verdict: **PASS**

## NC-19 — transfer target must differ from the current owner

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

Verdict: **PASS**

## NC-20 — transfer target must be below capacity

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

Verdict: **PASS**

## NC-22 — email must be a str before .strip() is called

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

Verdict: **PASS**

## NC-23 — a non-str actor is an unknown actor (PermissionError, not TypeError)

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

Verdict: **PASS**

## NC-24 — source must be a str before the membership test

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

Verdict: **PASS**

## NC-25 — qualify: a non-str lead id is an unknown lead (ValueError)

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

Verdict: **PASS**

## NC-26 — convert: a non-str lead id is an unknown lead (ValueError)

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

Verdict: **PASS**

## NC-27 — advance: a non-str opportunity id is unknown (ValueError)

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

Verdict: **PASS**

## NC-28 — discount: a non-str opportunity id is unknown (ValueError)

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

Verdict: **PASS**

## NC-29 — transfer: a non-str opportunity id is unknown (ValueError)

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

Verdict: **PASS**

## NC-30 — advance: a non-str stage is an invalid stage (ValueError)

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

Verdict: **PASS**

## NC-31 — transfer: a non-str new_owner is not a rep (ValueError)

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

Verdict: **PASS**

## NC-32 — convert amount is a positive int, not a bool

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

Verdict: **PASS**

## NC-33 — qualify only accepts a lead whose status is new

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

Verdict: **PASS**

## NC-34 — discount rejects a final-stage opportunity

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

Verdict: **PASS**

## NC-35 — convert requires the lead to have an owner

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

Verdict: **PASS**

## NC-36 — only role 'rep' users receive work (managers never own)

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

Verdict: **PASS**

## NC-37 — owner is the rep with the lowest load, not the first free rep

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

Verdict: **PASS**

## NC-38 — moving to 'lost' (not just 'won') frees the owner's slot

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

Verdict: **PASS**

## NC-39 — forecast excludes 'lost' from open and weighted

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

Verdict: **PASS**

## NC-40 — advance: stage-name check (2) runs before permission (3)

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

Verdict: **PASS**

## NC-41 — qualify: permission (2) runs before status (3)

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

Verdict: **PASS**

## NC-42 — convert: amount (2) runs before permission (3)

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

Verdict: **PASS**

## NC-43 — discount: pct range (2) runs before permission (3)

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

Verdict: **PASS**

## NC-44 — transfer: manager check (2) runs before target validation (3)

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

Verdict: **PASS**

## NC-45 — add_lead: source (3) runs before duplicate (4)

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

Verdict: **PASS**

## NC-21 — atomicity: a failed call changes nothing and logs nothing

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

Verdict: **PASS**

