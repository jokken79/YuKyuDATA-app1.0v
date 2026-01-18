#!/bin/bash

################################################################################
# Blue-Green Deployment Script for YuKyuDATA-app
# ============================================
# Implementa deployment sin downtime usando blue-green strategy
#
# Usage:
#   bash scripts/deploy-blue-green.sh [VERSION] [REGISTRY] [IMAGE_NAME]
#
# Environment Variables:
#   DOCKER_REGISTRY - Container registry (default: ghcr.io)
#   IMAGE_NAME - Image name (default: yukyu-app)
#   HEALTH_CHECK_TIMEOUT - Timeout for health checks (default: 60)
#   SMOKE_TEST_TIMEOUT - Timeout for smoke tests (default: 120)
#
# Features:
#   ✓ Zero-downtime deployment
#   ✓ Automatic health checks
#   ✓ Automated smoke tests
#   ✓ 10-minute rollback window
#   ✓ Automatic traffic switching (nginx)
#   ✓ Detailed logging
#
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VERSION="${1:-latest}"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io}"
IMAGE_NAME="${IMAGE_NAME:-yukyu-app}"
HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-60}"
SMOKE_TEST_TIMEOUT="${SMOKE_TEST_TIMEOUT:-120}"
ROLLBACK_WINDOW_SECONDS=600  # 10 minutes

# Paths
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPTS_DIR")"
LOG_DIR="${PROJECT_ROOT}/logs/deployment"
DEPLOYMENT_LOG="${LOG_DIR}/deploy-$(date +%Y%m%d_%H%M%S).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

# =============================================================================
# STEP 1: Validation and Setup
# =============================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║      YuKyuDATA Blue-Green Deployment                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

log_info "Starting deployment..."
log_info "Version: $VERSION"
log_info "Registry: $REGISTRY"
log_info "Image: $IMAGE_NAME"
log_info "Log: $DEPLOYMENT_LOG"

# Check required tools
for tool in docker curl jq; do
    if ! command -v "$tool" &> /dev/null; then
        log_error "Required tool not found: $tool"
        exit 1
    fi
done
log_success "All required tools available"

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    log_error "Docker daemon is not accessible"
    exit 1
fi
log_success "Docker daemon is accessible"

# =============================================================================
# STEP 2: Determine Current Color and Next Color
# =============================================================================

COLOR_FILE="/tmp/yukyu-color.txt"
if [ ! -f "$COLOR_FILE" ]; then
    CURRENT_COLOR="blue"
    echo "$CURRENT_COLOR" > "$COLOR_FILE"
    log_info "Initializing color state: $CURRENT_COLOR"
else
    CURRENT_COLOR=$(cat "$COLOR_FILE" 2>/dev/null || echo "blue")
fi

# Determine next color
if [ "$CURRENT_COLOR" == "blue" ]; then
    NEW_COLOR="green"
    OLD_PORT="9000"
    NEW_PORT="9001"
else
    NEW_COLOR="blue"
    OLD_PORT="9001"
    NEW_PORT="9000"
fi

OLD_CONTAINER="yukyu-$CURRENT_COLOR"
NEW_CONTAINER="yukyu-$NEW_COLOR"

log_info "Current color: $CURRENT_COLOR (port $OLD_PORT)"
log_info "Deploying to: $NEW_COLOR (port $NEW_PORT)"

# =============================================================================
# STEP 3: Pull Latest Image
# =============================================================================

log_info "Pulling Docker image..."
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${VERSION}"

if ! docker pull "$FULL_IMAGE" >> "$DEPLOYMENT_LOG" 2>&1; then
    log_error "Failed to pull image: $FULL_IMAGE"
    exit 1
fi
log_success "Image pulled successfully"

# =============================================================================
# STEP 4: Stop and Remove Existing Container (if any)
# =============================================================================

log_info "Preparing container slot for $NEW_COLOR..."
if docker inspect "$NEW_CONTAINER" > /dev/null 2>&1; then
    log_warn "Container $NEW_CONTAINER exists, stopping it..."
    docker stop "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
    sleep 2
    docker rm "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
fi
log_success "Container slot ready"

# =============================================================================
# STEP 5: Start New Container
# =============================================================================

log_info "Starting new container ($NEW_CONTAINER) on port $NEW_PORT..."

if ! docker run -d \
    --name "$NEW_CONTAINER" \
    -p "127.0.0.1:${NEW_PORT}:8000" \
    --health-cmd="curl -f http://localhost:8000/api/health || exit 1" \
    --health-interval=5s \
    --health-timeout=3s \
    --health-retries=3 \
    --health-start-period=10s \
    -e "DEBUG=false" \
    -e "LOG_LEVEL=INFO" \
    -v yukyu-data:/app/data \
    -v yukyu-logs:/app/logs \
    --restart=unless-stopped \
    "$FULL_IMAGE" >> "$DEPLOYMENT_LOG" 2>&1; then
    log_error "Failed to start container: $NEW_CONTAINER"
    exit 1
fi

log_success "Container started: $NEW_CONTAINER"

# =============================================================================
# STEP 6: Wait for Health Check
# =============================================================================

log_info "Waiting for container to become healthy (timeout: ${HEALTH_CHECK_TIMEOUT}s)..."

HEALTH_CHECK_START=$(date +%s)
CONTAINER_HEALTHY=false

while true; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - HEALTH_CHECK_START))

    if [ $ELAPSED -gt $HEALTH_CHECK_TIMEOUT ]; then
        log_error "Health check timeout after ${HEALTH_CHECK_TIMEOUT}s"
        docker logs "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1
        docker stop "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
        docker rm "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
        exit 1
    fi

    # Check if container is healthy
    HEALTH_STATUS=$(docker inspect "$NEW_CONTAINER" --format='{{.State.Health.Status}}' 2>/dev/null || echo "unhealthy")

    if [ "$HEALTH_STATUS" == "healthy" ]; then
        CONTAINER_HEALTHY=true
        log_success "Container is healthy"
        break
    fi

    echo -n "." | tee -a "$DEPLOYMENT_LOG"
    sleep 2
done

# =============================================================================
# STEP 7: Run Smoke Tests
# =============================================================================

log_info "Running smoke tests against http://localhost:${NEW_PORT}..."

if ! bash "$SCRIPTS_DIR/smoke-tests.sh" "localhost:${NEW_PORT}" >> "$DEPLOYMENT_LOG" 2>&1; then
    log_error "Smoke tests failed"
    log_warn "Rolling back to $OLD_CONTAINER..."
    docker stop "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
    docker rm "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
    exit 1
fi

log_success "All smoke tests passed"

# =============================================================================
# STEP 8: Switch Traffic (Update Nginx/Proxy)
# =============================================================================

log_info "Switching traffic from port $OLD_PORT to $NEW_PORT..."

# Check if nginx container exists
if docker inspect yukyu-nginx > /dev/null 2>&1; then
    NGINX_CONFIG=$(cat <<EOF
upstream backend {
    server 127.0.0.1:${NEW_PORT};
}

# Keep connection alive to backend
keepalive 64;
EOF
)

    if ! docker exec yukyu-nginx bash -c "cat > /etc/nginx/conf.d/upstream.conf <<'EOFNGINX'\n${NGINX_CONFIG}\nEOFNGINX\n" >> "$DEPLOYMENT_LOG" 2>&1; then
        log_error "Failed to update nginx config"
        docker stop "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
        docker rm "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
        exit 1
    fi

    if ! docker exec yukyu-nginx nginx -s reload >> "$DEPLOYMENT_LOG" 2>&1; then
        log_error "Failed to reload nginx"
        docker stop "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
        docker rm "$NEW_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
        exit 1
    fi

    log_success "Nginx traffic switched successfully"
else
    log_warn "Nginx container not found, using direct port exposure"
fi

# Save current color
echo "$NEW_COLOR" > "$COLOR_FILE"
log_info "Color state updated: $NEW_COLOR"

# =============================================================================
# STEP 9: Rollback Window
# =============================================================================

log_info "Deployment successful!"
log_info "Old container ($OLD_CONTAINER) will be kept for $((ROLLBACK_WINDOW_SECONDS / 60)) minutes for rollback"
log_info ""
log_info "╔═══════════════════════════════════════════════════════════╗"
log_info "║ Deployment Complete                                      ║"
log_info "╠═══════════════════════════════════════════════════════════╣"
log_info "║ New container: $NEW_CONTAINER (port $NEW_PORT)              ║"
log_info "║ Old container: $OLD_CONTAINER (port $OLD_PORT) - READY FOR ROLLBACK ║"
log_info "║ Rollback window: $((ROLLBACK_WINDOW_SECONDS / 60)) minutes"
log_info "╚═══════════════════════════════════════════════════════════╝"
log_info ""

# Schedule old container cleanup
log_info "Scheduling cleanup of $OLD_CONTAINER after $((ROLLBACK_WINDOW_SECONDS / 60)) minutes..."

(
    sleep "$ROLLBACK_WINDOW_SECONDS"
    log_info "Cleaning up old container: $OLD_CONTAINER"
    if docker inspect "$OLD_CONTAINER" > /dev/null 2>&1; then
        docker stop "$OLD_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
        docker rm "$OLD_CONTAINER" >> "$DEPLOYMENT_LOG" 2>&1 || true
        log_success "Old container removed: $OLD_CONTAINER"
    fi
) &

log_success "Deployment completed successfully"
log_info "View logs: $DEPLOYMENT_LOG"

exit 0
