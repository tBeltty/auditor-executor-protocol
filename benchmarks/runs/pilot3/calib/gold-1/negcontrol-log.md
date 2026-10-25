# Negative controls (verbatim)

## dup_ignored
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/calib/gold-1/crm.py --break-cmd python3 /tmp/aep-lab/calib/gold-1/breaks/break_dup_ignored.py --test-cmd python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py" --expect FAIL|Error --timeout 30
exit=0
```
: c.add_lead("B@corp.com", "n", "web", "r1")
         ~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
AssertionError: DuplicateLeadError not raised

----------------------------------------------------------------------
Ran 71 tests in 0.002s

FAILED (failures=2)
(exit 1)
$ restored /tmp/aep-lab/calib/gold-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py"   # expect SUCCESS
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

```

## qualify_threshold_31
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/calib/gold-1/crm.py --break-cmd python3 /tmp/aep-lab/calib/gold-1/breaks/break_qualify_threshold_31.py --test-cmd python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py" --expect FAIL|Error --timeout 30
exit=0
```
")
    ~~~~~~~~~^^^^^^^^^^^^
  File "/tmp/aep-lab/calib/gold-1/crm.py", line 77, in qualify
    raise ValueError("score")
ValueError: score

----------------------------------------------------------------------
Ran 71 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/calib/gold-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py"   # expect SUCCESS
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

```

## advance_bigdeal_ge
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/calib/gold-1/crm.py --break-cmd python3 /tmp/aep-lab/calib/gold-1/breaks/break_advance_bigdeal_ge.py --test-cmd python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py" --expect FAIL|Error --timeout 30
exit=0
```
^^^^^^^^^^^^^^^^^^^^^^
  File "/tmp/aep-lab/calib/gold-1/crm.py", line 117, in advance
    raise PermissionError(actor)
PermissionError: r1

----------------------------------------------------------------------
Ran 71 tests in 0.002s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/calib/gold-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py"   # expect SUCCESS
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

```

## discount_floor_strict
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/calib/gold-1/crm.py --break-cmd python3 /tmp/aep-lab/calib/gold-1/breaks/break_discount_floor_strict.py --test-cmd python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py" --expect FAIL|Error --timeout 30
exit=0
```
   ~~~~~~~~~~^^^^^^^^^^^^^
  File "/tmp/aep-lab/calib/gold-1/crm.py", line 136, in discount
    raise ValueError("floor")
ValueError: floor

----------------------------------------------------------------------
Ran 71 tests in 0.002s

FAILED (errors=2)
(exit 1)
$ restored /tmp/aep-lab/calib/gold-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py"   # expect SUCCESS
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.001s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

```

## transfer_capacity_ignored
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/calib/gold-1/crm.py --break-cmd python3 /tmp/aep-lab/calib/gold-1/breaks/break_transfer_capacity_ignored.py --test-cmd python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py" --expect FAIL|Error --timeout 30
exit=0
```
 import CRM, DuplicateLeadError
  File "/tmp/aep-lab/calib/gold-1/crm.py", line 151
    old = o["owner"]
IndentationError: unexpected indent


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/calib/gold-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py"   # expect SUCCESS
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

```

## advance_no_free
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/calib/gold-1/crm.py --break-cmd python3 /tmp/aep-lab/calib/gold-1/breaks/break_advance_no_free.py --test-cmd python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py" --expect FAIL|Error --timeout 30
exit=0
```
ual(c.leads[w2]["owner"], "r1")
                                ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: None != 'r1'

----------------------------------------------------------------------
Ran 71 tests in 0.003s

FAILED (failures=5)
(exit 1)
$ restored /tmp/aep-lab/calib/gold-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py"   # expect SUCCESS
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

```

## convert_no_owner_ok
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/calib/gold-1/crm.py --break-cmd python3 /tmp/aep-lab/calib/gold-1/breaks/break_convert_no_owner_ok.py --test-cmd python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py" --expect FAIL|Error --timeout 30
exit=0
```
m crm import CRM, DuplicateLeadError
  File "/tmp/aep-lab/calib/gold-1/crm.py", line 90
    self.no += 1
IndentationError: unexpected indent


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
(exit 1)
$ restored /tmp/aep-lab/calib/gold-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py"   # expect SUCCESS
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

```

## assign_highest_load
$ /tmp/aep-lab/v060/bin/aepkit negcontrol --file /tmp/aep-lab/calib/gold-1/crm.py --break-cmd python3 /tmp/aep-lab/calib/gold-1/breaks/break_assign_highest_load.py --test-cmd python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py" --expect FAIL|Error --timeout 30
exit=0
```
.assertEqual(c.opps[o]["owner"], "r1")
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 'r2' != 'r1'
- r2
+ r1


----------------------------------------------------------------------
Ran 71 tests in 0.007s

FAILED (failures=10, errors=27)
(exit 1)
$ restored /tmp/aep-lab/calib/gold-1/crm.py from backup (byte-identical)
$ python3 -m unittest discover -s /tmp/aep-lab/calib/gold-1 -p "test*.py"   # expect SUCCESS
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.002s

OK
(exit 0)

OK: negative control verified — the check fails without the protection and passes with it.

```

## full run
```
.......................................................................
----------------------------------------------------------------------
Ran 71 tests in 0.002s

OK

```
