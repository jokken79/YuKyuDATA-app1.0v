#!/bin/bash

################################################################################
# Blue-Green Rollback Script for YuKyuDATA-app
# ===========================================
# Reverts traffic from current version to previous version
#
# Usage:
#   bash scripts/rollback.sh
#
# Features:
#   ✓ Instant traffic rollback
#   ✓ Preserves both versions for quick re-rollback
#   ✓ Detailed logging
#   ✓ Safety checks
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
COLOR_FILE="/tmp/yukyu-color.txt"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPTS_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs/deployment"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

ROLLBACK_LOG="${LOG_DIR}/rollback-$(date +%Y%m%d_%H%M%S).log"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

# =============================================================================
# Validation
# =============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║      YuKyuDATA Blue-Green Rollback                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

log_info "Starting rollback procedure..."
log_info "Log: $ROLLBACK_LOG"

# Check required tools
for tool in docker curl; do
    if ! command -v "$tool" &> /dev/null; then
        log_error "Required tool not found: $tool"
        exit 1
    fi
done

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    log_error "Docker daemon is not accessible"
    exit 1
fi

# =============================================================================
# Determine Current and Target Colors
# =============================================================================

if [ ! -f "$COLOR_FILE" ]; then
    log_error "Color file not found: $COLOR_FILE"
    log_info "Have you deployed using blue-green deployment?"
    exit 1
fi

CURRENT_COLOR=$(cat "$COLOR_FILE" 2>/dev/null || echo "blue")
TARGET_COLOR=$([[ "$CURRENT_COLOR" == "blue" ]] && echo "green" || echo "blue")

CURRENT_PORT=$([[ "$CURRENT_COLOR" == "blue" ]] && echo "9000" || echo "9001")
TARGET_PORT=$([[ "$TARGET_COLOR" == "blue" ]] && echo "9000" || echo "9001")

CURRENT_CONTAINER="yukyu-$CURRENT_COLOR"
TARGET_CONTAINER="yukyu-$TARGET_COLOR"

log_info "Current color: $CURRENT_COLOR (port $CURRENT_PORT)"
log_info "Target color: $TARGET_COLOR (port $TARGET_PORT)"

# =============================================================================
# Validation Checks
# =============================================================================

log_info "Performing validation checks..."

# Check if target container exists
if ! docker inspect "$TARGET_CONTAINER" > /dev/null 2>&1; then
    log_error "Target container not found: $TARGET_CONTAINER"
    log_info "Available containers:"
    docker ps -a | grep yukyu | grep -v nginx || echo "  (none)"
    exit 1
fi
log_success "Target container exists: $TARGET_CONTAINER"

# Check if target container is running
if ! docker inspect "$TARGET_CONTAINER" --format='{{.State.Running}}' | grep -q true; then
    log_warn "Target container is not running, attempting to start it..."
    if ! docker start "$TARGET_CONTAINER" >> "$ROLLBACK_LOG" 2>&1; then
        log_error "Failed to start target container"
        exit 1
    fi
    sleep 5
    log_success "Target container started"
fi

# Wait for target container to be healthy
log_info "Waiting for target container to become healthy..."
HEALTH_ATTEMPTS=0
MAX_HEALTH_ATTEMPTS=30

while [ $HEALTH_ATTEMPTS -lt $MAX_HEALTH_ATTEMPTS ]; do
    HEALTH_STATUS=$(docker inspect "$TARGET_CONTAINER" --format='{{.State.Health.Status}}' 2>/dev/null || echo "unhealthy")

    if [ "$HEALTH_STATUS" == "healthy" ]; then
        log_success "Target container is healthy"
        break
    fi

    echo -n "." | tee -a "$ROLLBACK_LOG"
    sleep 2
    HEALTH_ATTEMPTS=$((HEALTH_ATTEMPTS + 1))
done

if [ $HEALTH_ATTEMPTS -ge $MAX_HEALTH_ATTEMPTS ]; then
    log_error "Target container failed to become healthy"
    exit 1
fi

# =============================================================================
# Switch Traffic Back
# =============================================================================

log_info "Switching traffic from $CURRENT_PORT to $TARGET_PORT..."

# Check if nginx container exists
if docker inspect yukyu-nginx > /dev/null 2>&1; then
    NGINX_CONFIG=$(cat <<EOF
upstream backend {
    server 127.0.0.1:${TARGET_PORT};
}

# Keep connection alive to backend
keepalive 64;
EOF
)

    if ! docker exec yukyu-nginx bash -c "cat > /etc/nginx/conf.d/upstream.conf <<'EOFNGINX'\n${NGINX_CONFIG}\nEOFNGINX\n" >> "$ROLLBACK_LOG" 2>&1; then
        log_error "Failed to update nginx config"
        exit 1
    fi

    if ! docker exec yukyu-nginx nginx -s reload >> "$ROLLBACK_LOG" 2>&1; then
        log_error "Failed to reload nginx"
        exit 1
    fi

    log_success "Nginx traffic switched to port $TARGET_PORT"
else
    log_warn "Nginx container not found"
fi

# =============================================================================
# Update State
# =============================================================================

# Save rolled-back color
echo "$TARGET_COLOR" > "$COLOR_FILE"
log_info "Color state updated: $TARGET_COLOR"

# =============================================================================
# Verification
# =============================================================================

log_info "Verifying rollback..."

sleep 2

# Test health
HEALTH_TEST=$(curl -s -w "%{http_code}" "http://localhost:9000/api/health" -o /dev/null 2>/dev/null || echo "000")

if [ "${HEALTH_TEST: -3}" == "200" ]; then
    log_success "Health check passed"
else
    log_warn "Health check returned status ${HEALTH_TEST: -3}"
fi

# =============================================================================
# Summary
# =============================================================================

log_success "Rollback completed successfully!"
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                   Rollback Complete                       ║"
echo "╠═══════════════════════════════════════════════════════════╣"
printf "║ %-20s %-37s ║\n" "Rolled back to:" "$TARGET_COLOR"
printf "║ %-20s %-37s ║\n" "Container:" "$TARGET_CONTAINER"
printf "║ %-20s %-37s ║\n" "Port:" "$TARGET_PORT"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

log_info "Current container ($CURRENT_CONTAINER) remains running for quick re-rollback"
log_info "View logs: $ROLLBACK_LOG"

exit 0
