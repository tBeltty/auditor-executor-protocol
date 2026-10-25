"""Allow ``python -m aepkit``."""

import sys

from .cli import main

sys.exit(main())
