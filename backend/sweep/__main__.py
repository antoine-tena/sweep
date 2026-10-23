"""`python -m sweep`: the same entry point as the installed command."""

import sys

from sweep.cli import main

sys.exit(main())
