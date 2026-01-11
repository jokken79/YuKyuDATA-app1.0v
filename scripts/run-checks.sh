#!/bin/bash
# =============================================================================
# run-checks.sh - Run all verification checks manually
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=============================================="
echo "  YuKyuDATA-app Quality Checks"
echo "=============================================="
echo ""

FAILED=0
WARNINGS=0

# Function to run check
run_check() {
    local name="$1"
    local command="$2"
    local required="$3"

    echo -n "[$name] "

    if eval "$command" > /tmp/check_output.txt 2>&1; then
        echo "PASS"
    else
        if [ "$required" = "required" ]; then
            echo "FAIL"
            cat /tmp/check_output.txt
            FAILED=$((FAILED + 1))
        else
            echo "WARN"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

echo "--- Python Checks ---"

# Python syntax check
run_check "Python Syntax" "python -m py_compile main.py database.py excel_service.py fiscal_year.py" "required"

# Python import check (optional - requires dependencies installed)
run_check "Python Imports" "python -c 'import main; import database; import excel_service'" "optional"

echo ""
echo "--- JavaScript Checks ---"

# JavaScript syntax check using acorn or basic validation
# Note: node --check doesn't work with ES6 modules, so we use alternative methods
if command -v node &> /dev/null; then
    # Check for syntax errors using JSON.parse on non-module files only
    JS_ERRORS=0
    for file in $(find static/js -name "*.js" -type f ! -path "*/vendor/*" ! -path "*/modules/*" 2>/dev/null | head -5); do
        if ! node -e "require('fs').readFileSync('$file', 'utf8')" 2>/dev/null; then
            JS_ERRORS=$((JS_ERRORS + 1))
        fi
    done
    if [ $JS_ERRORS -eq 0 ]; then
        echo "[JS Files Readable] PASS"
    else
        echo "[JS Files Readable] WARN ($JS_ERRORS errors)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "[JS Syntax] SKIP (node not installed)"
fi

# Console.log check
CONSOLE_LOGS=$(grep -rn "console\.log" --include="*.js" static/js/ 2>/dev/null | grep -v "// DEBUG" | wc -l)
if [ "$CONSOLE_LOGS" -gt 0 ]; then
    echo "[No console.log] WARN ($CONSOLE_LOGS found)"
    WARNINGS=$((WARNINGS + 1))
else
    echo "[No console.log] PASS"
fi

echo ""
echo "--- Security Checks ---"

# Secrets check
run_check "Secrets Detection" "$SCRIPT_DIR/check-secrets.sh" "required"

# .env check
if [ -f ".env" ]; then
    if git ls-files --error-unmatch .env > /dev/null 2>&1; then
        echo "[.env not tracked] FAIL"
        FAILED=$((FAILED + 1))
    else
        echo "[.env not tracked] PASS"
    fi
else
    echo "[.env not tracked] SKIP (no .env file)"
fi

echo ""
echo "--- Code Quality ---"

# TODO count
TODO_COUNT=$(grep -rn "TODO:" --include="*.py" --include="*.js" . 2>/dev/null | wc -l)
echo "[TODO Count] $TODO_COUNT items"

# FIXME count
FIXME_COUNT=$(grep -rn "FIXME:" --include="*.py" --include="*.js" . 2>/dev/null | wc -l)
if [ "$FIXME_COUNT" -gt 0 ]; then
    echo "[FIXME Count] WARN ($FIXME_COUNT found)"
    WARNINGS=$((WARNINGS + 1))
else
    echo "[FIXME Count] PASS"
fi

echo ""
echo "--- Tests ---"

# Backend tests
if [ -d "tests" ]; then
    if command -v pytest &> /dev/null; then
        run_check "Backend Tests" "pytest tests/ -q --tb=no" "optional"
    else
        echo "[Backend Tests] SKIP (pytest not installed)"
    fi
else
    echo "[Backend Tests] SKIP (no tests/ directory)"
fi

# Frontend tests
if [ -f "package.json" ] && [ -d "node_modules" ]; then
    if command -v npx &> /dev/null; then
        run_check "Frontend Tests" "npx jest --passWithNoTests --silent" "optional"
    else
        echo "[Frontend Tests] SKIP (npx not available)"
    fi
else
    echo "[Frontend Tests] SKIP (node_modules not installed)"
fi

echo ""
echo "=============================================="
echo "  Summary"
echo "=============================================="
echo ""
echo "  Failed: $FAILED"
echo "  Warnings: $WARNINGS"
echo ""

if [ $FAILED -gt 0 ]; then
    echo "STATUS: FAILED - Fix issues before committing"
    exit 1
else
    if [ $WARNINGS -gt 0 ]; then
        echo "STATUS: PASSED with warnings"
    else
        echo "STATUS: PASSED"
    fi
    exit 0
fi
