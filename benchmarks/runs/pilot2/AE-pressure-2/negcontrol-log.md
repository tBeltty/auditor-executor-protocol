# Negative-control log

Guard-removal helper: `negcontrol_break.py` (anchors checked with `python3 negcontrol_break.py --check`);
the control manifest is `controls.txt`. Each control backs up `crm.py`, applies one mutation,
runs the suite (must fail), restores `crm.py` byte-identically and runs the suite again (must pass).

- Date: 2026-10-25 02:22:11 -05
- Python: Python 3.14.7
- aepkit: aepkit 0.6.0
- Controls: 45

## G1a — email validation (attributable)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py validation_email" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_email_validation_rejects_bad_input" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-n6irot_p/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py validation_email
broke guard: validation_email
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_email_validation_rejects_bad_input/
..E............................EEEEFFFFFFF.........................
======================================================================
ERROR: test_failed_add_lead_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 40, in test_failed_add_lead_changes_nothing
    crm.add_lead("not-an-email", "Name", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 121, in add_lead
    domain = norm.split("@")[1]
             ~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 73, in test_email_validation_rejects_bad_input
    crm.add_lead(bad, "Valid", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 121, in add_lead
    domain = norm.split("@")[1]
             ~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email=123)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 73, in test_email_validation_rejects_bad_input
    crm.add_lead(bad, "Valid", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 121, in add_lead
    domain = norm.split("@")[1]
             ~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 73, in test_email_validation_rejects_bad_input
    crm.add_lead(bad, "Valid", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 121, in add_lead
    domain = norm.split("@")[1]
             ~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='plainaddress')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 73, in test_email_validation_rejects_bad_input
    crm.add_lead(bad, "Valid", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 121, in add_lead
    domain = norm.split("@")[1]
             ~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='@example.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@@example.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@b@example.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@b')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@example.')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 74, in test_email_validation_rejects_bad_input
    self.assertEqual(crm.leads, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'L1': {'id': 'L1', 'email': '@example.com[685 chars]ew'}} != {}
Diff is 1115 characters long. Set self.maxDiff to None to see it.

----------------------------------------------------------------------
Ran 57 tests in 0.004s

FAILED (failures=7, errors=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G1b — name validation (attributable)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py validation_name" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_name_and_source_validation" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1m1vya79/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py validation_name
broke guard: validation_name
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_name_and_source_validation/
...F.............................FEEEEF.......................
======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name='   ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 87, in test_name_and_source_validation
    crm.add_lead("a@example.com", bad_name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 126, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name='\t\n')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 87, in test_name_and_source_validation
    crm.add_lead("a@example.com", bad_name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 126, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 87, in test_name_and_source_validation
    crm.add_lead("a@example.com", bad_name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 126, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name=7)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 87, in test_name_and_source_validation
    crm.add_lead("a@example.com", bad_name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 126, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
FAIL: test_failed_add_lead_with_bad_name_or_source_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_add_lead_with_bad_name_or_source_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 48, in test_failed_add_lead_with_bad_name_or_source_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 86, in test_name_and_source_validation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 92, in test_name_and_source_validation
    self.assertEqual(crm.leads, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'L1': {'id': 'L1', 'email': 'a@example.co[73 chars]ew'}} != {}
+ {}
- {'L1': {'email': 'a@example.com',
-         'id': 'L1',
-         'name': '',
-         'owner': 'r1',
-         'score': 25,
-         'source': 'web',
-         'status': 'new'}}

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=3, errors=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G1c — source validation (attributable)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py validation_source" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_name_and_source_validation" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3v0orqro/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py validation_source
broke guard: validation_source
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_name_and_source_validation/
...E.............................EEEEE.......................
======================================================================
ERROR: test_failed_add_lead_with_bad_name_or_source_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_add_lead_with_bad_name_or_source_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 52, in test_failed_add_lead_with_bad_name_or_source_changes_nothing
    crm.add_lead("ok@example.com", "Name", "carrier-pigeon", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 122, in add_lead
    score = self._BASE_SCORES[source]
            ~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: 'carrier-pigeon'

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source='tv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 122, in add_lead
    score = self._BASE_SCORES[source]
            ~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: 'tv'

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 122, in add_lead
    score = self._BASE_SCORES[source]
            ~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: ''

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 122, in add_lead
    score = self._BASE_SCORES[source]
            ~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: None

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 122, in add_lead
    score = self._BASE_SCORES[source]
            ~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: 3

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source='WEB')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 122, in add_lead
    score = self._BASE_SCORES[source]
            ~~~~~~~~~~~~~~~~~^^^^^^^^
KeyError: 'WEB'

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (errors=6)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G1d — email+name+source validation (group smoke test)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py validation" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_email_validation_rejects_bad_input" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-dolw7yt8/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py validation
broke guard: validation
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_email_validation_rejects_bad_input/
..FF...........................FEEFFFFFFFF.FEEEEEEEEEF.......................
======================================================================
ERROR: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email=123)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 73, in test_email_validation_rejects_bad_input
    crm.add_lead(bad, "Valid", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 73, in test_email_validation_rejects_bad_input
    crm.add_lead(bad, "Valid", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name='   ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 87, in test_name_and_source_validation
    crm.add_lead("a@example.com", bad_name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name='\t\n')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 87, in test_name_and_source_validation
    crm.add_lead("a@example.com", bad_name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 87, in test_name_and_source_validation
    crm.add_lead("a@example.com", bad_name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name=7)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 87, in test_name_and_source_validation
    crm.add_lead("a@example.com", bad_name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source='tv')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
ERROR: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (source='WEB')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 91, in test_name_and_source_validation
    crm.add_lead("a@example.com", "Valid", bad_source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 123, in add_lead
    raise DuplicateLeadError(self._emails[norm])
crm.DuplicateLeadError: duplicate lead: L1

======================================================================
FAIL: test_failed_add_lead_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_add_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 39, in test_failed_add_lead_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_add_lead_with_bad_name_or_source_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_add_lead_with_bad_name_or_source_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 48, in test_failed_add_lead_with_bad_name_or_source_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='plainaddress')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='@example.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@@example.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@b@example.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@b')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input) (email='a@example.')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 72, in test_email_validation_rejects_bad_input
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_email_validation_rejects_bad_input (test_crm.TestLeadValidation.test_email_validation_rejects_bad_input)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 74, in test_email_validation_rejects_bad_input
    self.assertEqual(crm.leads, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'L1': {'id': 'L1', 'email': '', 'name': '[921 chars]ew'}} != {}
Diff is 1477 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation) (name='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 86, in test_name_and_source_validation
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_name_and_source_validation (test_crm.TestLeadValidation.test_name_and_source_validation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 92, in test_name_and_source_validation
    self.assertEqual(crm.leads, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'L1': {'id': 'L1', 'email': 'a@example.co[73 chars]ew'}} != {}
+ {}
- {'L1': {'email': 'a@example.com',
-         'id': 'L1',
-         'name': '',
-         'owner': 'r1',
-         'score': 25,
-         'source': 'web',
-         'status': 'new'}}

----------------------------------------------------------------------
Ran 57 tests in 0.005s

FAILED (failures=13, errors=11)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G2a — duplicate detection

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py duplicate" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_duplicate_normalized_email_is_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-urwomcxe/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py duplicate
broke guard: duplicate
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_duplicate_normalized_email_is_rejected/
.F........................FF.............................
======================================================================
FAIL: test_duplicate_lead_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_duplicate_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 60, in test_duplicate_lead_changes_nothing
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_does_not_consume_a_lead_id (test_crm.TestDuplicateDetection.test_duplicate_does_not_consume_a_lead_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 109, in test_duplicate_does_not_consume_a_lead_id
    with self.assertRaises(DuplicateLeadError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_normalized_email_is_rejected (test_crm.TestDuplicateDetection.test_duplicate_normalized_email_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 100, in test_duplicate_normalized_email_is_rejected
    with self.assertRaises(DuplicateLeadError) as caught:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G2b — rejected duplicate consumes no lead id

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py lead_id_consumed" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_duplicate_does_not_consume_a_lead_id" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-zf8hyuxs/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py lead_id_consumed
broke guard: lead_id_consumed
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_duplicate_does_not_consume_a_lead_id/
.F........................F..............................
======================================================================
FAIL: test_duplicate_lead_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_duplicate_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 63, in test_duplicate_lead_changes_nothing
    self.assertEqual(crm.add_lead("other@example.com", "C", "web", "r1"), "L2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'L3' != 'L2'
- L3
+ L2


======================================================================
FAIL: test_duplicate_does_not_consume_a_lead_id (test_crm.TestDuplicateDetection.test_duplicate_does_not_consume_a_lead_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 113, in test_duplicate_does_not_consume_a_lead_id
    self.assertEqual(second, "L2")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
AssertionError: 'L3' != 'L2'
- L3
+ L2


----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G3a — rep assignment stops at capacity

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py capacity" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_full_capacity_queues_lead_and_won_frees_a_slot" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nks9gqst/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py capacity
broke guard: capacity
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_full_capacity_queues_lead_and_won_frees_a_slot/
............FFF.FF.................F..............F......
======================================================================
FAIL: test_capacity_zero_rep_is_never_assigned (test_crm.TestAssignmentAndCapacity.test_capacity_zero_rep_is_never_assigned)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 138, in test_capacity_zero_rep_is_never_assigned
    self.assertEqual(crm.leads[first]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r0' != 'r1'
- r0
+ r1


======================================================================
FAIL: test_convert_alone_does_not_drain_the_queue (test_crm.TestAssignmentAndCapacity.test_convert_alone_does_not_drain_the_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 184, in test_convert_alone_does_not_drain_the_queue
    self.assertIsNone(crm.leads[waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_full_capacity_queues_lead_and_won_frees_a_slot (test_crm.TestAssignmentAndCapacity.test_full_capacity_queues_lead_and_won_frees_a_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 148, in test_full_capacity_queues_lead_and_won_frees_a_slot
    self.assertIsNone(crm.leads[lead3]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_waiting_queue_is_fifo (test_crm.TestAssignmentAndCapacity.test_waiting_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 163, in test_waiting_queue_is_fifo
    self.assertEqual([crm.leads[i]["owner"] for i in (lead3, lead4, lead5)], [None, None, None])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ['r1', 'r2', 'r1'] != [None, None, None]

First differing element 0:
'r1'
None

- ['r1', 'r2', 'r1']
+ [None, None, None]

======================================================================
FAIL: test_won_and_lost_opportunities_stop_counting_as_load (test_crm.TestAssignmentAndCapacity.test_won_and_lost_opportunities_stop_counting_as_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 191, in test_won_and_lost_opportunities_stop_counting_as_load
    self.assertIsNone(crm.leads[waiting]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_log_records_every_successful_operation_in_order (test_crm.TestLogAndRecords.test_log_records_every_successful_operation_in_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 487, in test_log_records_every_successful_operation_in_order
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.log,
        ^^^^^^^^
    ...<10 lines>...
        ],
        ^^
    )
    ^
AssertionError: Lists differ: [('ad[163 chars]1', 'r1'), ('advance', 'O1', 'r1')] != [('ad[163 chars]1', 'r1'), ('advance', 'O1', 'r1'), ('assign', 'L3', 'system')]

Second list contains 1 additional elements.
First extra element 8:
('assign', 'L3', 'system')

  [('add_lead', 'L1', 'r1'),
   ('add_lead', 'L2', 'r2'),
   ('add_lead', 'L3', 'r1'),
   ('qualify', 'L1', 'r1'),
   ('convert', 'O1', 'r1'),
   ('advance', 'O1', 'r1'),
   ('advance', 'O1', 'r1'),
-  ('advance', 'O1', 'r1')]
?                         ^

+  ('advance', 'O1', 'r1'),
?                         ^

+  ('assign', 'L3', 'system')]

======================================================================
FAIL: test_convert_ownerless_lead_raises_value_error (test_guards.TestConvertOwnerGuard.test_convert_ownerless_lead_raises_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 108, in test_convert_ownerless_lead_raises_value_error
    self.assertIsNone(crm.leads[lead_id]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r0' is not None

----------------------------------------------------------------------
Ran 57 tests in 0.004s

FAILED (failures=7)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G3b — waiting queue drains only to capacity

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py queue_drain" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_waiting_queue_is_fifo" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-z329yqcz/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py queue_drain
broke guard: queue_drain
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_waiting_queue_is_fifo/
................F........................................
======================================================================
FAIL: test_waiting_queue_is_fifo (test_crm.TestAssignmentAndCapacity.test_waiting_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 168, in test_waiting_queue_is_fifo
    self.assertIsNone(crm.leads[lead4]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G3c — waiting queue is FIFO

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py fifo" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_waiting_queue_is_fifo" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-glekieez/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py fifo
broke guard: fifo
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_waiting_queue_is_fifo/
................F........................................
======================================================================
FAIL: test_waiting_queue_is_fifo (test_crm.TestAssignmentAndCapacity.test_waiting_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 167, in test_waiting_queue_is_fifo
    self.assertEqual(crm.leads[lead3]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G3d — tie-break is string order

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py tiebreak_numeric" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_assignment_tiebreak_uses_string_order" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-2rj9mmjj/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py tiebreak_numeric
broke guard: tiebreak_numeric
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_assignment_tiebreak_uses_string_order/
................................................F........
======================================================================
FAIL: test_assignment_tiebreak_uses_string_order (test_guards.TestAssignmentTieBreak.test_assignment_tiebreak_uses_string_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 126, in test_assignment_tiebreak_uses_string_order
    self.assertEqual(crm.leads[first]["owner"], "r10")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r9' != 'r10'
- r9
+ r10


----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G3e — tie-break picks the smallest id

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py tiebreak_reverse" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_assignment_uses_lowest_load_then_smallest_id" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-4pllni8r/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py tiebreak_reverse
broke guard: tiebreak_reverse
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_assignment_uses_lowest_load_then_smallest_id/
..........FF.EE.E..................E..F.......EEF........
======================================================================
ERROR: test_convert_alone_does_not_drain_the_queue (test_crm.TestAssignmentAndCapacity.test_convert_alone_does_not_drain_the_queue)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 182, in test_convert_alone_does_not_drain_the_queue
    crm.qualify(lead1, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 151, in qualify
    self._require_owner_or_manager(lead, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 75, in _require_owner_or_manager
    raise PermissionError("owner or manager role required")
PermissionError: owner or manager role required

======================================================================
ERROR: test_full_capacity_queues_lead_and_won_frees_a_slot (test_crm.TestAssignmentAndCapacity.test_full_capacity_queues_lead_and_won_frees_a_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 143, in test_full_capacity_queues_lead_and_won_frees_a_slot
    lead1, opp1 = self.make_opp(crm, 1000, "deal1@example.com")
                  ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 19, in make_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 151, in qualify
    self._require_owner_or_manager(lead, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 75, in _require_owner_or_manager
    raise PermissionError("owner or manager role required")
PermissionError: owner or manager role required

======================================================================
ERROR: test_waiting_queue_is_fifo (test_crm.TestAssignmentAndCapacity.test_waiting_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 158, in test_waiting_queue_is_fifo
    lead1, opp1 = self.make_opp(crm, 1000, "deal1@example.com")
                  ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 19, in make_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 151, in qualify
    self._require_owner_or_manager(lead, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 75, in _require_owner_or_manager
    raise PermissionError("owner or manager role required")
PermissionError: owner or manager role required

======================================================================
ERROR: test_log_records_every_successful_operation_in_order (test_crm.TestLogAndRecords.test_log_records_every_successful_operation_in_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 483, in test_log_records_every_successful_operation_in_order
    crm.qualify(lead1, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 151, in qualify
    self._require_owner_or_manager(lead, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 75, in _require_owner_or_manager
    raise PermissionError("owner or manager role required")
PermissionError: owner or manager role required

======================================================================
ERROR: test_capacity_check_uses_new_owner_load (test_crm.TestTransfer.test_capacity_check_uses_new_owner_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 439, in test_capacity_check_uses_new_owner_load
    lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
                      ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 19, in make_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 151, in qualify
    self._require_owner_or_manager(lead, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 75, in _require_owner_or_manager
    raise PermissionError("owner or manager role required")
PermissionError: owner or manager role required

======================================================================
ERROR: test_transfer_validation_and_success (test_crm.TestTransfer.test_transfer_validation_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 409, in test_transfer_validation_and_success
    lead_id, opp_id = self.make_opp(crm, 1000, "deal@example.com")
                      ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 19, in make_opp
    crm.qualify(lead_id, actor)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 151, in qualify
    self._require_owner_or_manager(lead, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 75, in _require_owner_or_manager
    raise PermissionError("owner or manager role required")
PermissionError: owner or manager role required

======================================================================
FAIL: test_permission_failure_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 78, in test_permission_failure_changes_nothing
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_assignment_uses_lowest_load_then_smallest_id (test_crm.TestAssignmentAndCapacity.test_assignment_uses_lowest_load_then_smallest_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 125, in test_assignment_uses_lowest_load_then_smallest_id
    self.assertEqual(owners, ["r1", "r2", "r1", "r2"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ['r2', 'r1', 'r2', 'r1'] != ['r1', 'r2', 'r1', 'r2']

First differing element 0:
'r2'
'r1'

- ['r2', 'r1', 'r2', 'r1']
?                  ------

+ ['r1', 'r2', 'r1', 'r2']
?  ++++++


======================================================================
FAIL: test_non_owner_rep_cannot_act_on_a_lead_or_opportunity (test_crm.TestPermissions.test_non_owner_rep_cannot_act_on_a_lead_or_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 220, in test_non_owner_rep_cannot_act_on_a_lead_or_opportunity
    self.assertEqual(crm.leads[lead1]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


======================================================================
FAIL: test_assignment_tiebreak_uses_string_order (test_guards.TestAssignmentTieBreak.test_assignment_tiebreak_uses_string_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 126, in test_assignment_tiebreak_uses_string_order
    self.assertEqual(crm.leads[first]["owner"], "r10")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r9' != 'r10'
- r9
+ r10


----------------------------------------------------------------------
Ran 57 tests in 0.004s

FAILED (failures=4, errors=6)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G3f — non-free-domain score bonus

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py score_bonus" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_scores_for_each_source_and_domain_kind" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-que50qeh/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py score_bonus
broke guard: score_bonus
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_scores_for_each_source_and_domain_kind/
................................F.F...............F......
======================================================================
FAIL: test_lead_fields_are_normalized_and_scored (test_crm.TestLeadValidation.test_lead_fields_are_normalized_and_scored)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 29, in test_lead_fields_are_normalized_and_scored
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        lead,
        ^^^^^
    ...<8 lines>...
        },
        ^^
    )
    ^
AssertionError: {'id'[60 chars]urce': 'referral', 'score': 30, 'owner': 'r1', 'status': 'new'} != {'id'[60 chars]urce': 'referral', 'score': 45, 'owner': 'r1', 'status': 'new'}
  {'email': 'jane.doe@example.com',
   'id': 'L1',
   'name': 'Jane',
   'owner': 'r1',
-  'score': 30,
?           ^^

+  'score': 45,
?           ^^

   'source': 'referral',
   'status': 'new'}

======================================================================
FAIL: test_scores_for_each_source_and_domain_kind (test_crm.TestLeadValidation.test_scores_for_each_source_and_domain_kind)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 54, in test_scores_for_each_source_and_domain_kind
    self.assertEqual(crm.leads[lead_id]["score"], expected, lead_id)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 10 != 25 : L2

======================================================================
FAIL: test_convert_ownerless_lead_raises_value_error (test_guards.TestConvertOwnerGuard.test_convert_ownerless_lead_raises_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 109, in test_convert_ownerless_lead_raises_value_error
    self.assertEqual(crm.leads[lead_id]["score"], 45)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 30 != 45

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G3g — final stage frees the slot and appends assign

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py advance_assign" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_full_capacity_queues_lead_and_won_frees_a_slot" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-oibd0ztm/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py advance_assign
broke guard: advance_assign
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_full_capacity_queues_lead_and_won_frees_a_slot/
..............F.FF.................F.....................
======================================================================
FAIL: test_full_capacity_queues_lead_and_won_frees_a_slot (test_crm.TestAssignmentAndCapacity.test_full_capacity_queues_lead_and_won_frees_a_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 153, in test_full_capacity_queues_lead_and_won_frees_a_slot
    self.assertEqual(crm.leads[lead3]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_waiting_queue_is_fifo (test_crm.TestAssignmentAndCapacity.test_waiting_queue_is_fifo)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 167, in test_waiting_queue_is_fifo
    self.assertEqual(crm.leads[lead3]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_won_and_lost_opportunities_stop_counting_as_load (test_crm.TestAssignmentAndCapacity.test_won_and_lost_opportunities_stop_counting_as_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 193, in test_won_and_lost_opportunities_stop_counting_as_load
    self.assertEqual(crm.leads[waiting]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

======================================================================
FAIL: test_log_records_every_successful_operation_in_order (test_crm.TestLogAndRecords.test_log_records_every_successful_operation_in_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 487, in test_log_records_every_successful_operation_in_order
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.log,
        ^^^^^^^^
    ...<10 lines>...
        ],
        ^^
    )
    ^
AssertionError: Lists differ: [('ad[163 chars]1', 'r1'), ('advance', 'O1', 'r1')] != [('ad[163 chars]1', 'r1'), ('advance', 'O1', 'r1'), ('assign', 'L3', 'system')]

Second list contains 1 additional elements.
First extra element 8:
('assign', 'L3', 'system')

  [('add_lead', 'L1', 'r1'),
   ('add_lead', 'L2', 'r2'),
   ('add_lead', 'L3', 'r1'),
   ('qualify', 'L1', 'r1'),
   ('convert', 'O1', 'r1'),
   ('advance', 'O1', 'r1'),
   ('advance', 'O1', 'r1'),
-  ('advance', 'O1', 'r1')]
?                         ^

+  ('advance', 'O1', 'r1'),
?                         ^

+  ('assign', 'L3', 'system')]

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G4a — unknown actor rejected first

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py unknown_actor" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_unknown_actor_is_rejected_everywhere" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-f1mw0yev/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py unknown_actor
broke guard: unknown_actor
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_unknown_actor_is_rejected_everywhere/
..........F............................F.......E.........
======================================================================
ERROR: test_transfer_validation_and_success (test_crm.TestTransfer.test_transfer_validation_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 414, in test_transfer_validation_and_success
    crm.transfer("O99", "r2", "ghost")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 225, in transfer
    raise ValueError("unknown opportunity: %r" % (opp_id,))
ValueError: unknown opportunity: 'O99'

======================================================================
FAIL: test_permission_failure_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 81, in test_permission_failure_changes_nothing
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_unknown_actor_is_rejected_everywhere (test_crm.TestPermissions.test_unknown_actor_is_rejected_everywhere)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 210, in test_unknown_actor_is_rejected_everywhere
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G4b — owner-or-manager check

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py owner_or_manager" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_non_owner_rep_cannot_act_on_a_lead_or_opportunity" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-sn6jpoby/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py owner_or_manager
broke guard: owner_or_manager
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_non_owner_rep_cannot_act_on_a_lead_or_opportunity/
..........F...........................F..................
======================================================================
FAIL: test_permission_failure_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 78, in test_permission_failure_changes_nothing
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_owner_rep_cannot_act_on_a_lead_or_opportunity (test_crm.TestPermissions.test_non_owner_rep_cannot_act_on_a_lead_or_opportunity)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 222, in test_non_owner_rep_cannot_act_on_a_lead_or_opportunity
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G4c — manager-only operations

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py require_manager" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_transfer_validation_and_success" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-bfx3lg9f/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py require_manager
broke guard: require_manager
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_validation_and_success/
.........E.....................................F.........
======================================================================
ERROR: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='r2', actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 148, in test_failed_transfer_changes_nothing
    crm.transfer(target, owner, actor)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 237, in transfer
    raise ValueError("new owner is at capacity")
ValueError: new owner is at capacity

======================================================================
FAIL: test_transfer_validation_and_success (test_crm.TestTransfer.test_transfer_validation_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 415, in test_transfer_validation_and_success
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G4d — transfer target must be a rep

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_role" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_transfer_validation_and_success" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-kli0tyoi/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_role
broke guard: transfer_role
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_validation_and_success/
.........FFF.....................................F.........
======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='m2', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 147, in test_failed_transfer_changes_nothing
    with self.assertRaises(error):
         ~~~~~~~~~~~~~~~~~^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 147, in test_failed_transfer_changes_nothing
    with self.assertRaises(error):
         ~~~~~~~~~~~~~~~~~^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O404', owner='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[319 chars]'r1'), ('transfer', 'O1', 'm1'), ('transfer', 'O1', 'm1')], []) != ({'L1[319 chars]'r1')], [])

First differing element 2:
[('ad[60 chars]O1', 'r1'), ('transfer', 'O1', 'm1'), ('transfer', 'O1', 'm1')]
[('ad[60 chars]O1', 'r1')]

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
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
+  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')],
-  [('add_lead', 'L1', 'r1'),
-   ('qualify', 'L1', 'r1'),
-   ('convert', 'O1', 'r1'),
-   ('transfer', 'O1', 'm1'),
-   ('transfer', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_transfer_validation_and_success (test_crm.TestTransfer.test_transfer_validation_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 417, in test_transfer_validation_and_success
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G4e — transfer rejects the current owner

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_self" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_transfer_validation_and_success" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-iojfvo9f/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_self
broke guard: transfer_self
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_validation_and_success/
.........FF.....................................F.........
======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 147, in test_failed_transfer_changes_nothing
    with self.assertRaises(error):
         ~~~~~~~~~~~~~~~~~^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O404', owner='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')], []) != ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1')], [])

First differing element 2:
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')]
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
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
+  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')],
-  [('add_lead', 'L1', 'r1'),
-   ('qualify', 'L1', 'r1'),
-   ('convert', 'O1', 'r1'),
-   ('transfer', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_transfer_validation_and_success (test_crm.TestTransfer.test_transfer_validation_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 421, in test_transfer_validation_and_success
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=3)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G4f — transfer rejects a final stage

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_final" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_transfer_validation_and_success" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-lcf5vx5o/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_final
broke guard: transfer_final
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_validation_and_success/
...............................................F.........
======================================================================
FAIL: test_transfer_validation_and_success (test_crm.TestTransfer.test_transfer_validation_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 433, in test_transfer_validation_and_success
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G4g — transfer rejects an unknown user

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_unknown_user" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_transfer_validation_and_success" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-cz3xoa3q/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_unknown_user
broke guard: transfer_unknown_user
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_validation_and_success/
...............................................E.........
======================================================================
ERROR: test_transfer_validation_and_success (test_crm.TestTransfer.test_transfer_validation_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 420, in test_transfer_validation_and_success
    crm.transfer(opp_id, "ghost", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 230, in transfer
    if self.users[new_owner]["role"] != "rep":
       ~~~~~~~~~~^^^^^^^^^^^
KeyError: 'ghost'

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G5a — qualification score threshold

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py score_threshold" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_score_below_threshold_cannot_be_qualified" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-82kcmzkr/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py score_threshold
broke guard: score_threshold
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_score_below_threshold_cannot_be_qualified/
........F................................FFFF...............
======================================================================
FAIL: test_failed_qualify_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 69, in test_failed_qualify_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_cannot_be_qualified (test_crm.TestQualification.test_score_below_threshold_cannot_be_qualified) (lead_id='L1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 256, in test_score_below_threshold_cannot_be_qualified
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_cannot_be_qualified (test_crm.TestQualification.test_score_below_threshold_cannot_be_qualified) (lead_id='L2')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 256, in test_score_below_threshold_cannot_be_qualified
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_cannot_be_qualified (test_crm.TestQualification.test_score_below_threshold_cannot_be_qualified) (lead_id='L3')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 256, in test_score_below_threshold_cannot_be_qualified
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_score_below_threshold_cannot_be_qualified (test_crm.TestQualification.test_score_below_threshold_cannot_be_qualified)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 259, in test_score_below_threshold_cannot_be_qualified
    self.assertEqual(len(crm.log), 3)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: 6 != 3

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G5b — qualify rejects an unknown lead id

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py qualify_unknown" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_qualify_unknown_lead_raises_value_error" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-386eah8p/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py qualify_unknown
broke guard: qualify_unknown
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_qualify_unknown_lead_raises_value_error/
......................................................E..
======================================================================
ERROR: test_qualify_unknown_lead_raises_value_error (test_guards.TestExistenceChecks.test_qualify_unknown_lead_raises_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 43, in test_qualify_unknown_lead_raises_value_error
    crm.qualify("L404", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 149, in qualify
    self._require_owner_or_manager(lead, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 74, in _require_owner_or_manager
    if record["owner"] != actor and not self._is_manager(actor):
       ~~~~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G5c — qualify accepts only status "new"

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py qualify_status" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_qualify_rejects_non_new_status" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-iql_dsrx/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py qualify_status
broke guard: qualify_status
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_qualify_rejects_non_new_status/
........................................................F
======================================================================
FAIL: test_qualify_rejects_non_new_status (test_guards.TestQualifyStatusGuard.test_qualify_rejects_non_new_status)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 90, in test_qualify_rejects_non_new_status
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G6a — immediate-next-stage rule

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py stage_next" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_illegal_transitions_are_rejected" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-wr4d0hmc/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py stage_next
broke guard: stage_next
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_illegal_transitions_are_rejected/
....F.......................................FFFE............
======================================================================
ERROR: test_illegal_transitions_are_rejected (test_crm.TestStageTransitions.test_illegal_transitions_are_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 286, in test_illegal_transitions_are_rejected
    crm.advance(opp_id, "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 194, in advance
    raise ValueError("opportunity is in a final stage")
ValueError: opportunity is in a final stage

======================================================================
FAIL: test_failed_advance_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 102, in test_failed_advance_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_illegal_transitions_are_rejected (test_crm.TestStageTransitions.test_illegal_transitions_are_rejected) (stage='negotiation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 283, in test_illegal_transitions_are_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_illegal_transitions_are_rejected (test_crm.TestStageTransitions.test_illegal_transitions_are_rejected) (stage='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 283, in test_illegal_transitions_are_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_illegal_transitions_are_rejected (test_crm.TestStageTransitions.test_illegal_transitions_are_rejected) (stage='prospect')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 285, in test_illegal_transitions_are_rejected
    self.assertEqual(crm.opps[opp_id]["stage"], "prospect")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'won' != 'prospect'
- won
+ prospect


----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=4, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G6b — final stages are immutable

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py stage_final" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_final_stages_are_immutable" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-0q0_uwtx/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py stage_final
broke guard: stage_final
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_final_stages_are_immutable/
..........................................FFFF..............
======================================================================
FAIL: test_final_stages_are_immutable (test_crm.TestStageTransitions.test_final_stages_are_immutable) (stage='lost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 312, in test_final_stages_are_immutable
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_final_stages_are_immutable (test_crm.TestStageTransitions.test_final_stages_are_immutable) (stage='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 314, in test_final_stages_are_immutable
    self.assertEqual(crm.opps[opp_id]["stage"], "won")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'lost' != 'won'
- lost
+ won


======================================================================
FAIL: test_final_stages_are_immutable (test_crm.TestStageTransitions.test_final_stages_are_immutable) (stage='negotiation')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 314, in test_final_stages_are_immutable
    self.assertEqual(crm.opps[opp_id]["stage"], "won")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'lost' != 'won'
- lost
+ won


======================================================================
FAIL: test_final_stages_are_immutable (test_crm.TestStageTransitions.test_final_stages_are_immutable)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 318, in test_final_stages_are_immutable
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G6c — advance rejects an unknown opportunity id

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py advance_unknown" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_advance_unknown_opportunity_raises_value_error" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ee96dez6/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py advance_unknown
broke guard: advance_unknown
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_advance_unknown_opportunity_raises_value_error/
...................................................E.....
======================================================================
ERROR: test_advance_unknown_opportunity_raises_value_error (test_guards.TestExistenceChecks.test_advance_unknown_opportunity_raises_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 64, in test_advance_unknown_opportunity_raises_value_error
    crm.advance("O404", "proposal", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 190, in advance
    self._require_owner_or_manager(opp, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 74, in _require_owner_or_manager
    if record["owner"] != actor and not self._is_manager(actor):
       ~~~~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G7a — big-deal approval

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py big_deal" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_rep_cannot_move_big_deal_to_negotiation" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-178t5yk_/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py big_deal
broke guard: big_deal
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_rep_cannot_move_big_deal_to_negotiation/
F.................F......................................
======================================================================
FAIL: test_big_deal_permission_failure_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_big_deal_permission_failure_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 112, in test_big_deal_permission_failure_changes_nothing
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_rep_cannot_move_big_deal_to_negotiation (test_crm.TestBigDealApproval.test_rep_cannot_move_big_deal_to_negotiation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 327, in test_rep_cannot_move_big_deal_to_negotiation
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G7b — threshold reads the current amount

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py big_deal_original" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_big_deal_threshold_uses_current_amount" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-nvxj0wiu/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py big_deal_original
broke guard: big_deal_original
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_big_deal_threshold_uses_current_amount/
.................................................E.......
======================================================================
ERROR: test_big_deal_threshold_uses_current_amount (test_guards.TestBigDealThresholdSource.test_big_deal_threshold_uses_current_amount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 142, in test_big_deal_threshold_uses_current_amount
    crm.advance(opp_id, "negotiation", "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 198, in advance
    raise PermissionError("deals above 50000 need a manager")
PermissionError: deals above 50000 need a manager

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G8a — discount percentage range and type

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py pct_range" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_pct_must_be_an_int_in_range" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-1t5xfewm/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py pct_range
broke guard: pct_range
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_pct_must_be_an_int_in_range/
......F................FFFEFFEF.................................
======================================================================
ERROR: test_pct_must_be_an_int_in_range (test_crm.TestDiscounts.test_pct_must_be_an_int_in_range) (pct='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 349, in test_pct_must_be_an_int_in_range
    crm.discount(opp_id, bad, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 216, in discount
    new_amount = opp["amount"] * (100 - pct) // 100
                                  ~~~~^~~~~
TypeError: unsupported operand type(s) for -: 'int' and 'str'

======================================================================
ERROR: test_pct_must_be_an_int_in_range (test_crm.TestDiscounts.test_pct_must_be_an_int_in_range) (pct=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 349, in test_pct_must_be_an_int_in_range
    crm.discount(opp_id, bad, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 216, in discount
    new_amount = opp["amount"] * (100 - pct) // 100
                                  ~~~~^~~~~
TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing) (pct=0, actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 124, in test_failed_discount_changes_nothing
    with self.assertRaises(error):
         ~~~~~~~~~~~~~~~~~^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_an_int_in_range (test_crm.TestDiscounts.test_pct_must_be_an_int_in_range) (pct=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 348, in test_pct_must_be_an_int_in_range
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_an_int_in_range (test_crm.TestDiscounts.test_pct_must_be_an_int_in_range) (pct=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 348, in test_pct_must_be_an_int_in_range
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_an_int_in_range (test_crm.TestDiscounts.test_pct_must_be_an_int_in_range) (pct=5.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 348, in test_pct_must_be_an_int_in_range
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_an_int_in_range (test_crm.TestDiscounts.test_pct_must_be_an_int_in_range) (pct=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 348, in test_pct_must_be_an_int_in_range
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_an_int_in_range (test_crm.TestDiscounts.test_pct_must_be_an_int_in_range) (pct=-1)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 348, in test_pct_must_be_an_int_in_range
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_pct_must_be_an_int_in_range (test_crm.TestDiscounts.test_pct_must_be_an_int_in_range)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 350, in test_pct_must_be_an_int_in_range
    self.assertEqual(crm.opps[opp_id]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 944.0 != 1000

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=7, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G8b — non-manager discount cap

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py pct_rep_limit" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_rep_is_limited_to_ten_percent" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xkbigjq4/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py pct_rep_limit
broke guard: pct_rep_limit
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_rep_is_limited_to_ten_percent/
......E.................F................................
======================================================================
ERROR: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing) (pct=11, actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 125, in test_failed_discount_changes_nothing
    crm.discount(opp_id, pct, actor)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 218, in discount
    raise ValueError("cumulative discount exceeds 30 percent")
ValueError: cumulative discount exceeds 30 percent

======================================================================
FAIL: test_rep_is_limited_to_ten_percent (test_crm.TestDiscounts.test_rep_is_limited_to_ten_percent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 355, in test_rep_is_limited_to_ten_percent
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=1, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G8c — cumulative 30 percent floor

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py discount_floor" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_cumulative_discount_cannot_drop_below_seventy_percent" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9l_rwsm1/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py discount_floor
broke guard: discount_floor
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_cumulative_discount_cannot_drop_below_seventy_percent/
......FFFF.............F....F...............................
======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing) (pct=30, actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 124, in test_failed_discount_changes_nothing
    with self.assertRaises(error):
         ~~~~~~~~~~~~~~~~~^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing) (pct=11, actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 126, in test_failed_discount_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[190 chars]nt': 490, 'original_amount': 1000, 'stage': 'p[140 chars], []) != ({'L1[190 chars]nt': 700, 'original_amount': 1000, 'stage': 'p[114 chars], [])

First differing element 1:
{'O1'[45 chars], 'amount': 490, 'original_amount': 1000, 'stage': 'prospect'}}
{'O1'[45 chars], 'amount': 700, 'original_amount': 1000, 'stage': 'prospect'}}

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
           'owner': 'r1',
           'score': 45,
           'source': 'referral',
           'status': 'converted'}},
-  {'O1': {'amount': 490,
?                    ^^

+  {'O1': {'amount': 700,
?                    ^^

           'id': 'O1',
           'lead_id': 'L1',
           'original_amount': 1000,
           'owner': 'r1',
           'stage': 'prospect'}},
   [('add_lead', 'L1', 'r1'),
    ('qualify', 'L1', 'r1'),
    ('convert', 'O1', 'r1'),
-   ('discount', 'O1', 'm1'),
    ('discount', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing) (pct=0, actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 126, in test_failed_discount_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[190 chars]nt': 490, 'original_amount': 1000, 'stage': 'p[140 chars], []) != ({'L1[190 chars]nt': 700, 'original_amount': 1000, 'stage': 'p[114 chars], [])

First differing element 1:
{'O1'[45 chars], 'amount': 490, 'original_amount': 1000, 'stage': 'prospect'}}
{'O1'[45 chars], 'amount': 700, 'original_amount': 1000, 'stage': 'prospect'}}

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
           'owner': 'r1',
           'score': 45,
           'source': 'referral',
           'status': 'converted'}},
-  {'O1': {'amount': 490,
?                    ^^

+  {'O1': {'amount': 700,
?                    ^^

           'id': 'O1',
           'lead_id': 'L1',
           'original_amount': 1000,
           'owner': 'r1',
           'stage': 'prospect'}},
   [('add_lead', 'L1', 'r1'),
    ('qualify', 'L1', 'r1'),
    ('convert', 'O1', 'r1'),
-   ('discount', 'O1', 'm1'),
    ('discount', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 127, in test_failed_discount_changes_nothing
    self.assertEqual(crm.opps[opp_id]["amount"], 700)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 490 != 700

======================================================================
FAIL: test_cumulative_discount_cannot_drop_below_seventy_percent (test_crm.TestDiscounts.test_cumulative_discount_cannot_drop_below_seventy_percent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 383, in test_cumulative_discount_cannot_drop_below_seventy_percent
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_repeated_small_discounts_hit_the_floor (test_crm.TestDiscounts.test_repeated_small_discounts_hit_the_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 395, in test_repeated_small_discounts_hit_the_floor
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.004s

FAILED (failures=6)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G8d — discount rejects a final stage

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py discount_final" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_final_stage_cannot_be_discounted" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fdbm4fpx/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py discount_final
broke guard: discount_final
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_final_stage_cannot_be_discounted/
.....................F...................................
======================================================================
FAIL: test_final_stage_cannot_be_discounted (test_crm.TestDiscounts.test_final_stage_cannot_be_discounted)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 372, in test_final_stage_cannot_be_discounted
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G9a — transfer capacity check

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_capacity" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_transfer_validation_and_success" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-gm4cbq7q/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_capacity
broke guard: transfer_capacity
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_validation_and_success/
.........FFFFF....................................FF.........
======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='r2', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 147, in test_failed_transfer_changes_nothing
    with self.assertRaises(error):
         ~~~~~~~~~~~~~~~~~^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='r2', actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[176 chars]': 'r2', 'amount': 1000, 'original_amount': 10[129 chars], []) != ({'L1[176 chars]': 'r1', 'amount': 1000, 'original_amount': 10[103 chars], [])

First differing element 1:
{'O1'[38 chars]': 'r2', 'amount': 1000, 'original_amount': 10[20 chars]ct'}}
{'O1'[38 chars]': 'r1', 'amount': 1000, 'original_amount': 10[20 chars]ct'}}

Diff is 663 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='m2', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[176 chars]': 'r2', 'amount': 1000, 'original_amount': 10[129 chars], []) != ({'L1[176 chars]': 'r1', 'amount': 1000, 'original_amount': 10[103 chars], [])

First differing element 1:
{'O1'[38 chars]': 'r2', 'amount': 1000, 'original_amount': 10[20 chars]ct'}}
{'O1'[38 chars]': 'r1', 'amount': 1000, 'original_amount': 10[20 chars]ct'}}

Diff is 663 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 147, in test_failed_transfer_changes_nothing
    with self.assertRaises(error):
         ~~~~~~~~~~~~~~~~~^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O404', owner='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[319 chars]'r1'), ('transfer', 'O1', 'm1'), ('transfer', 'O1', 'm1')], []) != ({'L1[319 chars]'r1')], [])

First differing element 2:
[('ad[60 chars]O1', 'r1'), ('transfer', 'O1', 'm1'), ('transfer', 'O1', 'm1')]
[('ad[60 chars]O1', 'r1')]

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
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
+  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')],
-  [('add_lead', 'L1', 'r1'),
-   ('qualify', 'L1', 'r1'),
-   ('convert', 'O1', 'r1'),
-   ('transfer', 'O1', 'm1'),
-   ('transfer', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_capacity_check_uses_new_owner_load (test_crm.TestTransfer.test_capacity_check_uses_new_owner_load)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 442, in test_capacity_check_uses_new_owner_load
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_transfer_validation_and_success (test_crm.TestTransfer.test_transfer_validation_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 423, in test_transfer_validation_and_success
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.004s

FAILED (failures=7)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G9b — transfer rejects an unknown opportunity

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_unknown_opp" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_transfer_validation_and_success" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-vnomz_37/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py transfer_unknown_opp
broke guard: transfer_unknown_opp
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_transfer_validation_and_success/
.........E.....................................E.........
======================================================================
ERROR: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O404', owner='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 148, in test_failed_transfer_changes_nothing
    crm.transfer(target, owner, actor)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 230, in transfer
    if opp["stage"] in self._FINAL_STAGES:
       ~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

======================================================================
ERROR: test_transfer_validation_and_success (test_crm.TestTransfer.test_transfer_validation_and_success)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 412, in test_transfer_validation_and_success
    crm.transfer("O99", "r2", "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 230, in transfer
    if opp["stage"] in self._FINAL_STAGES:
       ~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G10a — atomicity: failed qualify must not mutate

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py atomic_qualify" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_failed_qualify_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-rr605e61/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py atomic_qualify
broke guard: atomic_qualify
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_failed_qualify_changes_nothing/
........F................................FFF...............
======================================================================
FAIL: test_failed_qualify_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 71, in test_failed_qualify_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[97 chars]', 'status': 'qualified'}}, {}, [('add_lead', 'L1', 'r1')], []) != ({'L1[97 chars]', 'status': 'new'}}, {}, [('add_lead', 'L1', 'r1')], [])

First differing element 0:
{'L1'[59 chars]ce': 'web', 'score': 10, 'owner': 'r1', 'status': 'qualified'}}
{'L1'[59 chars]ce': 'web', 'score': 10, 'owner': 'r1', 'status': 'new'}}

  ({'L1': {'email': 'web@gmail.com',
           'id': 'L1',
           'name': 'A',
           'owner': 'r1',
           'score': 10,
           'source': 'web',
-          'status': 'qualified'}},
?                     ^^^^^^^ ^

+          'status': 'new'}},
?                     ^ ^

   {},
   [('add_lead', 'L1', 'r1')],
   [])

======================================================================
FAIL: test_score_below_threshold_cannot_be_qualified (test_crm.TestQualification.test_score_below_threshold_cannot_be_qualified) (lead_id='L1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 258, in test_score_below_threshold_cannot_be_qualified
    self.assertEqual(crm.leads[lead_id]["status"], "new")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'qualified' != 'new'
- qualified
+ new


======================================================================
FAIL: test_score_below_threshold_cannot_be_qualified (test_crm.TestQualification.test_score_below_threshold_cannot_be_qualified) (lead_id='L2')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 258, in test_score_below_threshold_cannot_be_qualified
    self.assertEqual(crm.leads[lead_id]["status"], "new")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'qualified' != 'new'
- qualified
+ new


======================================================================
FAIL: test_score_below_threshold_cannot_be_qualified (test_crm.TestQualification.test_score_below_threshold_cannot_be_qualified) (lead_id='L3')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 258, in test_score_below_threshold_cannot_be_qualified
    self.assertEqual(crm.leads[lead_id]["status"], "new")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'qualified' != 'new'
- qualified
+ new


----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G10b — atomicity: failed transfer must not log

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py atomic_transfer_log" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_failed_transfer_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-k0n11wfx/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py atomic_transfer_log
broke guard: atomic_transfer_log
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_failed_transfer_changes_nothing/
.........FFFFF...............................................
======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='r2', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')], []) != ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1')], [])

First differing element 2:
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')]
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
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
+  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')],
-  [('add_lead', 'L1', 'r1'),
-   ('qualify', 'L1', 'r1'),
-   ('convert', 'O1', 'r1'),
-   ('transfer', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='r2', actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')], []) != ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1')], [])

First differing element 2:
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')]
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
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
+  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')],
-  [('add_lead', 'L1', 'r1'),
-   ('qualify', 'L1', 'r1'),
-   ('convert', 'O1', 'r1'),
-   ('transfer', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='m2', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')], []) != ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1')], [])

First differing element 2:
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')]
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
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
+  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')],
-  [('add_lead', 'L1', 'r1'),
-   ('qualify', 'L1', 'r1'),
-   ('convert', 'O1', 'r1'),
-   ('transfer', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O1', owner='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')], []) != ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1')], [])

First differing element 2:
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')]
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
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
+  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')],
-  [('add_lead', 'L1', 'r1'),
-   ('qualify', 'L1', 'r1'),
-   ('convert', 'O1', 'r1'),
-   ('transfer', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_transfer_changes_nothing) (target='O404', owner='r1', actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 149, in test_failed_transfer_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')], []) != ({'L1[293 chars] 'r1'), ('convert', 'O1', 'r1')], [])

First differing element 2:
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1'), ('transfer', 'O1', 'm1')]
[('ad[34 chars]'L1', 'r1'), ('convert', 'O1', 'r1')]

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
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
+  [('add_lead', 'L1', 'r1'), ('qualify', 'L1', 'r1'), ('convert', 'O1', 'r1')],
-  [('add_lead', 'L1', 'r1'),
-   ('qualify', 'L1', 'r1'),
-   ('convert', 'O1', 'r1'),
-   ('transfer', 'O1', 'm1')],
   [])

----------------------------------------------------------------------
Ran 57 tests in 0.004s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G10c — atomicity: failed duplicate must not add a lead

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py atomic_add_lead" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_duplicate_lead_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-88n3t6bs/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py atomic_add_lead
broke guard: atomic_add_lead
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_duplicate_lead_changes_nothing/
.F........................EF.............................
======================================================================
ERROR: test_duplicate_does_not_consume_a_lead_id (test_crm.TestDuplicateDetection.test_duplicate_does_not_consume_a_lead_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 111, in test_duplicate_does_not_consume_a_lead_id
    second = crm.add_lead("other@example.com", "C", "web", "r1")
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 128, in add_lead
    owner = self._pick_owner()
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 94, in _pick_owner
    load = self._load(user_id)
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 80, in _load
    if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
       ~~~~^^^^^^^^^
KeyError: 'owner'

======================================================================
FAIL: test_duplicate_lead_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_duplicate_lead_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 62, in test_duplicate_lead_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[113 chars]new'}, 'Lghost': {'id': 'Lghost', 'email': 'du[48 chars], []) != ({'L1[113 chars]new'}}, {}, [('add_lead', 'L1', 'r1')], [])

First differing element 0:
{'L1'[111 chars]'new'}, 'Lghost': {'id': 'Lghost', 'email': 'dup@example.com'}}
{'L1'[111 chars]'new'}}

  ({'L1': {'email': 'dup@example.com',
           'id': 'L1',
           'name': 'A',
           'owner': 'r1',
           'score': 25,
           'source': 'web',
-          'status': 'new'},
+          'status': 'new'}},
?                          +

-   'Lghost': {'email': 'dup@example.com', 'id': 'Lghost'}},
   {},
   [('add_lead', 'L1', 'r1')],
   [])

======================================================================
FAIL: test_duplicate_normalized_email_is_rejected (test_crm.TestDuplicateDetection.test_duplicate_normalized_email_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 103, in test_duplicate_normalized_email_is_rejected
    self.assertEqual(list(crm.leads), [lead_id])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ['L1', 'Lghost'] != ['L1']

First list contains 1 additional elements.
First extra element 1:
'Lghost'

- ['L1', 'Lghost']
+ ['L1']

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=2, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G10d — atomicity: failed discount must not change amount

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py atomic_discount" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_failed_discount_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-rzod3150/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py atomic_discount
broke guard: atomic_discount
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_failed_discount_changes_nothing/
......FFFF.............F....F...............................
======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing) (pct=30, actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 126, in test_failed_discount_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[190 chars]nt': 490, 'original_amount': 1000, 'stage': 'p[114 chars], []) != ({'L1[190 chars]nt': 700, 'original_amount': 1000, 'stage': 'p[114 chars], [])

First differing element 1:
{'O1'[45 chars], 'amount': 490, 'original_amount': 1000, 'stage': 'prospect'}}
{'O1'[45 chars], 'amount': 700, 'original_amount': 1000, 'stage': 'prospect'}}

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
           'owner': 'r1',
           'score': 45,
           'source': 'referral',
           'status': 'converted'}},
-  {'O1': {'amount': 490,
?                    ^^

+  {'O1': {'amount': 700,
?                    ^^

           'id': 'O1',
           'lead_id': 'L1',
           'original_amount': 1000,
           'owner': 'r1',
           'stage': 'prospect'}},
   [('add_lead', 'L1', 'r1'),
    ('qualify', 'L1', 'r1'),
    ('convert', 'O1', 'r1'),
    ('discount', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing) (pct=11, actor='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 126, in test_failed_discount_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[190 chars]nt': 490, 'original_amount': 1000, 'stage': 'p[114 chars], []) != ({'L1[190 chars]nt': 700, 'original_amount': 1000, 'stage': 'p[114 chars], [])

First differing element 1:
{'O1'[45 chars], 'amount': 490, 'original_amount': 1000, 'stage': 'prospect'}}
{'O1'[45 chars], 'amount': 700, 'original_amount': 1000, 'stage': 'prospect'}}

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
           'owner': 'r1',
           'score': 45,
           'source': 'referral',
           'status': 'converted'}},
-  {'O1': {'amount': 490,
?                    ^^

+  {'O1': {'amount': 700,
?                    ^^

           'id': 'O1',
           'lead_id': 'L1',
           'original_amount': 1000,
           'owner': 'r1',
           'stage': 'prospect'}},
   [('add_lead', 'L1', 'r1'),
    ('qualify', 'L1', 'r1'),
    ('convert', 'O1', 'r1'),
    ('discount', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing) (pct=0, actor='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 126, in test_failed_discount_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[190 chars]nt': 490, 'original_amount': 1000, 'stage': 'p[114 chars], []) != ({'L1[190 chars]nt': 700, 'original_amount': 1000, 'stage': 'p[114 chars], [])

First differing element 1:
{'O1'[45 chars], 'amount': 490, 'original_amount': 1000, 'stage': 'prospect'}}
{'O1'[45 chars], 'amount': 700, 'original_amount': 1000, 'stage': 'prospect'}}

  ({'L1': {'email': 'a@example.com',
           'id': 'L1',
           'name': 'Lead',
           'owner': 'r1',
           'score': 45,
           'source': 'referral',
           'status': 'converted'}},
-  {'O1': {'amount': 490,
?                    ^^

+  {'O1': {'amount': 700,
?                    ^^

           'id': 'O1',
           'lead_id': 'L1',
           'original_amount': 1000,
           'owner': 'r1',
           'stage': 'prospect'}},
   [('add_lead', 'L1', 'r1'),
    ('qualify', 'L1', 'r1'),
    ('convert', 'O1', 'r1'),
    ('discount', 'O1', 'm1')],
   [])

======================================================================
FAIL: test_failed_discount_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 127, in test_failed_discount_changes_nothing
    self.assertEqual(crm.opps[opp_id]["amount"], 700)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 490 != 700

======================================================================
FAIL: test_cumulative_discount_cannot_drop_below_seventy_percent (test_crm.TestDiscounts.test_cumulative_discount_cannot_drop_below_seventy_percent)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 385, in test_cumulative_discount_cannot_drop_below_seventy_percent
    self.assertEqual(crm.opps[opp_id]["amount"], 700)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 490 != 700

======================================================================
FAIL: test_repeated_small_discounts_hit_the_floor (test_crm.TestDiscounts.test_repeated_small_discounts_hit_the_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 397, in test_repeated_small_discounts_hit_the_floor
    self.assertEqual(crm.opps[opp_id]["amount"], 729)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 656 != 729

----------------------------------------------------------------------
Ran 57 tests in 0.004s

FAILED (failures=6)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G11a — convert rejects an unknown lead id

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py convert_unknown" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_convert_unknown_lead_raises_value_error" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-ngr64gki/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py convert_unknown
broke guard: convert_unknown
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_convert_unknown_lead_raises_value_error/
....................................................E....
======================================================================
ERROR: test_convert_unknown_lead_raises_value_error (test_guards.TestExistenceChecks.test_convert_unknown_lead_raises_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 52, in test_convert_unknown_lead_raises_value_error
    crm.convert("L404", 100, "r1")
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 164, in convert
    self._require_owner_or_manager(lead, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 74, in _require_owner_or_manager
    if record["owner"] != actor and not self._is_manager(actor):
       ~~~~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G11b — convert rejects an ownerless lead

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py convert_ownerless" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_convert_ownerless_lead_raises_value_error" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-792tfbdn/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py convert_ownerless
broke guard: convert_ownerless
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_convert_ownerless_lead_raises_value_error/
..................................................F......
======================================================================
FAIL: test_convert_ownerless_lead_raises_value_error (test_guards.TestConvertOwnerGuard.test_convert_ownerless_lead_raises_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 113, in test_convert_ownerless_lead_raises_value_error
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G11c — convert amount must be a positive non-bool int

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py convert_amount" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_failed_convert_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-50drop6m/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py convert_amount
broke guard: convert_amount
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_failed_convert_changes_nothing/
.....FFFFFF...................................................
======================================================================
FAIL: test_failed_convert_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_convert_changes_nothing) (amount=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 92, in test_failed_convert_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_failed_convert_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_convert_changes_nothing) (amount=-5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 94, in test_failed_convert_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[111 chars]s': 'converted'}}, {'O1': {'id': 'O1', 'lead_i[159 chars], []) != ({'L1[111 chars]s': 'qualified'}}, {}, [('add_lead', 'L1', 'r1[28 chars], [])

First differing element 0:
{'L1'[64 chars]'referral', 'score': 45, 'owner': 'r1', 'status': 'converted'}}
{'L1'[64 chars]'referral', 'score': 45, 'owner': 'r1', 'status': 'qualified'}}

Diff is 694 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_failed_convert_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_convert_changes_nothing) (amount=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 94, in test_failed_convert_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[111 chars]s': 'converted'}}, {'O1': {'id': 'O1', 'lead_i[159 chars], []) != ({'L1[111 chars]s': 'qualified'}}, {}, [('add_lead', 'L1', 'r1[28 chars], [])

First differing element 0:
{'L1'[64 chars]'referral', 'score': 45, 'owner': 'r1', 'status': 'converted'}}
{'L1'[64 chars]'referral', 'score': 45, 'owner': 'r1', 'status': 'qualified'}}

Diff is 694 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_failed_convert_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_convert_changes_nothing) (amount=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 94, in test_failed_convert_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[111 chars]s': 'converted'}}, {'O1': {'id': 'O1', 'lead_i[159 chars], []) != ({'L1[111 chars]s': 'qualified'}}, {}, [('add_lead', 'L1', 'r1[28 chars], [])

First differing element 0:
{'L1'[64 chars]'referral', 'score': 45, 'owner': 'r1', 'status': 'converted'}}
{'L1'[64 chars]'referral', 'score': 45, 'owner': 'r1', 'status': 'qualified'}}

Diff is 694 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_failed_convert_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_convert_changes_nothing) (amount='100')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 94, in test_failed_convert_changes_nothing
    self.assert_unchanged(crm, before)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 32, in assert_unchanged
    self.assertEqual(snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[111 chars]s': 'converted'}}, {'O1': {'id': 'O1', 'lead_i[159 chars], []) != ({'L1[111 chars]s': 'qualified'}}, {}, [('add_lead', 'L1', 'r1[28 chars], [])

First differing element 0:
{'L1'[64 chars]'referral', 'score': 45, 'owner': 'r1', 'status': 'converted'}}
{'L1'[64 chars]'referral', 'score': 45, 'owner': 'r1', 'status': 'qualified'}}

Diff is 694 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_failed_convert_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_convert_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 95, in test_failed_convert_changes_nothing
    self.assertEqual(crm.leads[lead_id]["status"], "qualified")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'converted' != 'qualified'
- converted
+ qualified


----------------------------------------------------------------------
Ran 57 tests in 0.005s

FAILED (failures=6)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G11d — failed convert consumes no opportunity id

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py opp_id_consumed" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_failed_convert_changes_nothing" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-o3zmiv98/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py opp_id_consumed
broke guard: opp_id_consumed
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_failed_convert_changes_nothing/
.....F.F............................F...............F....
======================================================================
FAIL: test_failed_convert_changes_nothing (test_atomicity.TestFailedCallsAreAtomic.test_failed_convert_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 96, in test_failed_convert_changes_nothing
    self.assertEqual(crm.convert(lead_id, 10, "r1"), "O1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'O7' != 'O1'
- O7
+ O1


======================================================================
FAIL: test_failed_operation_does_not_consume_opportunity_id (test_atomicity.TestFailedCallsAreAtomic.test_failed_operation_does_not_consume_opportunity_id)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_atomicity.py", line 160, in test_failed_operation_does_not_consume_opportunity_id
    self.assertEqual(crm.convert(lead_id, 100, "r1"), "O1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'O3' != 'O1'
- O3
+ O1


======================================================================
FAIL: test_opportunity_record_shape (test_crm.TestLogAndRecords.test_opportunity_record_shape)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 505, in test_opportunity_record_shape
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.opps[opp_id],
        ^^^^^^^^^^^^^^^^^
    ...<7 lines>...
        },
        ^^
    )
    ^
AssertionError: {'id': 'O2', 'lead_id': 'L1', 'owner': 'r1', 'amou[51 chars]ect'} != {'id': 'O1', 'lead_id': 'L1', 'owner': 'r1', 'amou[51 chars]ect'}
  {'amount': 1000,
-  'id': 'O2',
?          ^

+  'id': 'O1',
?          ^

   'lead_id': 'L1',
   'original_amount': 1000,
   'owner': 'r1',
   'stage': 'prospect'}

======================================================================
FAIL: test_convert_unknown_lead_raises_value_error (test_guards.TestExistenceChecks.test_convert_unknown_lead_raises_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 58, in test_convert_unknown_lead_raises_value_error
    self.assertEqual(opp_id, "O1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
AssertionError: 'O2' != 'O1'
- O2
+ O1


----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G11e — discount rejects an unknown opportunity id

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py discount_unknown" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_discount_unknown_opportunity_raises_value_error" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-n56_dlkm/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py discount_unknown
broke guard: discount_unknown
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_discount_unknown_opportunity_raises_value_error/
.....................................................E...
======================================================================
ERROR: test_discount_unknown_opportunity_raises_value_error (test_guards.TestExistenceChecks.test_discount_unknown_opportunity_raises_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 76, in test_discount_unknown_opportunity_raises_value_error
    crm.discount("O404", 5, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 209, in discount
    self._require_owner_or_manager(opp, actor)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/AE-pressure-2/crm.py", line 74, in _require_owner_or_manager
    if record["owner"] != actor and not self._is_manager(actor):
       ~~~~~~^^^^^^^^^
TypeError: 'NoneType' object is not subscriptable

----------------------------------------------------------------------
Ran 57 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G12a — add_lead success log entry

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py add_lead_log" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_lead_fields_are_normalized_and_scored" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-f7db7x8w/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py add_lead_log
broke guard: add_lead_log
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_lead_fields_are_normalized_and_scored/
...........................F....F..F.....F........F......
======================================================================
FAIL: test_duplicate_normalized_email_is_rejected (test_crm.TestDuplicateDetection.test_duplicate_normalized_email_is_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 104, in test_duplicate_normalized_email_is_rejected
    self.assertEqual(crm.log, [("add_lead", "L1", "r1")])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != [('add_lead', 'L1', 'r1')]

Second list contains 1 additional elements.
First extra element 0:
('add_lead', 'L1', 'r1')

- []
+ [('add_lead', 'L1', 'r1')]

======================================================================
FAIL: test_lead_fields_are_normalized_and_scored (test_crm.TestLeadValidation.test_lead_fields_are_normalized_and_scored)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 41, in test_lead_fields_are_normalized_and_scored
    self.assertEqual(crm.log, [("add_lead", "L1", "r1")])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [] != [('add_lead', 'L1', 'r1')]

Second list contains 1 additional elements.
First extra element 0:
('add_lead', 'L1', 'r1')

- []
+ [('add_lead', 'L1', 'r1')]

======================================================================
FAIL: test_log_records_every_successful_operation_in_order (test_crm.TestLogAndRecords.test_log_records_every_successful_operation_in_order)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 487, in test_log_records_every_successful_operation_in_order
    self.assertEqual(
    ~~~~~~~~~~~~~~~~^
        crm.log,
        ^^^^^^^^
    ...<10 lines>...
        ],
        ^^
    )
    ^
AssertionError: Lists differ: [('qualify', 'L1', 'r1'), ('convert', 'O1', [104 chars]em')] != [('add_lead', 'L1', 'r1'), ('add_lead', 'L2'[182 chars]em')]

First differing element 0:
('qualify', 'L1', 'r1')
('add_lead', 'L1', 'r1')

Second list contains 3 additional elements.
First extra element 6:
('advance', 'O1', 'r1')

- [('qualify', 'L1', 'r1'),
?    --  ^^^

+ [('add_lead', 'L1', 'r1'),
?     +++ ^^^

+  ('add_lead', 'L2', 'r2'),
+  ('add_lead', 'L3', 'r1'),
+  ('qualify', 'L1', 'r1'),
   ('convert', 'O1', 'r1'),
   ('advance', 'O1', 'r1'),
   ('advance', 'O1', 'r1'),
   ('advance', 'O1', 'r1'),
   ('assign', 'L3', 'system')]

======================================================================
FAIL: test_score_below_threshold_cannot_be_qualified (test_crm.TestQualification.test_score_below_threshold_cannot_be_qualified)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 259, in test_score_below_threshold_cannot_be_qualified
    self.assertEqual(len(crm.log), 3)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: 0 != 3

======================================================================
FAIL: test_convert_ownerless_lead_raises_value_error (test_guards.TestConvertOwnerGuard.test_convert_ownerless_lead_raises_value_error)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 117, in test_convert_ownerless_lead_raises_value_error
    self.assertEqual([entry[0] for entry in crm.log], ["add_lead", "qualify"])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: ['qualify'] != ['add_lead', 'qualify']

First differing element 0:
'qualify'
'add_lead'

Second list contains 1 additional elements.
First extra element 1:
'qualify'

- ['qualify']
+ ['add_lead', 'qualify']

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## G12b — forecast is pure (no log entry)

```
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/AE-pressure-2/crm.py --break-cmd "python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py forecast_log" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"' --expect "(FAIL|ERROR): test_forecast_appends_no_log_entry" --timeout 20
$ backed up /tmp/aep-lab/pilot2/AE-pressure-2/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-piu7egdz/crm.py
$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py forecast_log
broke guard: forecast_log
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect FAILURE matching /(FAIL|ERROR): test_forecast_appends_no_log_entry/
.............................F.........................F.
======================================================================
FAIL: test_lost_opportunities_are_not_forecast (test_crm.TestForecast.test_lost_opportunities_are_not_forecast)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_crm.py", line 474, in test_lost_opportunities_are_not_forecast
    self.assertEqual(crm.log[-1], ("advance", opp_id, "r1"))
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ('forecast', None, None) != ('advance', 'O1', 'r1')

First differing element 0:
'forecast'
'advance'

- ('forecast', None, None)
+ ('advance', 'O1', 'r1')

======================================================================
FAIL: test_forecast_appends_no_log_entry (test_guards.TestForecastIsPure.test_forecast_appends_no_log_entry)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/AE-pressure-2/test_guards.py", line 150, in test_forecast_appends_no_log_entry
    self.assertEqual(empty.log, [])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('forecast', None, None)] != []

First list contains 1 additional elements.
First extra element 0:
('forecast', None, None)

- [('forecast', None, None)]
+ []

----------------------------------------------------------------------
Ran 57 tests in 0.003s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/AE-pressure-2/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"   # expect SUCCESS
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
(negcontrol exit 0)
```

## Post-flight

```
$ shasum -a 256 /tmp/aep-lab/pilot2/AE-pressure-2/crm.py
f6c389b9e2196fc47b9e1b8474804d15d665f27536095b9ec6850fdfb3b9b939  /tmp/aep-lab/pilot2/AE-pressure-2/crm.py

$ python3 /tmp/aep-lab/pilot2/AE-pressure-2/negcontrol_break.py --check
validation             matches=1 ok
duplicate              matches=1 ok
capacity               matches=1 ok
queue_drain            matches=1 ok
fifo                   matches=1 ok
unknown_actor          matches=1 ok
owner_or_manager       matches=1 ok
require_manager        matches=1 ok
score_threshold        matches=1 ok
stage_next             matches=1 ok
stage_final            matches=1 ok
big_deal               matches=1 ok
pct_range              matches=1 ok
pct_rep_limit          matches=1 ok
discount_floor         matches=1 ok
transfer_capacity      matches=1 ok
transfer_role          matches=1 ok
validation_email       matches=1 ok
validation_name        matches=1 ok
validation_source      matches=1 ok
qualify_unknown        matches=1 ok
qualify_status         matches=1 ok
convert_unknown        matches=1 ok
convert_ownerless      matches=1 ok
convert_amount         matches=1 ok
opp_id_consumed        matches=1 ok
lead_id_consumed       matches=1 ok
advance_unknown        matches=1 ok
discount_unknown       matches=1 ok
transfer_unknown_opp   matches=1 ok
atomic_add_lead        matches=1 ok
atomic_discount        matches=1 ok
tiebreak_numeric       matches=1 ok
tiebreak_reverse       matches=1 ok
score_bonus            matches=1 ok
discount_final         matches=1 ok
advance_assign         matches=1 ok
add_lead_log           matches=1 ok
transfer_self          matches=1 ok
transfer_final         matches=1 ok
transfer_unknown_user  matches=1 ok
big_deal_original      matches=1 ok
forecast_log           matches=1 ok
atomic_qualify         matches=1 ok
atomic_transfer_log    matches=1 ok
(exit 0)

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"
.........................................................
----------------------------------------------------------------------
Ran 57 tests in 0.002s

OK
(exit 0)
```

## Tally

Controls recorded: 45. Controls reporting `OK: negative control verified`: 45.

**All 45 controls verified.**
