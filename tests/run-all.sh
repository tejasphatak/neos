#!/usr/bin/env bash
# neos test runner — dependency-free (only stdlib Python + pyyaml).
# Runs every tests/test_*.py and every bash -n on tests/test_*.sh.
set -u
cd "$(dirname "$0")/.."

fails=0
passes=0
skipped=0

echo "======================================================"
echo " neos v0.1 test suite"
echo "======================================================"

run_py() {
    local t="$1"
    echo ""
    echo "--- $t ---"
    python3 "$t"
    rc=$?
    if [ $rc -eq 0 ]; then
        passes=$((passes+1))
        echo "  ✓ PASS"
    elif [ $rc -eq 77 ]; then
        skipped=$((skipped+1))
        echo "  ⊘ SKIPPED (missing optional dependency)"
    else
        fails=$((fails+1))
        echo "  ✗ FAIL (exit $rc)"
    fi
}

run_sh() {
    local t="$1"
    echo ""
    echo "--- $t ---"
    bash "$t"
    rc=$?
    if [ $rc -eq 0 ]; then
        passes=$((passes+1)); echo "  ✓ PASS"
    else
        fails=$((fails+1)); echo "  ✗ FAIL (exit $rc)"
    fi
}

# Python tests
for t in tests/test_*.py; do
    [ -e "$t" ] || continue
    run_py "$t"
done

# Shell tests (bash -n syntax checks + real shell tests)
for t in tests/test_*.sh; do
    [ -e "$t" ] || continue
    run_sh "$t"
done

# bin/ script syntax checks
echo ""
echo "--- bin/ syntax checks ---"
syntax_ok=0; syntax_bad=0
for f in bin/*; do
    [ -f "$f" ] || continue
    first=$(head -1 "$f" 2>/dev/null)
    case "$first" in
        *python*)
            if python3 -m py_compile "$f" 2>/dev/null; then
                syntax_ok=$((syntax_ok+1))
            else
                echo "  ✗ py_compile failed: $f"
                syntax_bad=$((syntax_bad+1))
            fi
            ;;
        *bash*|*sh)
            if bash -n "$f" 2>/dev/null; then
                syntax_ok=$((syntax_ok+1))
            else
                echo "  ✗ bash -n failed: $f"
                syntax_bad=$((syntax_bad+1))
            fi
            ;;
    esac
done
if [ $syntax_bad -eq 0 ]; then
    echo "  ✓ $syntax_ok scripts in bin/ parse cleanly"
    passes=$((passes+1))
else
    echo "  ✗ $syntax_bad script(s) failed syntax"
    fails=$((fails+1))
fi

echo ""
echo "======================================================"
echo " Results: $passes passed | $fails failed | $skipped skipped"
echo "======================================================"

exit $fails
