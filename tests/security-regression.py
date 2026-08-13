#!/usr/bin/env python3

from pathlib import Path
import json
import sys

# ------------------------------------------------------------
# PROJECT ROOT AUTO-DETECT
# ------------------------------------------------------------

THIS_FILE = Path(__file__).resolve()
ROOT = THIS_FILE.parent.parent

# Zorg dat imports altijd vanaf de repository-root werken,
# ongeacht vanuit welke directory dit script wordt gestart.
root_string = str(ROOT)

if root_string not in sys.path:
    sys.path.insert(0, root_string)

try:
    from nexuslib.core import security_scan
except Exception as exc:
    print(
        json.dumps(
            {
                "status": "FAIL",
                "gate": "IMPORT",
                "root": str(ROOT),
                "python": sys.executable,
                "error": repr(exc),
            },
            indent=2,
        )
    )
    raise SystemExit(1)

# ------------------------------------------------------------
# SECURITY SCAN
# ------------------------------------------------------------

hits = security_scan()

# core.py bevat de scannerregels zelf.
# Die broncode mag niet als echte credential worden gemarkeerd.
self_hits = []

for hit in hits:
    if isinstance(hit, dict):
        filename = str(hit.get("file", ""))
    else:
        filename = str(hit)

    if filename.endswith("nexuslib/core.py"):
        self_hits.append(hit)

if self_hits:
    print(
        json.dumps(
            {
                "status": "FAIL",
                "gate": "SELF_DETECTION",
                "hits": self_hits,
            },
            indent=2,
            ensure_ascii=False,
        )
    )

    raise SystemExit(1)

print(
    json.dumps(
        {
            "status": "PASS",
            "gate": "SECURITY_REGRESSION",
            "root": str(ROOT),
            "hits": hits,
        },
        indent=2,
        ensure_ascii=False,
    )
)
