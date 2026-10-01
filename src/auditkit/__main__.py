"""Allow ``python -m auditkit``."""

import sys

from .cli import main

sys.exit(main())
