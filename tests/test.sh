#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo
echo "=========================================="
echo " NEXUS AUTOFORGE TEST SUITE"
echo "=========================================="

python -m py_compile \
    nexus.py \
    nexuslib/core.py

echo "✅ Python syntax"

bash -n bin/nexus
bash -n bin/repair-bot
bash -n tests/test.sh

echo "✅ Bash syntax"

python nexus.py selftest |
    grep -q "SELFTEST PASS"

echo "✅ Selftest"

python nexus.py create \
    "AutoForge Test Project" |
    jq -e '.name == "autoforge-test-project"' \
    >/dev/null

echo "✅ Architect"

SECURITY="$(
    python nexus.py audit
)"

printf '%s\n' "$SECURITY" |
    jq -e '.security == "PASS"' \
    >/dev/null

echo "✅ Security"

STATUS="$(
    python nexus.py status
)"

printf '%s\n' "$STATUS" |
    jq -e \
    '.service == "mikis13-nexus"' \
    >/dev/null

echo "✅ Status"

echo
echo "=========================================="
echo "✅ ALLE LOKALE TESTS PASS"
echo "=========================================="
