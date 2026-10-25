"""Background webhook delivery: bounded worker pool draining the outbox."""
import threading
import time
import urllib.request

from outbox import Outbox


def http_post(url, body, headers, timeout):
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


class Dispatcher:
    def __init__(self, outbox, workers=64, timeout=10.0, max_attempts=8, backoff_base=2.0,
                 poll_interval=0.05, stale_after=120.0, sender=http_post):
        self.outbox = outbox
        self.workers = workers
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.backoff_base = backoff_base
        self.poll_interval = poll_interval
        self.stale_after = stale_after
        self.sender = sender
        self._stop = threading.Event()
        self._threads = []

    def start(self):
        self.outbox.recover_stale(0)  # at startup nothing is legitimately in flight
        for i in range(self.workers):
            t = threading.Thread(target=self._loop, name=f"webhook-{i}", daemon=True)
            t.start()
            self._threads.append(t)
        t = threading.Thread(target=self._reaper, name="webhook-reaper", daemon=True)
        t.start()
        self._threads.append(t)

    def stop(self, join_timeout=15):
        self._stop.set()
        for t in self._threads:
            t.join(join_timeout)

    def _reaper(self):
        while not self._stop.wait(max(1.0, self.stale_after / 4)):
            self.outbox.recover_stale(self.stale_after)

    def _loop(self):
        while not self._stop.is_set():
            if not self.deliver_one():
                self._stop.wait(self.poll_interval)

    def deliver_one(self):
        rows = self.outbox.claim(1)
        if not rows:
            return False
        row = rows[0]
        import json
        headers = {"Content-Type": "application/json", "Idempotency-Key": row["id"]}
        try:
            status = self.sender(row["url"], json.dumps(row["payload"]).encode(), headers, self.timeout)
            if 200 <= status < 300:
                self.outbox.mark_done(row["id"])
            else:
                self.outbox.mark_failed(row["id"], f"HTTP {status}", self.max_attempts, self.backoff_base)
        except Exception as e:  # timeouts, connection errors, HTTPError
            self.outbox.mark_failed(row["id"], repr(e), self.max_attempts, self.backoff_base)
        return True
