# Negative controls — crm.py

Each control backs up crm.py, removes exactly one guard, runs the suite (it must
fail with the expected marker), restores the file and reruns the suite (it must pass).

## email validation

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py email" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "EMAIL_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-2q2s68bq/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py email
broke guard: email
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /EMAIL_GUARD/
.................................F...
======================================================================
FAIL: test_invalid_email_rejected (test_validation.ValidationTests.test_invalid_email_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 9, in expect_error
    fn(*args, **kwargs)
    ~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/crm.py", line 161, in add_lead
    domain = norm.rsplit("@", 1)[1]
             ~~~~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_validation.py", line 40, in test_invalid_email_rejected
    self.expect_error("EMAIL_GUARD", ValueError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      self.crm.add_lead, bad, "N", "web", "r1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 13, in expect_error
    self.fail("%s: expected %s, got %s(%s)"
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              % (tag, exc_type.__name__, type(err).__name__, err))
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: EMAIL_GUARD: expected ValueError, got IndexError(list index out of range)

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## name validation

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py name" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "NAME_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-kbkkq389/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py name
broke guard: name
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /NAME_GUARD/
..................................F..
======================================================================
FAIL: test_invalid_name_rejected (test_validation.ValidationTests.test_invalid_name_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_validation.py", line 48, in test_invalid_name_rejected
    self.expect_error("NAME_GUARD", ValueError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
                      self.crm.add_lead, "a@x.com", "   ", "web", "r1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: NAME_GUARD: expected ValueError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## source validation

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py source" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "SOURCE_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-u3ud5aya/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py source
broke guard: source
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /SOURCE_GUARD/
...................................F.
======================================================================
FAIL: test_invalid_source_rejected (test_validation.ValidationTests.test_invalid_source_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 9, in expect_error
    fn(*args, **kwargs)
    ~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/crm.py", line 171, in add_lead
    score = SOURCE_SCORES[source]
            ~~~~~~~~~~~~~^^^^^^^^
KeyError: 'podcast'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_validation.py", line 55, in test_invalid_source_rejected
    self.expect_error("SOURCE_GUARD", ValueError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      self.crm.add_lead, "a@x.com", "A", "podcast", "r1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 13, in expect_error
    self.fail("%s: expected %s, got %s(%s)"
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              % (tag, exc_type.__name__, type(err).__name__, err))
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: SOURCE_GUARD: expected ValueError, got KeyError('podcast')

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## duplicate detection

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py duplicate" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "DUPLICATE_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-atq3x116/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py duplicate
broke guard: duplicate
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /DUPLICATE_GUARD/
.....F.......F.......................
======================================================================
FAIL: test_failed_add_lead_does_not_consume_ids (test_atomicity.AtomicityTests.test_failed_add_lead_does_not_consume_ids)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_atomicity.py", line 44, in test_failed_add_lead_does_not_consume_ids
    self.expect_error("ATOMIC_STATE_GUARD", DuplicateLeadError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      self.crm.add_lead, "a@corp.com", "A", "web", "r1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ATOMIC_STATE_GUARD: expected DuplicateLeadError, nothing raised

======================================================================
FAIL: test_duplicate_email_rejected (test_guards.GuardTests.test_duplicate_email_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 62, in test_duplicate_email_rejected
    self.fail("DUPLICATE_GUARD: duplicate email must raise DuplicateLeadError")
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: DUPLICATE_GUARD: duplicate email must raise DuplicateLeadError

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## rep assignment capacity

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py capacity" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "CAPACITY_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-qero0ree/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py capacity
broke guard: capacity
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /CAPACITY_GUARD/
F..F.................................
======================================================================
FAIL: test_capacity_is_respected_and_queue_is_fifo (test_assignment.AssignmentTests.test_capacity_is_respected_and_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_assignment.py", line 32, in test_capacity_is_respected_and_queue_is_fifo
    self.assertIsNone(crm.leads[second]["owner"],
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      "CAPACITY_GUARD: a rep at capacity must not take more leads")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None : CAPACITY_GUARD: a rep at capacity must not take more leads

======================================================================
FAIL: test_queue_released_when_slot_frees (test_assignment.AssignmentTests.test_queue_released_when_slot_frees)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_assignment.py", line 41, in test_queue_released_when_slot_frees
    self.assertEqual(crm.waiting, [second, third])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != ['L2', 'L3']

Second list contains 2 additional elements.
First extra element 0:
'L2'

- []
+ ['L2', 'L3']

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## waiting queue release

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py queue" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "QUEUE_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-abnttpd8/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py queue
broke guard: queue
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /QUEUE_GUARD/
...F.................................
======================================================================
FAIL: test_queue_released_when_slot_frees (test_assignment.AssignmentTests.test_queue_released_when_slot_frees)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_assignment.py", line 47, in test_queue_released_when_slot_frees
    self.assertEqual(crm.leads[second]["owner"], "r1",
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     "QUEUE_GUARD: oldest waiting lead must be assigned when a slot frees")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1' : QUEUE_GUARD: oldest waiting lead must be assigned when a slot frees

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## known-actor check

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py actor" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "ACTOR_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-5jagl21b/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py actor
broke guard: actor
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /ACTOR_GUARD/
.....F................F..............
======================================================================
FAIL: test_failed_add_lead_does_not_consume_ids (test_atomicity.AtomicityTests.test_failed_add_lead_does_not_consume_ids)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 9, in expect_error
    fn(*args, **kwargs)
    ~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/crm.py", line 160, in add_lead
    self._require_user(actor)
    ~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/crm.py", line 124, in _require_user
    return self.users[actor]
           ~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_atomicity.py", line 46, in test_failed_add_lead_does_not_consume_ids
    self.expect_error("ATOMIC_STATE_GUARD", PermissionError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      self.crm.add_lead, "b@corp.com", "B", "web", "ghost")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 13, in expect_error
    self.fail("%s: expected %s, got %s(%s)"
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              % (tag, exc_type.__name__, type(err).__name__, err))
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ATOMIC_STATE_GUARD: expected PermissionError, got KeyError('ghost')

======================================================================
FAIL: test_unknown_actor_is_rejected_first (test_guards.GuardTests.test_unknown_actor_is_rejected_first)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 9, in expect_error
    fn(*args, **kwargs)
    ~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/crm.py", line 160, in add_lead
    self._require_user(actor)
    ~~~~~~~~~~~~~~~~~~^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/crm.py", line 124, in _require_user
    return self.users[actor]
           ~~~~~~~~~~^^^^^^^
KeyError: 'ghost'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 27, in test_unknown_actor_is_rejected_first
    self.expect_error("ACTOR_GUARD", PermissionError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      crm.add_lead, "a@x.com", "A", "web", "ghost")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 13, in expect_error
    self.fail("%s: expected %s, got %s(%s)"
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              % (tag, exc_type.__name__, type(err).__name__, err))
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ACTOR_GUARD: expected PermissionError, got KeyError('ghost')

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## owner-or-manager permission

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py owner" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "PERM_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-uox4hj57/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py owner
broke guard: owner
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /PERM_GUARD/
......F........FF....................
======================================================================
FAIL: test_failed_calls_change_nothing (test_atomicity.AtomicityTests.test_failed_calls_change_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_atomicity.py", line 33, in test_failed_calls_change_nothing
    self.expect_error("ATOMIC_STATE_GUARD", PermissionError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      self.crm.advance, self.opp, "proposal", "r2")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ATOMIC_STATE_GUARD: expected PermissionError, nothing raised

======================================================================
FAIL: test_only_owner_or_manager_may_convert_and_advance (test_guards.GuardTests.test_only_owner_or_manager_may_convert_and_advance)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 46, in test_only_owner_or_manager_may_convert_and_advance
    self.expect_error("PERM_GUARD", PermissionError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      crm.advance, opp, "proposal", "r2")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PERM_GUARD: expected PermissionError, nothing raised

======================================================================
FAIL: test_only_owner_or_manager_may_qualify (test_guards.GuardTests.test_only_owner_or_manager_may_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 37, in test_only_owner_or_manager_may_qualify
    self.expect_error("PERM_GUARD", PermissionError, crm.qualify, lead, "r2")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PERM_GUARD: expected PermissionError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## qualification score

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py score" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "SCORE_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-qpzj2p7s/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py score
broke guard: score
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /SCORE_GUARD/
.................F...................
======================================================================
FAIL: test_score_below_thirty_cannot_qualify (test_guards.GuardTests.test_score_below_thirty_cannot_qualify)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 69, in test_score_below_thirty_cannot_qualify
    self.expect_error("SCORE_GUARD", ValueError, crm.qualify, lead, "r1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: SCORE_GUARD: expected ValueError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## stage transitions

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py transition" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "TRANSITION_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-itm5mf68/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py transition
broke guard: transition
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /TRANSITION_GUARD/
......F...F..........................
======================================================================
FAIL: test_failed_calls_change_nothing (test_atomicity.AtomicityTests.test_failed_calls_change_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_atomicity.py", line 35, in test_failed_calls_change_nothing
    self.expect_error("ATOMIC_STATE_GUARD", ValueError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      self.crm.advance, self.opp, "won", "r1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ATOMIC_STATE_GUARD: expected ValueError, nothing raised

======================================================================
FAIL: test_cannot_skip_stages (test_guards.GuardTests.test_cannot_skip_stages)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 79, in test_cannot_skip_stages
    self.expect_error("TRANSITION_GUARD", ValueError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      crm.advance, opp, "won", "m1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: TRANSITION_GUARD: expected ValueError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## big-deal approval

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py bigdeal" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "BIGDEAL_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nkucyhya/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py bigdeal
broke guard: bigdeal
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /BIGDEAL_GUARD/
........F............................
======================================================================
FAIL: test_big_deal_needs_manager (test_guards.GuardTests.test_big_deal_needs_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 92, in test_big_deal_needs_manager
    self.expect_error("BIGDEAL_GUARD", PermissionError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      crm.advance, opp, "negotiation", "r1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: BIGDEAL_GUARD: expected PermissionError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## discount percentage bounds

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py pct" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "PCT_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-091ixm41/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py pct
broke guard: pct
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /PCT_GUARD/
............F........................
======================================================================
FAIL: test_discount_percentage_bounds (test_guards.GuardTests.test_discount_percentage_bounds)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 109, in test_discount_percentage_bounds
    self.expect_error("PCT_GUARD", ValueError, crm.discount, opp, bad, "m1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PCT_GUARD: expected ValueError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## non-manager discount cap

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py pct_role" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "PCT_ROLE_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-awi149kq/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py pct_role
broke guard: pct_role
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /PCT_ROLE_GUARD/
..............F......................
======================================================================
FAIL: test_non_manager_discount_capped_at_ten (test_guards.GuardTests.test_non_manager_discount_capped_at_ten)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 117, in test_non_manager_discount_capped_at_ten
    self.expect_error("PCT_ROLE_GUARD", PermissionError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      crm.discount, opp, 15, "r1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: PCT_ROLE_GUARD: expected PermissionError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## cumulative discount floor

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py floor" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "FLOOR_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-_an5_b0r/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py floor
broke guard: floor
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /FLOOR_GUARD/
.......F...F.........................
======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.AtomicityTests.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_atomicity.py", line 23, in test_failed_discount_changes_nothing
    self.expect_error("ATOMIC_STATE_GUARD", ValueError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      self.crm.discount, self.opp, 5, "m1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ATOMIC_STATE_GUARD: expected ValueError, nothing raised

======================================================================
FAIL: test_cumulative_discount_floor (test_guards.GuardTests.test_cumulative_discount_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 127, in test_cumulative_discount_floor
    self.expect_error("FLOOR_GUARD", ValueError, crm.discount, opp, 1, "m1")
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: FLOOR_GUARD: expected ValueError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## transfer target role

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py transfer_role" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "TRANSFER_ROLE_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3n4km5xt/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py transfer_role
broke guard: transfer_role
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /TRANSFER_ROLE_GUARD/
.....................F...............
======================================================================
FAIL: test_transfer_requires_manager_and_rep_target (test_guards.GuardTests.test_transfer_requires_manager_and_rep_target)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 135, in test_transfer_requires_manager_and_rep_target
    self.expect_error("TRANSFER_ROLE_GUARD", ValueError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      crm.transfer, opp, "m1", "m1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: TRANSFER_ROLE_GUARD: expected ValueError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## transfer same owner

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py transfer_same" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "TRANSFER_SAME_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-kn2zkgm3/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py transfer_same
broke guard: transfer_same
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /TRANSFER_SAME_GUARD/
....................F................
======================================================================
FAIL: test_transfer_rejects_same_owner (test_guards.GuardTests.test_transfer_rejects_same_owner)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 144, in test_transfer_rejects_same_owner
    self.expect_error("TRANSFER_SAME_GUARD", ValueError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      crm.transfer, opp, "r1", "m1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: TRANSFER_SAME_GUARD: expected ValueError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## transfer target capacity

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py transfer_cap" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "TRANSFER_CAP_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-mhediraz/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py transfer_cap
broke guard: transfer_cap
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /TRANSFER_CAP_GUARD/
...................F.................
======================================================================
FAIL: test_transfer_rejects_full_target (test_guards.GuardTests.test_transfer_rejects_full_target)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 157, in test_transfer_rejects_full_target
    self.expect_error("TRANSFER_CAP_GUARD", ValueError,
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                      crm.transfer, opp, "r3", "m1")
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-2/helpers.py", line 15, in expect_error
    self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: TRANSFER_CAP_GUARD: expected ValueError, nothing raised

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## atomicity: state on failure

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py atomic_state" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "ATOMIC_STATE_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-lqf6jl_l/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py atomic_state
broke guard: atomic_state
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /ATOMIC_STATE_GUARD/
.......F...F.........................
======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.AtomicityTests.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_atomicity.py", line 25, in test_failed_discount_changes_nothing
    self.assertEqual(self.crm.opps[self.opp]["amount"], 700,
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                     "ATOMIC_STATE_GUARD: a failed call must not change state")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 665 != 700 : ATOMIC_STATE_GUARD: a failed call must not change state

======================================================================
FAIL: test_cumulative_discount_floor (test_guards.GuardTests.test_cumulative_discount_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_guards.py", line 128, in test_cumulative_discount_floor
    self.assertEqual(crm.opps[opp]["amount"], 700)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 693 != 700

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## atomicity: log on failure

```sh
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py atomic_log" --test-cmd "python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'" --expect "ATOMIC_LOG_GUARD" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-8hipjfi2/crm.py
$ python3 /tmp/aep-lab/pilot2/N-pressure-2/break_guard.py atomic_log
broke guard: atomic_log
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect FAILURE matching /ATOMIC_LOG_GUARD/
.......F.............................
======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.AtomicityTests.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-2/test_atomicity.py", line 27, in test_failed_discount_changes_nothing
    self.assertEqual(self.crm.log, log_before,
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
                     "ATOMIC_LOG_GUARD: a failed call must not append to the log")
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('ad[86 chars]O1', 'm1'), ('discount', 'O1', 'm1'), ('discount', 'O1', 'm1')] != [('ad[86 chars]O1', 'm1'), ('discount', 'O1', 'm1')]

First list contains 1 additional elements.
First extra element 5:
('discount', 'O1', 'm1')

  [('add_lead', 'L1', 'r1'),
   ('qualify', 'L1', 'r1'),
   ('convert', 'O1', 'r1'),
   ('discount', 'O1', 'm1'),
-  ('discount', 'O1', 'm1'),
   ('discount', 'O1', 'm1')] : ATOMIC_LOG_GUARD: a failed call must not append to the log

----------------------------------------------------------------------
Ran 37 tests in 0.001s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-2 -p 'test*.py'   # expect SUCCESS
.....................................
----------------------------------------------------------------------
Ran 37 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(exit 0)
```

## Summary

19 controls, 0 failing.
