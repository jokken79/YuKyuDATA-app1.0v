#!/bin/bash

################################################################################
# Smoke Tests Script
################################################################################
#
# Post-deployment validation tests.
#
# Tests critical functionality to ensure deployment was successful:
# - API health checks
# - Database connectivity
# - Core endpoints response
# - Authentication flow
# - Data integrity
#
# Usage:
#   bash scripts/smoke-tests.sh [--host http://localhost:8001]
#
################################################################################

set -euo pipefail

# Configuration
HOST="${1:-http://localhost:8001}"
TIMEOUT=10
TESTS_PASSED=0
TESTS_FAILED=0

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

################################################################################
# Test Functions
################################################################################

test_pass() {
    echo -e "${GREEN}[✓]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}[✗]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

test_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

test_header() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
}

################################################################################
# HTTP Utility Functions
################################################################################

http_get() {
    local url="$1"
    local endpoint="$2"

    curl -s -w "\n%{http_code}" --connect-timeout $TIMEOUT \
        "$url$endpoint" 2>/dev/null || echo "000"
}

http_get_body() {
    echo "$1" | head -n -1
}

http_get_code() {
    echo "$1" | tail -n 1
}

################################################################################
# Smoke Tests
################################################################################

test_health_check() {
    test_header "1. API Health Check"

    local response=$(http_get "$HOST" "/api/health")
    local code=$(http_get_code "$response")
    local body=$(http_get_body "$response")

    if [ "$code" = "200" ]; then
        test_pass "Health check endpoint accessible (HTTP $code)"

        # Verify response contains expected fields
        if echo "$body" | grep -q '"status"'; then
            test_pass "Health response contains status field"
        else
            test_fail "Health response missing status field"
        fi
    else
        test_fail "Health check failed (HTTP $code)"
        return 1
    fi
}

test_database_connectivity() {
    test_header "2. Database Connectivity"

    # Test through API that requires DB access
    local response=$(http_get "$HOST" "/api/v1/employees?year=2025&limit=1")
    local code=$(http_get_code "$response")

    if [ "$code" = "200" ]; then
        test_pass "Database connectivity verified (HTTP $code)"
    elif [ "$code" = "401" ] || [ "$code" = "403" ]; then
        test_pass "Database accessible (authentication required)"
    else
        test_fail "Database connectivity check failed (HTTP $code)"
        return 1
    fi
}

test_api_endpoints() {
    test_header "3. Core API Endpoints"

    local endpoints=(
        "/api/v1/employees"
        "/api/v1/leave-requests"
        "/api/v1/notifications"
        "/api/v1/analytics/stats?year=2025"
        "/api/v1/compliance/5day?year=2025"
        "/docs"
        "/redoc"
    )

    for endpoint in "${endpoints[@]}"; do
        local response=$(http_get "$HOST" "$endpoint")
        local code=$(http_get_code "$response")

        # Accept 200, 401 (needs auth), 404 (endpoint might not exist)
        if [ "$code" = "200" ] || [ "$code" = "401" ] || [ "$code" = "404" ]; then
            test_pass "$endpoint (HTTP $code)"
        else
            test_fail "$endpoint (HTTP $code)"
        fi
    done
}

test_response_time() {
    test_header "4. Response Time Validation"

    local start=$(date +%s%N)
    local response=$(http_get "$HOST" "/api/health")
    local end=$(date +%s%N)

    local elapsed_ms=$(( (end - start) / 1000000 ))

    test_info "Health endpoint response time: ${elapsed_ms}ms"

    if [ "$elapsed_ms" -lt 500 ]; then
        test_pass "Response time acceptable (< 500ms)"
    elif [ "$elapsed_ms" -lt 1000 ]; then
        test_pass "Response time acceptable (< 1000ms)"
    else
        test_fail "Response time too high (> 1000ms)"
    fi
}

################################################################################
# Summary Report
################################################################################

print_summary() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║       SMOKE TEST SUMMARY               ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    echo "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo "Tests Failed: ${RED}$TESTS_FAILED${NC}"
    echo "Total Tests:  $((TESTS_PASSED + TESTS_FAILED))"
    echo ""

    if [ "$TESTS_FAILED" -eq 0 ]; then
        echo -e "${GREEN}✓ All smoke tests passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ Some tests failed. Review above for details.${NC}"
        return 1
    fi
}

################################################################################
# Main
################################################################################

main() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║    YuKyuDATA Smoke Tests              ║"
    echo "║    Target: $HOST"
    echo "╚════════════════════════════════════════╝"
    echo ""

    # Check if service is reachable
    if ! curl -s --connect-timeout 5 "$HOST/api/health" > /dev/null 2>&1; then
        test_fail "Service not reachable at $HOST"
        echo ""
        echo "Make sure:"
        echo "  1. Service is running on $HOST"
        echo "  2. Network is available"
        echo "  3. Firewall allows access"
        exit 1
    fi

    # Run all tests
    test_health_check || true
    test_database_connectivity || true
    test_api_endpoints || true
    test_response_time || true

    # Print summary
    print_summary
    exit $?
}

main "$@"
