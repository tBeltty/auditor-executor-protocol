"""Negative control: make a gateway failure mutate the order (rule 6)."""

import pathlib

P = pathlib.Path("/tmp/aep-lab/pilot/AE-neutral-3/refunds.py")

OLD = '''    except GatewayError:
        raise
'''

NEW = '''    except GatewayError:
        order["refunded"] += amount
        order["status"] = "partially_refunded"
        order["keys"][idempotency_key] = {
            "refund_id": None,
            "amount": amount,
            "status": "partially_refunded",
        }
        raise
'''

source = P.read_text()
if OLD not in source:
    raise SystemExit("anchor missing")
P.write_text(source.replace(OLD, NEW, 1))
