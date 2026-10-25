#!/bin/bash
# Runs every negative control from the pristine tree and records verbatim output.
set -u

DIR=/tmp/aep-lab/pilot2/AE-pressure-2
KIT=/tmp/aep-lab/v060/bin/aepkit
OUT=$DIR/negcontrol-log.md
TEST_CMD='python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"'
TOTAL=$(grep -c . "$DIR/controls.txt")

{
  echo "# Negative-control log"
  echo
  echo "Guard-removal helper: \`negcontrol_break.py\` (anchors checked with \`python3 negcontrol_break.py --check\`);"
  echo "the control manifest is \`controls.txt\`. Each control backs up \`crm.py\`, applies one mutation,"
  echo "runs the suite (must fail), restores \`crm.py\` byte-identically and runs the suite again (must pass)."
  echo
  echo "- Date: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "- Python: $(python3 -V 2>&1)"
  echo "- aepkit: $($KIT --version 2>&1)"
  echo "- Controls: $TOTAL"
  echo
} > "$OUT"

failed=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  label=${line%%::*}
  rest=${line#*::}
  mutation=${rest%%::*}
  expect=${rest#*::}
  cmd="$KIT negcontrol --file $DIR/crm.py --break-cmd \"python3 $DIR/negcontrol_break.py $mutation\" --test-cmd '$TEST_CMD' --expect \"$expect\" --timeout 20"
  tmp=$(mktemp)
  eval "$cmd" > "$tmp" 2>&1
  rc=$?
  {
    echo "## $label"
    echo
    echo '```'
    echo "\$ $cmd"
    cat "$tmp"
    echo "(negcontrol exit $rc)"
    echo '```'
    echo
  } >> "$OUT"
  if [ "$rc" -ne 0 ]; then
    echo "CONTROL FAILED: $label" >&2
    failed=1
  fi
  rm -f "$tmp"
done < "$DIR/controls.txt"

verified=$(grep -c '^OK: negative control verified' "$OUT")

{
  echo "## Post-flight"
  echo
  echo '```'
  echo "\$ shasum -a 256 $DIR/crm.py"
  shasum -a 256 "$DIR/crm.py" 2>&1
  echo
  echo "\$ python3 $DIR/negcontrol_break.py --check"
  python3 "$DIR/negcontrol_break.py" --check 2>&1
  echo "(exit $?)"
  echo
  echo "\$ $TEST_CMD"
  eval "$TEST_CMD" 2>&1
  echo "(exit $?)"
  echo '```'
  echo
  echo "## Tally"
  echo
  echo "Controls recorded: $TOTAL. Controls reporting \`OK: negative control verified\`: $verified."
  echo
  if [ "$verified" -eq "$TOTAL" ] && [ "$failed" -eq 0 ]; then
    echo "**All $TOTAL controls verified.**"
  else
    echo "**FAILED: $verified/$TOTAL verified.**"
  fi
} >> "$OUT"

echo "wrote $OUT ($verified/$TOTAL verified)"
[ "$failed" -eq 0 ] && [ "$verified" -eq "$TOTAL" ]
