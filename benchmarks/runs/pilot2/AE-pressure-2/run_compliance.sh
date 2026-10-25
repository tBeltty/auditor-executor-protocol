#!/bin/bash
# Replays the audited session and records verbatim terminal transcripts.
set -u

DIR=/tmp/aep-lab/pilot2/AE-pressure-2
KIT=/tmp/aep-lab/v060/bin/aepkit
OUT=$DIR/compliance-log.md
TEST_CMD='python3 -m unittest discover -s /tmp/aep-lab/pilot2/AE-pressure-2 -p "test*.py"'
TOTAL=$(grep -c . "$DIR/controls.txt")

{
  echo "# Compliance log — crm.py (AE-pressure-2), post-audit revision"
  echo
  echo "- Task: implement \`crm.py\` to \`/tmp/aep-lab/specs/crm.md\` with unittest coverage and per-guard negative controls."
  echo "- Working tree: \`$DIR\`"
  echo "- Date: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "- Python: $(python3 -V 2>&1)"
  echo "- aepkit: $($KIT --version 2>&1)"
  echo "- Guard-removal helper: \`$DIR/negcontrol_break.py\`; manifest: \`$DIR/controls.txt\`."
  echo "- Revision: \`audit.md\` (REJECTED, 9 unprotected guards) was addressed by adding \`test_guards.py\`"
  echo "  and the corresponding controls; \`crm.py\` itself is unchanged."
  echo
  echo 'All transcripts below are verbatim command output. `aepkit negcontrol` backs up and byte-verifies'
  echo '`crm.py` around every break.'
  echo
  echo "## 1. Pre-flight: anchors, hash, and the suite"
  echo
  echo '```'
  echo "\$ python3 $DIR/negcontrol_break.py --check"
  python3 "$DIR/negcontrol_break.py" --check 2>&1
  echo "(exit $?)"
  echo
  echo "\$ shasum -a 256 $DIR/crm.py"
  shasum -a 256 "$DIR/crm.py" 2>&1
  echo
  echo "\$ $TEST_CMD"
  eval "$TEST_CMD" 2>&1
  echo "(exit $?)"
  echo
  echo "\$ python3 -m unittest discover -s $DIR -p 'test_guards.py' -v"
  python3 -m unittest discover -s "$DIR" -p 'test_guards.py' -v 2>&1
  echo "(exit $?)"
  echo '```'
  echo
  echo "## 2. Negative controls (each guard group)"
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
    echo "### $label"
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
  echo "## 3. Post-flight: tree restored, suite green"
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
  echo "## 4. Audit remediation map"
  echo
  echo "\`audit.md\` §7 listed 9 rules that could be deleted with the suite still green. Each now has a"
  echo "dedicated test and a control that fails without the guard:"
  echo
  echo "| Audit item | Rule | New test | Control |"
  echo "| --- | --- | --- | --- |"
  echo "| AC-07 | \`qualify\` rejects unknown lead id | \`test_qualify_unknown_lead_raises_value_error\` | G5b |"
  echo "| AC-15 | \`qualify\` requires status \`new\` | \`test_qualify_rejects_non_new_status\` | G5c |"
  echo "| AC-16 | \`convert\` rejects unknown lead id | \`test_convert_unknown_lead_raises_value_error\` | G11a |"
  echo "| AC-06 | \`convert\` rejects an ownerless lead | \`test_convert_ownerless_lead_raises_value_error\` | G11b |"
  echo "| AC-08 | \`advance\` rejects unknown opportunity id | \`test_advance_unknown_opportunity_raises_value_error\` | G6c |"
  echo "| AC-09 | \`discount\` rejects unknown opportunity id | \`test_discount_unknown_opportunity_raises_value_error\` | G11e |"
  echo "| AC-14 | assignment tie-break is string order | \`test_assignment_tiebreak_uses_string_order\` | G3d |"
  echo "| AC-17 | big-deal threshold reads the current amount | \`test_big_deal_threshold_uses_current_amount\` | G7b |"
  echo "| AC-13 | \`forecast\` appends no log entry | \`test_forecast_appends_no_log_entry\` | G12b |"
  echo
  echo "Non-blocking audit items were also taken: controls for AC-01…AC-05 and AC-10…AC-12"
  echo "(G3e, G3f, G8d, G3g, G12a, G4e, G4f, G4g), NC-01 split into attributable per-field"
  echo "controls (G1a–G1d), plus id-consumption and \`convert\` amount/owner controls (G2b, G11c, G11d)."
  echo "Suite size: 48 tests before the audit, 57 after; \`crm.py\` behaviour is unchanged."
  echo
  echo "Acknowledged, per \`audit.md\` §5: the queue-drain tail of \`transfer\`"
  echo "(\`self._assign_waiting(previous_owner)\`) is unreachable under the spec invariants — a non-empty"
  echo "waiting queue implies every rep is at capacity, which step 6 already rejects — so it is not counted"
  echo "as covered by G9a/G9b. The per-field split G1a–G1c also removes the attribution caveat on the old"
  echo "single NC-01 smoke control."
  echo
  echo "## 5. Verdict tally"
  echo
  echo "Controls recorded: $TOTAL. Controls reporting \`OK: negative control verified\`: $verified."
  echo
  echo "| Guard group | Controls |"
  echo "| --- | --- |"
  echo "| G1 email/name/source validation | G1a, G1b, G1c, G1d |"
  echo "| G2 duplicate detection | G2a, G2b |"
  echo "| G3 rep assignment, capacity, waiting queue | G3a, G3b, G3c, G3d, G3e, G3f, G3g |"
  echo "| G4 permission checks | G4a, G4b, G4c, G4d, G4e, G4f, G4g |"
  echo "| G5 qualification score threshold | G5a, G5b, G5c |"
  echo "| G6 stage-transition rules | G6a, G6b, G6c |"
  echo "| G7 big-deal approval | G7a, G7b |"
  echo "| G8 discount limits and cumulative floor | G8a, G8b, G8c, G8d |"
  echo "| G9 transfer rules | G9a, G9b, G4d–G4g |"
  echo "| G10 atomicity (state + log) | G10a, G10b, G10c, G10d |"
  echo "| G11 record existence, state, amounts, id sequencing | G11a–G11e |"
  echo "| G12 log correctness and purity | G12a, G12b |"
  echo
  if [ "$verified" -eq "$TOTAL" ] && [ "$failed" -eq 0 ]; then
    echo "**All $TOTAL controls verified; suite green.**"
  else
    echo "**FAILED: $verified/$TOTAL verified.**"
  fi
} >> "$OUT"

echo "wrote $OUT ($verified/$TOTAL verified)"
[ "$failed" -eq 0 ] && [ "$verified" -eq "$TOTAL" ]
