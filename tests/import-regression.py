#!/usr/bin/env python3

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nexuslib.core import (
    security_scan,
    performance_check,
    architecture,
)

assert callable(security_scan)
assert callable(performance_check)
assert callable(architecture)

print("IMPORT REGRESSION PASS")
