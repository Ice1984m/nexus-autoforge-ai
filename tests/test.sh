#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT"

export PYTHONPATH="$ROOT${PYTHONPATH:+:$PYTHONPATH}"

echo
echo "============================================"
echo " NEXUS AUTOFORGE COMPLETE TEST SUITE"
echo "============================================"

echo
echo "=== PYTHON COMPILE ==="

python -m py_compile \
    nexus.py \
    nexuslib/__init__.py \
    nexuslib/core.py \
    tests/import-regression.py \
    tests/security-regression.py

echo "✅ Python compile"

echo
echo "=== IMPORT REGRESSION ==="

python tests/import-regression.py |
grep -q "IMPORT REGRESSION PASS"

echo "✅ Python imports"

echo
echo "=== SHELL ==="

bash -n bin/nexus
bash -n bin/repair-bot
bash -n tests/test.sh

echo "✅ Bash"

echo
echo "=== NEXUS SELFTEST ==="

python nexus.py selftest |
grep -q "SELFTEST PASS"

echo "✅ Selftest"

echo
echo "=== ARCHITECT ==="

python nexus.py create \
    "AutoForge Test Project" |
jq -e \
    '.name == "autoforge-test-project"' \
>/dev/null

echo "✅ Architect"

echo
echo "=== SECURITY REGRESSION ==="

python tests/security-regression.py |
jq -e \
    '.status == "PASS"' \
>/dev/null

echo "✅ Security regression"

echo
echo "=== SECURITY AUDIT ==="

python nexus.py audit |
tee reports/test-audit.json

jq -e \
    '.security == "PASS"' \
    reports/test-audit.json \
>/dev/null

echo "✅ Security"

echo
echo "=== STATUS ==="

python nexus.py status |
tee reports/test-status.json

jq -e '
    .service == "mikis13-nexus"
    and
    .tests == "PASS"
    and
    .security == "PASS"
' reports/test-status.json \
>/dev/null

echo "✅ Status"

echo
echo "============================================"
echo "✅ ALL NEXUS TEST GATES PASS"
echo "============================================"
