# Negative-control log

## 1. email/name/source validation

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Qif not isinstance(email, str) or not valid_email(normalize_email(email)):\E/if False:/; s/\Qif not isinstance(name, str) or not name.strip():\E/if False:/; s/\Qif source not in SOURCES:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-d98hwq1d/crm.py
$ perl -0pi -e 's/\Qif not isinstance(email, str) or not valid_email(normalize_email(email)):\E/if False:/; s/\Qif not isinstance(name, str) or not name.strip():\E/if False:/; s/\Qif source not in SOURCES:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
....E.................EFFFFFFEEEEEFFFEEEFEEEEE...................
======================================================================
ERROR: test_failed_add_changes_nothing (test_crm.TestAtomicity.test_failed_add_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 421, in test_failed_add_changes_nothing
    crm.add_lead(args[0], args[1], args[2], "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 113, in add_lead
    if normalized.split("@")[1] not in FREE_DOMAINS:
       ~~~~~~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email='plain')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 39, in test_bad_email_rejected
    crm.add_lead(email, "Name", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 113, in add_lead
    if normalized.split("@")[1] not in FREE_DOMAINS:
       ~~~~~~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 39, in test_bad_email_rejected
    crm.add_lead(email, "Name", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 113, in add_lead
    if normalized.split("@")[1] not in FREE_DOMAINS:
       ~~~~~~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email='   ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 39, in test_bad_email_rejected
    crm.add_lead(email, "Name", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 113, in add_lead
    if normalized.split("@")[1] not in FREE_DOMAINS:
       ~~~~~~~~~~~~~~~~~~~~~^^^
IndexError: list index out of range

======================================================================
ERROR: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email=7)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 39, in test_bad_email_rejected
    crm.add_lead(email, "Name", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 103, in add_lead
    normalized = normalize_email(email)
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 21, in normalize_email
    return email.strip().lower()
           ^^^^^^^^^^^
AttributeError: 'int' object has no attribute 'strip'

======================================================================
ERROR: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 39, in test_bad_email_rejected
    crm.add_lead(email, "Name", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 103, in add_lead
    normalized = normalize_email(email)
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 21, in normalize_email
    return email.strip().lower()
           ^^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

======================================================================
ERROR: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email=['a@b.co'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 39, in test_bad_email_rejected
    crm.add_lead(email, "Name", "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 103, in add_lead
    normalized = normalize_email(email)
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 21, in normalize_email
    return email.strip().lower()
           ^^^^^^^^^^^
AttributeError: 'list' object has no attribute 'strip'

======================================================================
ERROR: test_bad_name_rejected (test_crm.TestLeadValidation.test_bad_name_rejected) (name=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 48, in test_bad_name_rejected
    crm.add_lead("n%d@corp.com" % i, name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 121, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'NoneType' object has no attribute 'strip'

======================================================================
ERROR: test_bad_name_rejected (test_crm.TestLeadValidation.test_bad_name_rejected) (name=5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 48, in test_bad_name_rejected
    crm.add_lead("n%d@corp.com" % i, name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 121, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'int' object has no attribute 'strip'

======================================================================
ERROR: test_bad_name_rejected (test_crm.TestLeadValidation.test_bad_name_rejected) (name=['n'])
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 48, in test_bad_name_rejected
    crm.add_lead("n%d@corp.com" % i, name, "web", "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 121, in add_lead
    "name": name.strip(),
            ^^^^^^^^^^
AttributeError: 'list' object has no attribute 'strip'

======================================================================
ERROR: test_bad_source_rejected (test_crm.TestLeadValidation.test_bad_source_rejected) (source='ads')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 56, in test_bad_source_rejected
    crm.add_lead("s%d@corp.com" % i, "N", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 112, in add_lead
    score = BASE_SCORE[source]
            ~~~~~~~~~~^^^^^^^^
KeyError: 'ads'

======================================================================
ERROR: test_bad_source_rejected (test_crm.TestLeadValidation.test_bad_source_rejected) (source='WEB')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 56, in test_bad_source_rejected
    crm.add_lead("s%d@corp.com" % i, "N", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 112, in add_lead
    score = BASE_SCORE[source]
            ~~~~~~~~~~^^^^^^^^
KeyError: 'WEB'

======================================================================
ERROR: test_bad_source_rejected (test_crm.TestLeadValidation.test_bad_source_rejected) (source='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 56, in test_bad_source_rejected
    crm.add_lead("s%d@corp.com" % i, "N", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 112, in add_lead
    score = BASE_SCORE[source]
            ~~~~~~~~~~^^^^^^^^
KeyError: ''

======================================================================
ERROR: test_bad_source_rejected (test_crm.TestLeadValidation.test_bad_source_rejected) (source=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 56, in test_bad_source_rejected
    crm.add_lead("s%d@corp.com" % i, "N", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 112, in add_lead
    score = BASE_SCORE[source]
            ~~~~~~~~~~^^^^^^^^
KeyError: None

======================================================================
ERROR: test_bad_source_rejected (test_crm.TestLeadValidation.test_bad_source_rejected) (source=3)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 56, in test_bad_source_rejected
    crm.add_lead("s%d@corp.com" % i, "N", source, "r1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 112, in add_lead
    score = BASE_SCORE[source]
            ~~~~~~~~~~^^^^^^^^
KeyError: 3

======================================================================
FAIL: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email='a@@b.co')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 38, in test_bad_email_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email='@corp.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 38, in test_bad_email_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email='a@corp')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 38, in test_bad_email_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email='a@.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 38, in test_bad_email_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email='a@com.')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 38, in test_bad_email_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected) (email='a@b@c.com')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 38, in test_bad_email_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 40, in test_bad_email_rejected
    self.assertEqual(crm.leads, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'L1': {'id': 'L1', 'email': 'a@@b.co', 'n[662 chars]ew'}} != {}
Diff is 1092 characters long. Set self.maxDiff to None to see it.

======================================================================
FAIL: test_bad_name_rejected (test_crm.TestLeadValidation.test_bad_name_rejected) (name='')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 47, in test_bad_name_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_bad_name_rejected (test_crm.TestLeadValidation.test_bad_name_rejected) (name='   ')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 47, in test_bad_name_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_bad_name_rejected (test_crm.TestLeadValidation.test_bad_name_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 49, in test_bad_name_rejected
    self.assertEqual(crm.leads, {})
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'L1': {'id': 'L1', 'email': 'n0@corp.com'[189 chars]ew'}} != {}
+ {}
- {'L1': {'email': 'n0@corp.com',
-         'id': 'L1',
-         'name': '',
-         'owner': 'r1',
-         'score': 25,
-         'source': 'web',
-         'status': 'new'},
-  'L2': {'email': 'n1@corp.com',
-         'id': 'L2',
-         'name': '',
-         'owner': 'r1',
-         'score': 25,
-         'source': 'web',
-         'status': 'new'}}

----------------------------------------------------------------------
Ran 44 tests in 0.005s

FAILED (failures=10, errors=15)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 2. duplicate detection

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Qraise DuplicateLeadError(lead_id)\E/pass/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fl3kvsf3/crm.py
$ perl -0pi -e 's/\Qraise DuplicateLeadError(lead_id)\E/pass/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
..................FF........................
======================================================================
FAIL: test_duplicate_after_conversion (test_crm.TestDuplicateDetection.test_duplicate_after_conversion)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 105, in test_duplicate_after_conversion
    with self.assertRaises(DuplicateLeadError) as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

======================================================================
FAIL: test_duplicate_normalized_email (test_crm.TestDuplicateDetection.test_duplicate_normalized_email)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 94, in test_duplicate_normalized_email
    with self.assertRaises(DuplicateLeadError) as ctx:
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 44 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 3. rep assignment and capacity with waiting queue

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Qif load >= rep[\"capacity\"]:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jbx0sh5n/crm.py
$ perl -0pi -e 's/\Qif load >= rep["capacity"]:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
F.F.........................................
======================================================================
FAIL: test_capacity_queue_and_free_slot (test_crm.TestAssignmentAndQueue.test_capacity_queue_and_free_slot)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 152, in test_capacity_queue_and_free_slot
    self.assertIsNone(crm.leads[third]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

======================================================================
FAIL: test_manager_never_owns (test_crm.TestAssignmentAndQueue.test_manager_never_owns)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 138, in test_manager_never_owns
    self.assertIsNone(crm.leads[lead]["owner"])
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r1' is not None

----------------------------------------------------------------------
Ran 44 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 4. permission checks

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Qif actor != owner and self._role(actor) != \"manager\":\E/if False:/; s/\Qif self._role(actor) != \"manager\":\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-fwuwl2f0/crm.py
$ perl -0pi -e 's/\Qif actor != owner and self._role(actor) != "manager":\E/if False:/; s/\Qif self._role(actor) != "manager":\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
............................FFF..........F..
======================================================================
FAIL: test_non_owner_cannot_advance_or_discount (test_crm.TestPermissions.test_non_owner_cannot_advance_or_discount)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 198, in test_non_owner_cannot_advance_or_discount
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_non_owner_cannot_qualify_or_convert (test_crm.TestPermissions.test_non_owner_cannot_qualify_or_convert)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 188, in test_non_owner_cannot_qualify_or_convert
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_transfer_requires_manager (test_crm.TestPermissions.test_transfer_requires_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 208, in test_transfer_requires_manager
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_manager_only (test_crm.TestTransfer.test_manager_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 376, in test_manager_only
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 44 tests in 0.002s

FAILED (failures=4)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 5. qualification score threshold

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Qif lead[\"score\"] < 30:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-73cjdkd9/crm.py
$ perl -0pi -e 's/\Qif lead["score"] < 30:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
........F.......................FFFF...........
======================================================================
FAIL: test_failed_qualify_changes_nothing (test_crm.TestAtomicity.test_failed_qualify_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 429, in test_failed_qualify_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_low_scores_rejected (test_crm.TestQualificationThreshold.test_low_scores_rejected) (lead_id='L1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 227, in test_low_scores_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_low_scores_rejected (test_crm.TestQualificationThreshold.test_low_scores_rejected) (lead_id='L2')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 227, in test_low_scores_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_low_scores_rejected (test_crm.TestQualificationThreshold.test_low_scores_rejected) (lead_id='L3')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 227, in test_low_scores_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_low_scores_rejected (test_crm.TestQualificationThreshold.test_low_scores_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 230, in test_low_scores_rejected
    self.assertNotIn(("qualify", low[0], "r1"), crm.log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ('qualify', 'L1', 'r1') unexpectedly found in [('add_lead', 'L1', 'r1'), ('add_lead', 'L2', 'r1'), ('add_lead', 'L3', 'r1'), ('qualify', 'L1', 'r1'), ('qualify', 'L2', 'r1'), ('qualify', 'L3', 'r1')]

----------------------------------------------------------------------
Ran 44 tests in 0.002s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 6. stage-transition rules

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Qif opp[\"stage\"] in FINAL:\E/if False:/; s/\Qif stage != \"lost\" and stage != NEXT_STAGE.get(opp[\"stage\"]):\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-9m6bz7me/crm.py
$ perl -0pi -e 's/\Qif opp["stage"] in FINAL:\E/if False:/; s/\Qif stage != "lost" and stage != NEXT_STAGE.get(opp["stage"]):\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.....F............................FFFFF.F......
======================================================================
FAIL: test_failed_advance_changes_nothing (test_crm.TestAtomicity.test_failed_advance_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 449, in test_failed_advance_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_backwards_rejected (test_crm.TestStageTransitions.test_backwards_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 262, in test_backwards_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_final_stage_is_final (test_crm.TestStageTransitions.test_final_stage_is_final) (stage='prospect')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 272, in test_final_stage_is_final
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_final_stage_is_final (test_crm.TestStageTransitions.test_final_stage_is_final) (stage='lost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 272, in test_final_stage_is_final
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_final_stage_is_final (test_crm.TestStageTransitions.test_final_stage_is_final) (stage='won')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 272, in test_final_stage_is_final
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_final_stage_is_final (test_crm.TestStageTransitions.test_final_stage_is_final)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 274, in test_final_stage_is_final
    self.assertEqual(crm.opps[opp]["stage"], "lost")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'won' != 'lost'
- won
+ lost


======================================================================
FAIL: test_skipping_stages_rejected (test_crm.TestStageTransitions.test_skipping_stages_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 254, in test_skipping_stages_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 44 tests in 0.002s

FAILED (failures=7)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 7. big-deal approval

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Qif stage == \"negotiation\" and opp[\"amount\"] > 50000 and self._role(actor) != \"manager\":\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-3uyfnppo/crm.py
$ perl -0pi -e 's/\Qif stage == "negotiation" and opp["amount"] > 50000 and self._role(actor) != "manager":\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
...........F................................
======================================================================
FAIL: test_large_negotiation_needs_manager (test_crm.TestBigDealApproval.test_large_negotiation_needs_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 291, in test_large_negotiation_needs_manager
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 44 tests in 0.002s

FAILED (failures=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 8. discount limits and cumulative floor

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Qif not isinstance(pct, int) or isinstance(pct, bool) or pct < 1 or pct > 30:\E/if False:/; s/\Qif self._role(actor) != \"manager\" and pct > 10:\E/if False:/; s/\Qif new_amount * 100 < opp[\"original_amount\"] * 70:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-lguza5vj/crm.py
$ perl -0pi -e 's/\Qif not isinstance(pct, int) or isinstance(pct, bool) or pct < 1 or pct > 30:\E/if False:/; s/\Qif self._role(actor) != "manager" and pct > 10:\E/if False:/; s/\Qif new_amount * 100 < opp["original_amount"] * 70:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.......F.....F.FFFFFEEFF.F..........................
======================================================================
ERROR: test_invalid_pct_rejected (test_crm.TestDiscount.test_invalid_pct_rejected) (pct='10')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 321, in test_invalid_pct_rejected
    crm.discount(opp, pct, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 202, in discount
    new_amount = opp["amount"] * (100 - pct) // 100
                                  ~~~~^~~~~
TypeError: unsupported operand type(s) for -: 'int' and 'str'

======================================================================
ERROR: test_invalid_pct_rejected (test_crm.TestDiscount.test_invalid_pct_rejected) (pct=None)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 321, in test_invalid_pct_rejected
    crm.discount(opp, pct, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 202, in discount
    new_amount = opp["amount"] * (100 - pct) // 100
                                  ~~~~^~~~~
TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'

======================================================================
FAIL: test_failed_discount_changes_nothing (test_crm.TestAtomicity.test_failed_discount_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 458, in test_failed_discount_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_cumulative_floor (test_crm.TestDiscount.test_cumulative_floor)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 347, in test_cumulative_floor
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_pct_rejected (test_crm.TestDiscount.test_invalid_pct_rejected) (pct=0)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 320, in test_invalid_pct_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_pct_rejected (test_crm.TestDiscount.test_invalid_pct_rejected) (pct=31)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 320, in test_invalid_pct_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_pct_rejected (test_crm.TestDiscount.test_invalid_pct_rejected) (pct=-5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 320, in test_invalid_pct_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_pct_rejected (test_crm.TestDiscount.test_invalid_pct_rejected) (pct=True)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 320, in test_invalid_pct_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_pct_rejected (test_crm.TestDiscount.test_invalid_pct_rejected) (pct=False)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 320, in test_invalid_pct_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_pct_rejected (test_crm.TestDiscount.test_invalid_pct_rejected) (pct=1.5)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 320, in test_invalid_pct_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_invalid_pct_rejected (test_crm.TestDiscount.test_invalid_pct_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 322, in test_invalid_pct_rejected
    self.assertEqual(crm.opps[opp]["amount"], 1000)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 705.0 != 1000

======================================================================
FAIL: test_rep_limit_is_10 (test_crm.TestDiscount.test_rep_limit_is_10)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 328, in test_rep_limit_is_10
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

----------------------------------------------------------------------
Ran 44 tests in 0.003s

FAILED (failures=10, errors=2)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 9. transfer rules

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Qif self._role(actor) != \"manager\":\E/if False:/; s/\Qif target is None or target[\"role\"] != \"rep\":\E/if False:/; s/\Qif opp[\"stage\"] in FINAL:\E/if False:/; s/\Qif new_owner == opp[\"owner\"]:\E/if False:/; s/\Qif self._load(new_owner) >= target[\"capacity\"]:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-xtcti05s/crm.py
$ perl -0pi -e 's/\Qif self._role(actor) != "manager":\E/if False:/; s/\Qif target is None or target["role"] != "rep":\E/if False:/; s/\Qif opp["stage"] in FINAL:\E/if False:/; s/\Qif new_owner == opp["owner"]:\E/if False:/; s/\Qif self._load(new_owner) >= target["capacity"]:\E/if False:/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
.........F....................F....F....FF.FEF
======================================================================
ERROR: test_target_must_be_rep (test_crm.TestTransfer.test_target_must_be_rep) (target='m1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 386, in test_target_must_be_rep
    crm.transfer(opp, target, "m1")
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 226, in transfer
    self._free_slot(previous)
    ~~~~~~~~~~~~~~~^^^^^^^^^^
  File "/tmp/aep-lab/pilot2/N-pressure-3/crm.py", line 92, in _free_slot
    rep = self.reps[uid]
          ~~~~~~~~~^^^^^
KeyError: 'nobody'

======================================================================
FAIL: test_failed_transfer_changes_nothing (test_crm.TestAtomicity.test_failed_transfer_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 472, in test_failed_transfer_changes_nothing
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_transfer_requires_manager (test_crm.TestPermissions.test_transfer_requires_manager)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 208, in test_transfer_requires_manager
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_final_stage_is_final (test_crm.TestStageTransitions.test_final_stage_is_final) (stage='lost')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 272, in test_final_stage_is_final
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_full_target_rejected (test_crm.TestTransfer.test_full_target_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 392, in test_full_target_rejected
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_manager_only (test_crm.TestTransfer.test_manager_only)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 376, in test_manager_only
    with self.assertRaises(PermissionError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
AssertionError: PermissionError not raised

======================================================================
FAIL: test_target_must_be_rep (test_crm.TestTransfer.test_target_must_be_rep) (target='nobody')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 385, in test_target_must_be_rep
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_target_must_be_rep (test_crm.TestTransfer.test_target_must_be_rep) (target='r1')
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 385, in test_target_must_be_rep
    with self.assertRaises(ValueError):
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 44 tests in 0.003s

FAILED (failures=7, errors=1)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0

## 10. atomicity: failed call changes nothing and logs nothing

```sh
/tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/pilot2/N-pressure-3/crm.py --break-cmd "perl -0pi -e 's/\Q    def add_lead(self, email, name, source, actor):\E/    def add_lead(self, email, name, source, actor):\n        self.log.append((\"bogus\", \"x\", actor))/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py" --test-cmd 'python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"' --expect "FAILED" --timeout 20
```

```text
$ backed up /tmp/aep-lab/pilot2/N-pressure-3/crm.py -> /var/folders/t0/kj5x1gtn08j274f6nfcpmql40000gn/T/aepkit-negcontrol-jys6sah5/crm.py
$ perl -0pi -e 's/\Q    def add_lead(self, email, name, source, actor):\E/    def add_lead(self, email, name, source, actor):\n        self.log.append(("bogus", "x", actor))/' /tmp/aep-lab/pilot2/N-pressure-3/crm.py

$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect FAILURE matching /FAILED/
....F..............F.FF...F..F..............
======================================================================
FAIL: test_failed_add_changes_nothing (test_crm.TestAtomicity.test_failed_add_changes_nothing)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 422, in test_failed_add_changes_nothing
    self.assertEqual(self.snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({}, {}, [('bogus', 'x', 'r1'), ('bogus', 'x', 'r1'), ('bogus', 'x', 'r1')], []) != ({}, {}, [], [])

First differing element 2:
[('bogus', 'x', 'r1'), ('bogus', 'x', 'r1'), ('bogus', 'x', 'r1')]
[]

- ({}, {}, [('bogus', 'x', 'r1'), ('bogus', 'x', 'r1'), ('bogus', 'x', 'r1')], [])
+ ({}, {}, [], [])

======================================================================
FAIL: test_duplicate_normalized_email (test_crm.TestDuplicateDetection.test_duplicate_normalized_email)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 97, in test_duplicate_normalized_email
    self.assertEqual(self.snapshot(crm), before)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Tuples differ: ({'L1[132 chars]x', 'r1'), ('add_lead', 'L1', 'r1'), ('bogus', 'x', 'r1')], []) != ({'L1[132 chars]x', 'r1'), ('add_lead', 'L1', 'r1')], [])

First differing element 2:
[('bogus', 'x', 'r1'), ('add_lead', 'L1', 'r1'), ('bogus', 'x', 'r1')]
[('bogus', 'x', 'r1'), ('add_lead', 'L1', 'r1')]

  ({'L1': {'email': 'a@corp.com',
           'id': 'L1',
           'name': 'A',
           'owner': 'r1',
           'score': 25,
           'source': 'web',
           'status': 'new'}},
   {},
-  [('bogus', 'x', 'r1'), ('add_lead', 'L1', 'r1'), ('bogus', 'x', 'r1')],
?                                           ----------------------

+  [('bogus', 'x', 'r1'), ('add_lead', 'L1', 'r1')],
   [])

======================================================================
FAIL: test_successful_calls_log_exactly_once (test_crm.TestForecastAndLog.test_successful_calls_log_exactly_once)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 500, in test_successful_calls_log_exactly_once
    self.assertEqual(crm.log, [
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^
        ("add_lead", lead, "r1"),
        ^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
        ("discount", opp, "r1"),
        ^^^^^^^^^^^^^^^^^^^^^^^^
    ])
    ^^
AssertionError: Lists differ: [('bogus', 'x', 'r1'), ('add_lead', 'L1', 'r[100 chars]r1')] != [('add_lead', 'L1', 'r1'), ('qualify', 'L1',[78 chars]r1')]

First differing element 0:
('bogus', 'x', 'r1')
('add_lead', 'L1', 'r1')

First list contains 1 additional elements.
First extra element 5:
('discount', 'O1', 'r1')

- [('bogus', 'x', 'r1'),
-  ('add_lead', 'L1', 'r1'),
? ^

+ [('add_lead', 'L1', 'r1'),
? ^

   ('qualify', 'L1', 'r1'),
   ('convert', 'O1', 'r1'),
   ('advance', 'O1', 'r1'),
   ('discount', 'O1', 'r1')]

======================================================================
FAIL: test_bad_email_rejected (test_crm.TestLeadValidation.test_bad_email_rejected)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 41, in test_bad_email_rejected
    self.assertEqual(crm.log, [])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^
AssertionError: Lists differ: [('bogus', 'x', 'r1'), ('bogus', 'x', 'r1'[217 chars]r1')] != []

First list contains 12 additional elements.
First extra element 0:
('bogus', 'x', 'r1')

+ []
- [('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1'),
-  ('bogus', 'x', 'r1')]

======================================================================
FAIL: test_valid_lead_normalized (test_crm.TestLeadValidation.test_valid_lead_normalized)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 72, in test_valid_lead_normalized
    self.assertEqual(crm.log, [("add_lead", "L1", "r1")])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('bogus', 'x', 'r1'), ('add_lead', 'L1', 'r1')] != [('add_lead', 'L1', 'r1')]

First differing element 0:
('bogus', 'x', 'r1')
('add_lead', 'L1', 'r1')

First list contains 1 additional elements.
First extra element 1:
('add_lead', 'L1', 'r1')

- [('bogus', 'x', 'r1'), ('add_lead', 'L1', 'r1')]
+ [('add_lead', 'L1', 'r1')]

======================================================================
FAIL: test_non_owner_cannot_qualify_or_convert (test_crm.TestPermissions.test_non_owner_cannot_qualify_or_convert)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/tmp/aep-lab/pilot2/N-pressure-3/test_crm.py", line 193, in test_non_owner_cannot_qualify_or_convert
    self.assertEqual(self.crm.log, [("add_lead", self.lead, "r1")])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('bogus', 'x', 'r1'), ('add_lead', 'L1', 'r1')] != [('add_lead', 'L1', 'r1')]

First differing element 0:
('bogus', 'x', 'r1')
('add_lead', 'L1', 'r1')

First list contains 1 additional elements.
First extra element 1:
('add_lead', 'L1', 'r1')

- [('bogus', 'x', 'r1'), ('add_lead', 'L1', 'r1')]
+ [('add_lead', 'L1', 'r1')]

----------------------------------------------------------------------
Ran 44 tests in 0.003s

FAILED (failures=6)
(exit 1)
$ restored /tmp/aep-lab/pilot2/N-pressure-3/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/pilot2/N-pressure-3 -p "test*.py"   # expect SUCCESS
............................................
----------------------------------------------------------------------
Ran 44 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.
```

aepkit exit status: 0
