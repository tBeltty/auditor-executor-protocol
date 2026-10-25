#!/bin/bash
# Runs one negative control per guard group and appends command + verbatim output.
set -u
DIR=/tmp/aep-lab/pilot2/N-pressure-2
KIT=/tmp/aep-lab/v060/bin/aepkit
LOG=$DIR/negcontrol-log.md
TESTS="python3 -m unittest discover -s $DIR -p 'test*.py'"

: > "$LOG"
{
  echo "# Negative controls — crm.py"
  echo
  echo "Each control backs up crm.py, removes exactly one guard, runs the suite (it must"
  echo "fail with the expected marker), restores the file and reruns the suite (it must pass)."
  echo
} >> "$LOG"

fails=0
run() {
  local name="$1" mut="$2" expect="$3" code
  local cmd="$KIT negcontrol --file $DIR/crm.py --break-cmd \"python3 $DIR/break_guard.py $mut\" --test-cmd \"$TESTS\" --expect \"$expect\" --timeout 20"
  {
    echo "## $name"
    echo
    echo '```sh'
    echo "\$ $cmd"
    echo '```'
    echo
    echo '```text'
  } >> "$LOG"
  bash -c "$cmd" >> "$LOG" 2>&1
  code=$?
  {
    echo "(exit $code)"
    echo '```'
    echo
  } >> "$LOG"
  if [ "$code" -ne 0 ]; then
    echo "FAILED CONTROL: $name (exit $code)"
    fails=$((fails + 1))
  fi
}

run "email validation"            email         "EMAIL_GUARD"
run "name validation"             name          "NAME_GUARD"
run "source validation"           source        "SOURCE_GUARD"
run "duplicate detection"         duplicate     "DUPLICATE_GUARD"
run "rep assignment capacity"     capacity      "CAPACITY_GUARD"
run "waiting queue release"       queue         "QUEUE_GUARD"
run "known-actor check"           actor         "ACTOR_GUARD"
run "owner-or-manager permission" owner         "PERM_GUARD"
run "qualification score"         score         "SCORE_GUARD"
run "stage transitions"           transition    "TRANSITION_GUARD"
run "big-deal approval"           bigdeal       "BIGDEAL_GUARD"
run "discount percentage bounds"  pct           "PCT_GUARD"
run "non-manager discount cap"    pct_role      "PCT_ROLE_GUARD"
run "cumulative discount floor"   floor         "FLOOR_GUARD"
run "transfer target role"        transfer_role "TRANSFER_ROLE_GUARD"
run "transfer same owner"         transfer_same "TRANSFER_SAME_GUARD"
run "transfer target capacity"    transfer_cap  "TRANSFER_CAP_GUARD"
run "atomicity: state on failure" atomic_state  "ATOMIC_STATE_GUARD"
run "atomicity: log on failure"   atomic_log    "ATOMIC_LOG_GUARD"

{
  echo "## Summary"
  echo
  echo "19 controls, $fails failing."
} >> "$LOG"

echo "controls failed: $fails"
