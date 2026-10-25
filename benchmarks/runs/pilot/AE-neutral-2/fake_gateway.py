"""A hand-written test double for the payment gateway.

``gateway.refund(charge_id, amount) -> str`` records every call, returns a
deterministic refund id, and can be told to raise :class:`refunds.GatewayError`
on chosen calls (the call is still recorded, as a real gateway would have been
contacted before failing).
"""

import itertools

from refunds import GatewayError


class FakeGateway:
    """Minimal in-memory gateway used by the unit tests."""

    def __init__(self, prefix="re"):
        self.calls = []            # list of (charge_id, amount) in call order
        self.fail_calls = set()    # 1-based call numbers that raise
        self.fail_all = False
        self.error_message = "gateway declined the refund"
        self._ids = itertools.count(1)
        self._prefix = prefix

    # -- failure configuration ------------------------------------------------
    def fail_on_call(self, number):
        """Make the ``number``-th call (1-based) raise ``GatewayError``."""
        self.fail_calls.add(number)
        return self

    def fail_next_call(self):
        """Make the next call raise ``GatewayError``, later calls succeed."""
        return self.fail_on_call(len(self.calls) + 1)

    def fail_every_call(self):
        """Make every call raise ``GatewayError``."""
        self.fail_all = True
        return self

    # -- gateway API ---------------------------------------------------------
    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        number = len(self.calls)
        if self.fail_all or number in self.fail_calls:
            raise GatewayError(self.error_message)
        return "%s_%04d" % (self._prefix, next(self._ids))

    # -- inspection helpers --------------------------------------------------
    @property
    def call_count(self):
        return len(self.calls)

    @property
    def last_call(self):
        return self.calls[-1] if self.calls else None
