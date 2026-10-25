# Execution guide

TASK 1: Create the SQLite schema (orders, outbox with status/attempts/lease) and an atomic confirm_order that inserts the outbox row in the same transaction, with no network I/O. Verify: python3 -m unittest test_webhooks.TestOutbox -v
TASK 2: Validate the riskiest assumption: with a hanging endpoint and 16 concurrent workers, confirm_order p99 stays under 1.5 s and all 200 events are delivered after the endpoint recovers. Verify: python3 -m unittest test_webhooks.TestDelivery.test_slow_endpoint_p99_and_no_loss -v
TASK 3: Implement claim() with leases so a crashed worker's in-flight events are reclaimed. Verify: python3 -m unittest test_webhooks.TestOutbox.test_claim_is_exclusive_and_lease_expiry_recovers -v
TASK 4: Implement the Dispatcher thread pool with exponential backoff retry; a 300-event burst where every event fails once must be fully delivered. Verify: python3 -m unittest test_webhooks.TestDelivery.test_retry_until_success_burst -v
TASK 5: Keep events that exhaust max_attempts as 'dead' rows (never deleted) for manual replay. Verify: python3 -m unittest test_webhooks.TestDelivery.test_dead_letter_retained -v
TASK 6: Run the whole suite. Verify: python3 -m unittest discover -s /tmp/aep-lab/runs/e1/O-1
