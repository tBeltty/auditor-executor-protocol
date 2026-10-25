"""In-process dispatcher: claims outbox rows and POSTs them with a short timeout."""
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import outbox


def http_send(url, body, key, timeout):
    req = urllib.request.Request(
        url, data=body.encode(), method="POST",
        headers={"Content-Type": "application/json", "Idempotency-Key": key})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if not 200 <= resp.status < 300:
            raise RuntimeError("status %s" % resp.status)


class Dispatcher:
    def __init__(self, db_path, send=http_send, workers=32, timeout=3.0,
                 max_attempts=8, base=2.0, lease=None, poll=0.05):
        self.db_path, self.send = db_path, send
        self.timeout, self.max_attempts, self.base = timeout, max_attempts, base
        self.lease = lease if lease is not None else timeout * 3 + 5
        self.poll = poll
        self.pool = ThreadPoolExecutor(max_workers=workers)
        self.workers = workers
        self._inflight = 0
        self._cv = threading.Condition()
        self._stop = threading.Event()
        self._thread = None

    def _deliver(self, item):
        conn = outbox.connect(self.db_path)
        try:
            try:
                self.send(item["url"], item["payload"], item["id"], self.timeout)
            except Exception as e:  # any failure -> retry/dead, never drop
                outbox.mark_failed(conn, item["id"], item["attempts"], repr(e)[:300],
                                   self.max_attempts, self.base)
            else:
                outbox.mark_delivered(conn, item["id"])
        finally:
            conn.close()
            with self._cv:
                self._inflight -= 1
                self._cv.notify_all()

    def run_once(self):
        """Claim up to the free worker capacity; returns number submitted."""
        with self._cv:
            free = self.workers - self._inflight
        if free <= 0:
            return 0
        conn = outbox.connect(self.db_path)
        try:
            items = outbox.claim(conn, limit=free, lease=self.lease)
        finally:
            conn.close()
        for it in items:
            with self._cv:
                self._inflight += 1
            self.pool.submit(self._deliver, it)
        return len(items)

    def _loop(self):
        while not self._stop.is_set():
            if self.run_once() == 0:
                self._stop.wait(self.poll)

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join()
        self.pool.shutdown(wait=True)
