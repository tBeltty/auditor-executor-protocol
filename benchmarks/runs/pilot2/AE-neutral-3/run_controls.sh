#!/bin/bash
# Drive aepkit negcontrol for every guard group and append verbatim transcripts
# to negcontrol-log.md.  The log is truncated first so every run is complete.
set -u

DIR=/tmp/aep-lab/pilot2/AE-neutral-3
KIT=/tmp/aep-lab/v060/bin/aepkit
LOG=$DIR/negcontrol-log.md
TEST_CMD="rm -rf $DIR/__pycache__ && python3 -m unittest discover -s $DIR -p 'test*.py'"

cat >"$LOG" <<'HEADER'
# Negative-control log

Each block is a verbatim transcript of the shell command and its complete output.

- harness: /tmp/aep-lab/v060/bin/aepkit negcontrol (backup / break / test / restore / test)
- python: Python 3.14.7
- module under test: /tmp/aep-lab/pilot2/AE-neutral-3/crm.py
HEADER

while IFS=$'\t' read -r name expect; do
  [ -z "${name:-}" ] && continue
  CMD="$KIT negcontrol --file $DIR/crm.py --break-cmd \"python3 $DIR/breaks/apply_break.py $name\" --test-cmd \"$TEST_CMD\" --expect \"$expect\" --timeout 20"
  {
    echo ""
    echo "## control $name"
    echo ""
    echo '```text'
    echo "\$ $CMD"
    eval "$CMD" 2>&1
    echo "[exit $?]"
    echo '```'
  } >>"$LOG"
done <"$DIR/controls.tsv"
