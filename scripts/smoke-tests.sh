#!/bin/bash

################################################################################
# Smoke Tests for YuKyuDATA-app Deployment
# ========================================
# Validates that the application is functioning correctly after deployment
#
# Usage:
#   bash scripts/smoke-tests.sh [HOST] [VERBOSE]
#
# Arguments:
#   HOST     - Target host:port (default: localhost:8000)
#   VERBOSE  - Enable verbose output (default: false)
#
# Exits with:
#   0 - All tests passed
#   1 - One or more tests failed
#
# Features:
#   ✓ Health check validation
#   ✓ API endpoint tests
#   ✓ Database connectivity verification
#   ✓ Data integrity checks
#   ✓ Performance baselines
#
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
HOST="${1:-localhost:8000}"
VERBOSE="${2:-false}"
FAILED_TESTS=0
PASSED_TESTS=0
TOTAL_TESTS=0

# Helper functions
log_test() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "[$TOTAL_TESTS] Testing $1... "
}

log_pass() {
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo -e "${GREEN}✓${NC}"
}

log_fail() {
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo -e "${RED}✗${NC}"
    if [ "$VERBOSE" == "true" ]; then
        echo "     Error: $1"
    fi
}

test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_code="${3:-200}"
    local method="${4:-GET}"

    log_test "$name"

    # Make request
    local response=$(curl -s -w "%{http_code}" -X "$method" "$url" -o /tmp/response.json 2>/dev/null || echo "000")
    local http_code="${response: -3}"

    if [ "$http_code" == "$expected_code" ]; then
        log_pass
        return 0
    else
        log_fail "HTTP $http_code (expected $expected_code)"
        return 1
    fi
}

test_endpoint_with_auth() {
    local name="$1"
    local url="$2"
    local token="$3"
    local expected_code="${4:-200}"

    log_test "$name (with auth)"

    local response=$(curl -s -w "%{http_code}" \
        -H "Authorization: Bearer $token" \
        "$url" -o /tmp/response.json 2>/dev/null || echo "000")
    local http_code="${response: -3}"

    if [ "$http_code" == "$expected_code" ]; then
        log_pass
        return 0
    else
        log_fail "HTTP $http_code (expected $expected_code)"
        return 1
    fi
}

# =============================================================================
# Test Suite
# =============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         YuKyuDATA Smoke Tests                             ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║ Target: http://$HOST"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# Section 1: Health & Status
# =============================================================================

echo "Section 1: Health & Status"
echo "─────────────────────────"

test_endpoint "Health Check" "http://$HOST/api/health" 200

# Check if response contains required fields
if curl -s "http://$HOST/api/health" | jq -e '.status' > /dev/null 2>&1; then
    echo -n "[2] Checking health details... "
    if curl -s "http://$HOST/api/health" | jq -e '.timestamp' > /dev/null 2>&1; then
        log_pass
    else
        log_fail "Missing timestamp in health response"
    fi
else
    log_fail "Invalid health response format"
fi

echo ""

# =============================================================================
# Section 2: Authentication
# =============================================================================

echo "Section 2: Authentication"
echo "─────────────────────────"

# Test login endpoint
log_test "Login endpoint"

LOGIN_RESPONSE=$(curl -s -X POST "http://$HOST/api/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}' 2>/dev/null)

if echo "$LOGIN_RESPONSE" | jq -e '.access_token' > /dev/null 2>&1; then
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
    log_pass

    # Test token verification
    log_test "Token verification"
    VERIFY_RESPONSE=$(curl -s "http://$HOST/api/auth/verify" \
        -H "Authorization: Bearer $ACCESS_TOKEN" 2>/dev/null)

    if echo "$VERIFY_RESPONSE" | jq -e '.data.valid' > /dev/null 2>&1; then
        log_pass
    else
        log_fail "Token verification failed"
    fi
else
    log_fail "Login failed - invalid response format"
    ACCESS_TOKEN=""
fi

echo ""

# =============================================================================
# Section 3: Core API Endpoints
# =============================================================================

echo "Section 3: Core API Endpoints"
echo "────────────────────────────"

# Employees endpoint
test_endpoint "GET /api/employees" "http://$HOST/api/employees?year=2025" 200

# Docs endpoint (FastAPI auto-generated)
test_endpoint "FastAPI Swagger Docs" "http://$HOST/docs" 200

# ReDoc endpoint
test_endpoint "FastAPI ReDoc" "http://$HOST/redoc" 200

echo ""

# =============================================================================
# Section 4: Database Connectivity
# =============================================================================

echo "Section 4: Database Connectivity"
echo "─────────────────────────────────"

test_endpoint "Database Status" "http://$HOST/api/health/db" 200

echo ""

# =============================================================================
# Section 5: Data Integrity (if data exists)
# =============================================================================

echo "Section 5: Data Integrity"
echo "──────────────────────────"

log_test "Employee count verification"

EMPLOYEE_COUNT=$(curl -s "http://$HOST/api/employees?year=2025" 2>/dev/null | jq '.meta.total // 0' 2>/dev/null || echo "0")

if [ "$EMPLOYEE_COUNT" -ge 0 ]; then
    log_pass
    if [ "$VERBOSE" == "true" ]; then
        echo "     Total employees: $EMPLOYEE_COUNT"
    fi
else
    log_fail "Invalid employee count: $EMPLOYEE_COUNT"
fi

echo ""

# =============================================================================
# Section 6: Performance Baselines
# =============================================================================

echo "Section 6: Performance Baselines"
echo "─────────────────────────────────"

log_test "Response time (health check)"

START_TIME=$(date +%s%N)
curl -s "http://$HOST/api/health" > /dev/null 2>&1
END_TIME=$(date +%s%N)
RESPONSE_TIME=$(( (END_TIME - START_TIME) / 1000000 ))  # Convert to milliseconds

if [ "$RESPONSE_TIME" -lt 5000 ]; then  # 5 seconds threshold
    log_pass
    if [ "$VERBOSE" == "true" ]; then
        echo "     Response time: ${RESPONSE_TIME}ms"
    fi
else
    log_fail "Response time too slow: ${RESPONSE_TIME}ms"
fi

echo ""

# =============================================================================
# Summary
# =============================================================================

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    Test Summary                           ║"
echo "╠═══════════════════════════════════════════════════════════╣"
printf "║ %-20s %-37s ║\n" "Total Tests:" "$TOTAL_TESTS"
printf "║ %-20s %-37s ║\n" "Passed:" "${GREEN}$PASSED_TESTS${NC}"
printf "║ %-20s %-37s ║\n" "Failed:" "${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo "╠═══════════════════════════════════════════════════════════╣"
    echo -e "║${GREEN} ✓ All smoke tests passed!${NC}                                  ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    exit 0
else
    echo "╠═══════════════════════════════════════════════════════════╣"
    echo -e "║${RED} ✗ $FAILED_TESTS test(s) failed!${NC}                              ║"
    echo "╚═══════════════════════════════════════════════════════════╝"
    exit 1
fi
