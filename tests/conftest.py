"""letz test configuration."""

import sys
from pathlib import Path

# Ensure src package is importable
src = Path(__file__).parent.parent / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))