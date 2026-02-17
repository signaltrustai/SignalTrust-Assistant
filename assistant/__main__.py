"""OmniJARVIS — Entry point when run as ``python -m assistant``."""

import sys

from assistant.cli import main

if __name__ == "__main__":
    sys.exit(main())
