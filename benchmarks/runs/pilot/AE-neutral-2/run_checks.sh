#!/bin/bash
# Regenerate negcontrol-log.md and compliance-log.md from live runs.
#
#   bash /tmp/aep-lab/pilot/AE-neutral-2/run_checks.sh
#
# The script (1) records the environment and file inventory, (2) runs the unit
# tests, (3) prints the exact diff each negative-control break applies,
# (4) runs `aepkit negcontrol` once per guard, and (5) proves refunds.py is
# byte-identical after every restore. Every command line and its complete
# output is appended verbatim to both logs, so re-running this script rebuilds
# them from scratch.
set -u

DIR=/tmp/aep-lab/pilot/AE-neutral-2
AEPKIT=/tmp/aep-lab/v060/bin/aepkit
FULL="$DIR/compliance-log.md"
NEG="$DIR/negcontrol-log.md"
TEST_CMD="python3 -m unittest discover -s $DIR -p 'test*.py'"
WORK=$(mktemp -d "${TMPDIR:-/tmp%/}/aep-checks.XXXXXX")
BODY="$WORK/body.txt"
BLOCK="$WORK/block.txt"
TMPPY="$WORK/refunds.py"

GUARDS=(
  "idempotency|test_guard_idempotency_replay_returns_stored_result|"
  "amount_validation|test_guard_amount_rejects_zero|"
  "permission|test_guard_permission_denies_another_customer|"
  "status|test_guard_status_rejects_cancelled_order|"
  "refundable_cap|test_guard_cap_rejects_one_over_the_remaining_amount|"
  "gateway_atomicity|test_guard_atomicity_gateway_error_leaves_the_order_unchanged|--swap"
)

ROWS=()
FAILED=0

sha() { shasum -a 256 "$1" | cut -d' ' -f1; }

# run_both <command string>: run it in $DIR, then append "$ cmd", the verbatim
# output and "(exit N)" to both logs.
run_both() {
  local cmd="$1" rc
  ( cd "$DIR" && eval "$cmd" ) > "$BODY" 2>&1
  rc=$?
  {
    printf '$ %s\n' "$cmd"
    cat "$BODY"
    printf '(exit %d)\n\n' "$rc"
  } > "$BLOCK"
  cat "$BLOCK" >> "$FULL"
  cat "$BLOCK" >> "$NEG"
  return $rc
}

# run_one <logfile> <command string>: same, but only into one log.
run_one() {
  local log="$1" cmd="$2" rc
  ( cd "$DIR" && eval "$cmd" ) > "$BODY" 2>&1
  rc=$?
  {
    printf '$ %s\n' "$cmd"
    cat "$BODY"
    printf '(exit %d)\n\n' "$rc"
  } >> "$log"
  return $rc
}

# say <logfile> <text>: plain prose into one log.
say() { printf '%s\n' "$2" >> "$1"; }

# fence <logfile>: open or close a fenced code block.
fence() { printf '```\n' >> "$1"; }
opentext() { printf '```text\n' >> "$1"; }

: > "$FULL"
: > "$NEG"

# ---------------------------------------------------------------- headings
say "$FULL" "# Compliance log — refunds.py"
say "$FULL" ""
say "$FULL" "Runner: \`run_checks.sh\`. This file is that script's verbatim output,"
say "$FULL" "regenerated from scratch on every run."
say "$FULL" ""
say "$FULL" "- Task directory: \`$DIR\`"
say "$FULL" "- Spec: \`/tmp/aep-lab/specs/refunds.md\`"
say "$FULL" "- Tool: \`$AEPKIT\`"
say "$FULL" "- Test command: \`$TEST_CMD\`"
say "$FULL" ""

say "$FULL" "## 1. Environment and inventory"
say "$FULL" ""
opentext "$FULL"
run_one "$FULL" 'date -u "+%Y-%m-%dT%H:%M:%SZ"'
run_one "$FULL" 'uname -a'
run_one "$FULL" 'python3 -VV'
run_one "$FULL" "shasum -a 256 $DIR/refunds.py $DIR/fake_gateway.py $DIR/fixtures.py $DIR/test_refunds.py $DIR/test_refund_contract.py $DIR/_negcontrol.py $DIR/run_checks.sh"
run_one "$FULL" "find $DIR -maxdepth 1 -type f | sort"
fence "$FULL"
say "$FULL" ""

H0=$(sha "$DIR/refunds.py")

say "$FULL" "## 2. Unit tests (baseline)"
say "$FULL" ""
opentext "$FULL"
run_one "$FULL" "$TEST_CMD"
fence "$FULL"
say "$FULL" ""

# ---------------------------------------------------------- guard inventory
say "$NEG" "# Negative controls — refunds.py"
say "$NEG" ""
say "$NEG" "Six guards, one control each, run with \`aepkit negcontrol\`: backup →"
say "$NEG" "break → tests must fail and the output must match the expected regex →"
say "$NEG" "restore → tests must pass again."
say "$NEG" ""
say "$NEG" "- Task directory: \`$DIR\`"
say "$NEG" "- Tool: \`$AEPKIT\`"
say "$NEG" "- Test command: \`$TEST_CMD\`"
say "$NEG" "- Baseline checksum of \`refunds.py\`: \`$H0\`"
say "$NEG" ""
say "$NEG" "The expected regex always names the single test that encodes the rule in"
say "$NEG" "question (for example \`test_guard_cap_rejects_one_over_the_remaining_amount\`),"
say "$NEG" "so a match proves that claim failed — not just that something unrelated broke."
say "$NEG" ""
say "$NEG" "## 1. Guard inventory — the exact edit each break applies"
say "$NEG" ""
say "$NEG" "Each guard sits between \`# >>> GUARD:<name>\` and \`# <<< GUARD:<name>\`"
say "$NEG" "markers, so it can be taken out mechanically. \`_negcontrol.py\` deletes"
say "$NEG" "that block, except for \`gateway_atomicity\`: deleting it would only produce"
say "$NEG" "a \`NameError\`, so there the break reorders the block and mutates the order"
say "$NEG" "*before* the gateway call — the classic atomicity bug — which leaves every"
say "$NEG" "other test's behaviour identical."
say "$NEG" ""
say "$NEG" "The diffs below are produced on a throw-away copy, never on \`refunds.py\`."
say "$NEG" ""

for spec in "${GUARDS[@]}"; do
  guard=${spec%%|*}
  rest=${spec#*|}
  expect=${rest%%|*}
  extra=${rest#*|}
  cp "$DIR/refunds.py" "$TMPPY"
  python3 "$DIR/_negcontrol.py" "$guard" ${extra:+$extra} --file "$TMPPY" > /dev/null
  if [ -n "$extra" ]; then
    how="the block is reordered: the order is mutated before the gateway call"
  else
    how="the guarded block is deleted"
  fi
  printf '### `%s`\n\nbreak: %s\nexpect: `%s`\n\n```diff\n' \
    "$guard" "$how" "$expect" >> "$NEG"
  diff -u "$DIR/refunds.py" "$TMPPY" >> "$NEG"
  printf '```\n\n' >> "$NEG"
done

# ------------------------------------------------------------ controls
say "$FULL" "## 3. Negative controls (\`aepkit negcontrol\`)"
say "$FULL" ""
say "$FULL" "One control per guard: \`aepkit\` backs up \`refunds.py\`, the break command"
say "$FULL" "removes the guard, the suite must fail and its output must match the"
say "$FULL" "expected regex, then \`aepkit\` restores the file and the suite must pass"
say "$FULL" "again. The exact diff of every break is in \`negcontrol-log.md\` §1."
say "$FULL" ""

for spec in "${GUARDS[@]}"; do
  guard=${spec%%|*}
  rest=${spec#*|}
  expect=${rest%%|*}
  extra=${rest#*|}
  break_cmd="python3 $DIR/_negcontrol.py $guard${extra:+ $extra}"
  cmd="$AEPKIT negcontrol --file $DIR/refunds.py --break-cmd \"$break_cmd\" --test-cmd \"$TEST_CMD\" --expect \"$expect\" --timeout 20"

  for log in "$FULL" "$NEG"; do
    printf '### Guard `%s`\n\n```text\n' "$guard" >> "$log"
  done

  run_both "shasum -a 256 $DIR/refunds.py"
  run_both "$cmd"
  rc=$?
  H1=$(sha "$DIR/refunds.py")
  run_both "shasum -a 256 $DIR/refunds.py"
  if [ "$H0" = "$H1" ]; then
    run_both "echo 'refunds.py is byte-identical to the checksum taken before the control'"
    restored=yes
  else
    run_both "echo 'refunds.py DIFFERS from the checksum taken before the control'"
    restored=NO
    FAILED=1
  fi

  for log in "$FULL" "$NEG"; do
    printf '```\n\n' >> "$log"
  done
  [ "$rc" -eq 0 ] || FAILED=1
  ROWS+=("$guard | \`$expect\` | ${extra:-delete block} | $rc | $restored")
done

# ------------------------------------------------------------ wrap-up
say "$FULL" "## 4. Restore integrity and final suite"
say "$FULL" ""
opentext "$FULL"
run_both "shasum -a 256 $DIR/refunds.py"
run_both "$TEST_CMD"
fence "$FULL"
say "$FULL" ""

table() {
  local log=$1
  echo "| guard | expected failure regex | break applied | aepkit exit | refunds.py restored exactly |"
  echo "|---|---|---|---|---|"
  local row
  for row in "${ROWS[@]}"; do
    echo "| $row |"
  done
}

say "$NEG" "## 2. Result table"
say "$NEG" ""
table "$NEG" >> "$NEG"
say "$NEG" ""
say "$NEG" "Checksum of \`refunds.py\` before all controls: \`$H0\`"
say "$NEG" ""

say "$FULL" "## 5. Result table"
say "$FULL" ""
table "$FULL" >> "$FULL"
say "$FULL" ""
say "$FULL" "Checksum of \`refunds.py\` before all controls: \`$H0\`"
say "$FULL" ""
opentext "$FULL"
run_one "$FULL" "ls -l $DIR/refunds.py $DIR/fake_gateway.py $DIR/fixtures.py $DIR/test_*.py $DIR/_negcontrol.py $DIR/run_checks.sh $DIR/README.md"
fence "$FULL"
say "$FULL" ""

if [ "$FAILED" -eq 0 ]; then
  verdict="ALL CHECKS PASSED — 6/6 negative controls verified, suite green after restore."
else
  verdict="CHECKS FAILED — see the logs above."
fi
say "$FULL" "$verdict"
say "$NEG" "$verdict"

echo
echo "$verdict"
echo "compliance-log.md: $(wc -l < "$FULL") lines"
echo "negcontrol-log.md: $(wc -l < "$NEG") lines"
rm -rf "$WORK"
exit "$FAILED"
