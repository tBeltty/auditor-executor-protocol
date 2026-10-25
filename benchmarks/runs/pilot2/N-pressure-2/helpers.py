"""Shared helpers for the CRM test suite (not a test module itself)."""


class GuardChecks:
    """Assertion helper that tags failures so negative controls can match them."""

    def expect_error(self, tag, exc_type, fn, *args, **kwargs):
        try:
            fn(*args, **kwargs)
        except exc_type:
            return
        except Exception as err:  # noqa: BLE001 - diagnostics only
            self.fail("%s: expected %s, got %s(%s)"
                      % (tag, exc_type.__name__, type(err).__name__, err))
        self.fail("%s: expected %s, nothing raised" % (tag, exc_type.__name__))
