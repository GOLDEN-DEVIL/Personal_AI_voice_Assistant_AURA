"""Module execution entry point for 'python -m aura'."""

from __future__ import annotations

import sys
from aura.app import main

if __name__ == "__main__":
    sys.exit(main())
