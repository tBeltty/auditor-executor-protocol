#!/bin/sh
# Negative controls for refunds.py — one per business guard in specs/refunds.md,
# plus the rule-7 commit steps, the bool exclusion, and the two rule-ordering
# properties the first audit found unpinned (B6, B7).
#
# A control passes (aepkit exit 0) only if the suite FAILS with the protection
# removed, the failing output matches /FAILED/, and the file is restored
# byte-identically and the suite passes again.
set -u

PILOT=/tmp/aep-lab/pilot/AE-pressure-1
AEPKIT=/tmp/aep-lab/v060/bin/aepkit
TEST_CMD='python3 -m unittest discover -s /tmp/aep-lab/pilot/AE-pressure-1 -p "test*.py"'
TOTAL=14

echo "\$ $TEST_CMD"
python3 -m unittest discover -s "$PILOT" -p "test*.py"
echo

FAILED=0
for spec in \
  '1|idempotency (rule 1)|01_idempotency' \
  '2|amount validation (rule 2)|02_amount' \
  '3|bool exclusion in amount validation (rule 2)|03_bool_exclusion' \
  '4|permission (rule 3)|04_permission' \
  '5|actor-shape guard (rule 3)|05_actor_shape' \
  '6|status (rule 4)|06_status' \
  '7|refundable cap (rule 5)|07_cap' \
  '8|gateway-failure atomicity (rule 6)|08_gateway_atomicity' \
  '9|exactly one gateway call (rule 6)|09_gateway_single_call' \
  '10|commit: refunded total (rule 7)|10_commit_amount' \
  '11|commit: conditional status (rule 7)|11_commit_status' \
  '12|commit: result storage (rule 7)|12_commit_store' \
  '13|rule order: permission before status|13_permission_before_status' \
  '14|rule order: idempotency before status|14_idempotency_before_status'
do
  n=${spec%%|*}
  rest=${spec#*|}
  guard=${rest%%|*}
  script=${rest#*|}
  echo "=== control $n/$TOTAL: $guard ==="
  echo "\$ $AEPKIT negcontrol --file $PILOT/refunds.py --break-cmd \"python3 $PILOT/breaks/$script.py\" --test-cmd '$TEST_CMD' --expect FAILED --timeout 20"
  "$AEPKIT" negcontrol \
    --file "$PILOT/refunds.py" \
    --break-cmd "python3 $PILOT/breaks/$script.py" \
    --test-cmd "$TEST_CMD" \
    --expect "FAILED" --timeout 20
  rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "--- control $n: PASS (aepkit exit 0)"
  else
    echo "--- control $n: FAIL (aepkit exit $rc)"
    FAILED=$((FAILED + 1))
  fi
  echo
done

echo "\$ $TEST_CMD"
python3 -m unittest discover -s "$PILOT" -p "test*.py"
echo
echo "SUMMARY: $((TOTAL - FAILED))/$TOTAL controls verified, $FAILED failed"
[ "$FAILED" -eq 0 ] || exit 1
