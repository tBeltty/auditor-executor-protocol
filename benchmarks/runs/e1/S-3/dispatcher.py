"""Background webhook dispatcher (threads inside the monolith)."""
import threading
import time
import urllib.request

import outbox


def http_post(url, body, webhook_id, timeout):
    req = urllib.request.Request(
        url, data=body.encode(), method="POST",
        headers={"Content-Type": "application/json", "X-Webhook-Id": webhook_id})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        code = resp.status
    if not 200 <= code < 300:
        raise RuntimeError(f"HTTP {code}")


class Dispatcher:
    def __init__(self, db_path, workers=32, http_timeout=5.0, lease=30.0, max_attempts=12,
                 backoff_base=2.0, backoff_cap=900.0, poll_interval=0.1, sender=http_post):
        self.db_path, self.workers = db_path, workers
        self.http_timeout, self.lease = http_timeout, lease
        self.max_attempts, self.base, self.cap = max_attempts, backoff_base, backoff_cap
        self.poll_interval, self.sender = poll_interval, sender
        self._stop = threading.Event()
        self._threads = []
        self._cooldown = {}          # url -> monotonic-free wall time until which it is skipped
        self._cd_lock = threading.Lock()
        self._busy = 0               # claimed rows currently being processed
        self._busy_lock = threading.Lock()
        self._sem = threading.Semaphore(workers)

    def start(self):
        self._stop.clear()
        t = threading.Thread(target=self._loop, name="webhook-claimer", daemon=True)
        t.start()
        self._threads.append(t)

    def stop(self, timeout=10):
        self._stop.set()
        for t in self._threads:
            t.join(timeout)
        self._threads = []

    def _active_cooldowns(self, now):
        with self._cd_lock:
            self._cooldown = {u: t for u, t in self._cooldown.items() if t > now}
            return list(self._cooldown)

    def _loop(self):
        conn = outbox.connect(self.db_path)
        try:
            while not self._stop.is_set():
                free = self.workers - self._busy
                rows = []
                if free > 0:
                    rows = outbox.claim_due(conn, free, self.lease,
                                            skip_urls=self._active_cooldowns(time.time()))
                for r in rows:
                    with self._busy_lock:
                        self._busy += 1
                    threading.Thread(target=self._deliver, args=(r,), daemon=True).start()
                if not rows:
                    self._stop.wait(self.poll_interval)
        finally:
            conn.close()

    def _deliver(self, row):
        conn = outbox.connect(self.db_path)
        try:
            try:
                self.sender(row["url"], row["payload"], row["id"], self.http_timeout)
            except Exception as e:  # timeout, connection error, non-2xx
                status, nxt = outbox.mark_failed(conn, row["id"], repr(e), self.max_attempts,
                                                 self.base, self.cap)
                if status == "pending":
                    with self._cd_lock:
                        self._cooldown[row["url"]] = nxt
            else:
                outbox.mark_delivered(conn, row["id"])
        finally:
            conn.close()
            with self._busy_lock:
                self._busy -= 1
