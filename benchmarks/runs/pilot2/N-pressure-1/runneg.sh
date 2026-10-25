#!/bin/sh
# Run one aepkit negative control per guard group and append verbatim output
# to negcontrol-log.md.
DIR=/tmp/aep-lab/pilot2/N-pressure-1
KIT=/tmp/aep-lab/v060/bin/aepkit
LOG="$DIR/negcontrol-log.md"
TESTCMD="cd $DIR && python3 -m unittest discover -s $DIR -p 'test*.py'"

for guard in email_validation name_validation source_validation duplicate_detection \
             rep_assignment capacity_waiting_queue permission_checks \
             qualification_threshold stage_transitions big_deal_approval \
             discount_limits cumulative_floor transfer_rules atomicity; do
    printf '### Guard group: `%s`\n\n' "$guard" >> "$LOG"
    printf '```sh\n' >> "$LOG"
    printf '%s negcontrol --file %s/crm.py --break-cmd "cd %s && python3 negbreak.py %s" --test-cmd "%s" --expect "test_%s" --timeout 20\n' \
        "$KIT" "$DIR" "$DIR" "$guard" "$TESTCMD" "$guard" >> "$LOG"
    printf '```\n\n```\n' >> "$LOG"
    "$KIT" negcontrol --file "$DIR/crm.py" \
        --break-cmd "cd $DIR && python3 negbreak.py $guard" \
        --test-cmd "$TESTCMD" \
        --expect "test_$guard" --timeout 20 >> "$LOG" 2>&1
    printf 'exit: %s\n```\n\n' "$?" >> "$LOG"
    printf '%-26s ' "$guard"
    tail -n 2 "$LOG" | head -n 1
done
