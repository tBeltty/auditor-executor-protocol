"""Background dispatcher: claims due outbox rows and delivers them with retry/backoff."""
import threading
import time
from concurrent.futures import ThreadPoolExecutor


class Dispatcher:
    def __init__(self, outbox, sender, workers=64, per_host=8, max_attempts=8,
                 base_backoff=1.0, max_backoff=300.0, poll_interval=0.05, clock=time.time):
        self.outbox = outbox
        self.sender = sender          # callable(row) -> None; raises on failure
        self.workers = workers
        self.per_host = per_host
        self.max_attempts = max_attempts
        self.base_backoff = base_backoff
        self.max_backoff = max_backoff
        self.poll_interval = poll_interval
        self.clock = clock
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="webhook")
        self._lock = threading.Lock()
        self._host_inflight = {}
        self._inflight = 0
        self._stop = threading.Event()
        self._thread = None

    def backoff(self, attempts):
        return min(self.max_backoff, self.base_backoff * (2 ** (attempts - 1)))

    def _deliver(self, row):
        try:
            try:
                self.sender(row)
            except Exception as exc:  # delivery failure: reschedule or give up visibly
                attempts = row["attempts"] + 1
                err = f"{type(exc).__name__}: {exc}"[:500]
                if attempts >= self.max_attempts:
                    self.outbox.mark_dead(row["id"], err)
                else:
                    self.outbox.mark_retry(row["id"], self.clock() + self.backoff(attempts), err)
            else:
                self.outbox.mark_done(row["id"])
        finally:
            with self._lock:
                self._inflight -= 1
                self._host_inflight[row["host"]] -= 1

    def run_once(self):
        """Claim and submit one batch. Returns number of rows submitted."""
        with self._lock:
            free = self.workers - self._inflight
            full = [h for h, n in self._host_inflight.items() if n >= self.per_host]
        if free <= 0:
            return 0
        rows = self.outbox.claim(free, exclude_hosts=full, now=self.clock())
        submitted = 0
        for row in rows:
            with self._lock:
                n = self._host_inflight.get(row["host"], 0)
                over = n >= self.per_host
                if not over:
                    self._host_inflight[row["host"]] = n + 1
                    self._inflight += 1
            if over:
                # Release the lease without spending an attempt; retry shortly.
                self.outbox._update(
                    "UPDATE webhook_outbox SET status='pending', next_attempt_at=? WHERE id=?",
                    (self.clock() + 0.2, row["id"]))
                continue
            self._pool.submit(self._deliver, row)
            submitted += 1
        return submitted

    def _loop(self):
        while not self._stop.is_set():
            try:
                n = self.run_once()
            except Exception:
                n = 0
            if n == 0:
                self._stop.wait(self.poll_interval)

    def start(self):
        self._thread = threading.Thread(target=self._loop, name="webhook-dispatcher", daemon=True)
        self._thread.start()

    def stop(self, wait=True):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._pool.shutdown(wait=wait, cancel_futures=True)
