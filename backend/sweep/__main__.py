"""`python -m sweep` : même point d'entrée que la commande installée."""

import sys

from sweep.cli import main

sys.exit(main())
