#!/bin/bash

################################################################################
# Health Check Script for YuKyuDATA-app
# ====================================
# Continuously monitors application health and alerts on failures
#
# Usage:
#   bash scripts/health-check.sh [HOST] [CHECK_INTERVAL] [ALERT_CMD]
#
# Arguments:
#   HOST           - Target host:port (default: localhost:8000)
#   CHECK_INTERVAL - Check interval in seconds (default: 30)
#   ALERT_CMD      - Command to execute on failure (default: log only)
#
# Features:
#   ✓ HTTP health checks
#   ✓ Database connectivity
#   ✓ Disk space monitoring
#   ✓ Memory usage tracking
#   ✓ Custom alert commands
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
CHECK_INTERVAL="${2:-30}"
ALERT_CMD="${3:-}"

# State tracking
LAST_STATUS="healthy"
CONSECUTIVE_FAILURES=0
MAX_FAILURES_BEFORE_ALERT=3

# =============================================================================
# Health Check Functions
# =============================================================================

check_http_health() {
    local url="http://$HOST/api/health"
    local response=$(curl -s -w "%{http_code}" "$url" -o /tmp/health.json 2>/dev/null || echo "000")
    local http_code="${response: -3}"

    if [ "$http_code" == "200" ]; then
        # Verify response contains required fields
        if jq -e '.status' /tmp/health.json > /dev/null 2>&1; then
            echo "ok"
            return 0
        fi
    fi

    echo "failed"
    return 1
}

check_database() {
    local url="http://$HOST/api/health/db"
    local response=$(curl -s -w "%{http_code}" "$url" -o /dev/null 2>/dev/null || echo "000")
    local http_code="${response: -3}"

    if [ "$http_code" == "200" ]; then
        echo "ok"
        return 0
    else
        echo "failed"
        return 1
    fi
}

check_disk_space() {
    # Check if disk usage is > 90%
    local usage=$(df -h / | tail -1 | awk '{print $5}' | sed 's/%//')

    if [ "$usage" -gt 90 ]; then
        echo "high_usage:$usage%"
        return 1
    else
        echo "ok:$usage%"
        return 0
    fi
}

check_memory() {
    # Check available memory
    if command -v free &> /dev/null; then
        local mem_usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')

        if [ "$mem_usage" -gt 85 ]; then
            echo "high_usage:$mem_usage%"
            return 1
        else
            echo "ok:$mem_usage%"
            return 0
        fi
    fi

    echo "ok"
    return 0
}

# =============================================================================
# Alert Functions
# =============================================================================

alert() {
    local severity="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo -e "${RED}[ALERT]${NC} [$severity] [$timestamp] $message"

    # Execute custom alert command if provided
    if [ -n "$ALERT_CMD" ]; then
        eval "$ALERT_CMD '$severity' '$message'" || true
    fi

    # Log to file
    echo "[$severity] [$timestamp] $message" >> /var/log/yukyu-health.log 2>/dev/null || \
        echo "[$severity] [$timestamp] $message" >> ./yukyu-health.log 2>/dev/null || true
}

# =============================================================================
# Main Health Check Loop
# =============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║    YuKyuDATA Health Check Monitor                         ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║ Target: http://$HOST"
echo "║ Interval: ${CHECK_INTERVAL}s"
echo "║ Alerts: $([ -n "$ALERT_CMD" ] && echo 'Enabled' || echo 'Disabled')"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

while true; do
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    # Perform all checks
    HTTP_STATUS=$(check_http_health)
    DB_STATUS=$(check_database)
    DISK_STATUS=$(check_disk_space)
    MEM_STATUS=$(check_memory)

    # Determine overall status
    CURRENT_STATUS="healthy"
    if [ "$HTTP_STATUS" != "ok" ] || [ "$DB_STATUS" != "ok" ]; then
        CURRENT_STATUS="unhealthy"
        CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
    else
        CONSECUTIVE_FAILURES=0
    fi

    # Alert if status changed or too many consecutive failures
    if [ "$CURRENT_STATUS" != "$LAST_STATUS" ]; then
        if [ "$CURRENT_STATUS" == "unhealthy" ]; then
            alert "ERROR" "Application became unhealthy"
        else
            alert "RECOVERY" "Application recovered"
        fi
        LAST_STATUS="$CURRENT_STATUS"
    fi

    if [ $CONSECUTIVE_FAILURES -ge $MAX_FAILURES_BEFORE_ALERT ] && [ "$CURRENT_STATUS" == "unhealthy" ]; then
        alert "CRITICAL" "Multiple consecutive failures detected"
    fi

    # Warn about disk/memory
    if [[ "$DISK_STATUS" == "high_usage"* ]]; then
        alert "WARNING" "High disk usage: $DISK_STATUS"
    fi

    if [[ "$MEM_STATUS" == "high_usage"* ]]; then
        alert "WARNING" "High memory usage: $MEM_STATUS"
    fi

    # Display status
    printf "[$TIMESTAMP] HTTP: %-10s | DB: %-10s | Disk: %-15s | Memory: %-15s\n" \
        "$HTTP_STATUS" "$DB_STATUS" "$DISK_STATUS" "$MEM_STATUS"

    sleep "$CHECK_INTERVAL"
done
