#!/bin/sh
# Runs the six per-guard negative controls and records them verbatim.
cd /tmp/aep-lab/pilot/N-pressure-1 || exit 1
LOG=/tmp/aep-lab/pilot/N-pressure-1/negcontrol-log.md
: > "$LOG"

run() {
    name=$1
    breakcmd=$2
    testcmd=$3
    expect=$4
    file=$5

    {
        printf '\n## %s\n\n' "$name"
        printf 'Command:\n\n```sh\n/tmp/aep-lab/v060/bin/aepkit negcontrol --file %s --break-cmd "%s" --test-cmd "%s" --expect "%s" --timeout 20\n```\n\n' \
            "$file" "$breakcmd" "$testcmd" "$expect"
        printf 'Verbatim output:\n\n```\n'
        /tmp/aep-lab/v060/bin/aepkit negcontrol --file "$file" --break-cmd "$breakcmd" \
            --test-cmd "$testcmd" --expect "$expect" --timeout 20 2>&1
        printf 'exit=%s\n```\n' "$?"
    } >> "$LOG"
}

run "Guard 1 — idempotency" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if idempotency_key in order\[\"keys\"\]:/    if False:/' refunds.py" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_idempotency" \
    "FAILED \\(failures=[1-9]" \
    "/tmp/aep-lab/pilot/N-pressure-1/refunds.py"

run "Guard 2 — amount validation" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if not _is_valid_amount(amount):/    if False:/' refunds.py" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_amount" \
    "FAILED \\(failures=[1-9]" \
    "/tmp/aep-lab/pilot/N-pressure-1/refunds.py"

run "Guard 3 — permission" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if not _is_allowed(actor, order):/    if False:/' refunds.py" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_permission" \
    "FAILED \\(failures=[1-9]" \
    "/tmp/aep-lab/pilot/N-pressure-1/refunds.py"

run "Guard 4 — status" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if order\[\"status\"\] not in _REFUNDABLE_STATUSES:/    if False:/' refunds.py" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_status" \
    "FAILED \\(failures=[1-9]" \
    "/tmp/aep-lab/pilot/N-pressure-1/refunds.py"

run "Guard 5 — refundable cap" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && sed -i '' 's/    if amount > refundable:/    if False:/' refunds.py" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_cap" \
    "FAILED \\(failures=[1-9]" \
    "/tmp/aep-lab/pilot/N-pressure-1/refunds.py"

run "Guard 6 — gateway-failure atomicity" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 break_gateway.py" \
    "cd /tmp/aep-lab/pilot/N-pressure-1 && python3 -m unittest test_gateway" \
    "FAILED \\(failures=[1-9]" \
    "/tmp/aep-lab/pilot/N-pressure-1/refunds.py"
