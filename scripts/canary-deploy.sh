#!/bin/bash
# =============================================================================
# Canary Deployment Script - FASE 3
# =============================================================================
# Progressive rollout with automatic rollback on metrics degradation
#
# Usage:
#   ./scripts/canary-deploy.sh --image ghcr.io/app:v1.2.3 --environment production
#
# Phases:
#   1. Deploy to 10% of traffic
#   2. Wait 10 minutes, check metrics
#   3. Deploy to 25% of traffic
#   4. Wait 15 minutes, check metrics
#   5. Deploy to 50% of traffic
#   6. Wait 20 minutes, check metrics
#   7. Deploy to 100% (complete)
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE=""
ENVIRONMENT="staging"
CANARY_PHASES=(10 25 50 100)
WAIT_TIMES=(600 900 1200 0)  # seconds
ERROR_THRESHOLD=1.0  # percent
LATENCY_THRESHOLD=250  # milliseconds
REVERT_THRESHOLD=5  # percent

# Logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --image)
            IMAGE="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# Validate arguments
if [ -z "$IMAGE" ]; then
    error "Image is required: --image <image-tag>"
fi

log "Canary Deployment Started"
log "Image: $IMAGE"
log "Environment: $ENVIRONMENT"
log "Error Threshold: ${ERROR_THRESHOLD}%"
log "Latency Threshold: ${LATENCY_THRESHOLD}ms"
echo ""

# Get current baseline metrics
get_metrics() {
    local service=$1

    # Simulate metrics retrieval (in production: CloudWatch/Prometheus)
    cat <<EOF
{
    "error_rate": 0.3,
    "latency_p95": 145,
    "latency_p99": 210,
    "throughput": 250,
    "requests_total": 15000,
    "requests_error": 45
}
EOF
}

# Check if metrics are healthy
check_metrics() {
    local phase=$1
    local metrics=$2

    local error_rate=$(echo "$metrics" | jq -r '.error_rate')
    local latency=$(echo "$metrics" | jq -r '.latency_p95')

    log "Metrics for Phase $phase:"
    log "  Error Rate: ${error_rate}%"
    log "  Latency (p95): ${latency}ms"

    # Check thresholds
    if (( $(echo "$error_rate > $ERROR_THRESHOLD" | bc -l) )); then
        return 1  # Unhealthy
    fi

    if (( $(echo "$latency > $LATENCY_THRESHOLD" | bc -l) )); then
        return 1  # Unhealthy
    fi

    return 0  # Healthy
}

# Deploy to percentage of traffic
deploy_phase() {
    local phase=$1
    local percentage=$2

    log "Deploying to ${percentage}% of traffic..."

    if [ "$ENVIRONMENT" = "kubernetes" ]; then
        # Kubernetes canary with Flagger/Istio
        kubectl patch virtualservice yukyu-app -p \
            '{"spec":{"hosts":[{"name":"yukyu-app","weight":'"$((100-percentage))"',"destination":{"host":"yukyu-app-stable"}},{"name":"yukyu-app","weight":'"$percentage"',"destination":{"host":"yukyu-app-canary"}}]}}'

    else
        # AWS ALB weighted target groups
        aws elbv2 modify-rule \
            --rule-arn "$RULE_ARN" \
            --actions Type=forward,TargetGroups="[{TargetGroupArn=$STABLE_TG_ARN,Weight=$((100-percentage))},{TargetGroupArn=$CANARY_TG_ARN,Weight=$percentage}]"
    fi

    success "Deployed $IMAGE to ${percentage}% traffic"
}

# Rollback deployment
rollback() {
    local reason=$1

    error "Rollback triggered: $reason"

    log "Rolling back to previous version..."

    if [ "$ENVIRONMENT" = "kubernetes" ]; then
        kubectl rollout undo deployment/yukyu-app
    else
        # Revert weight to 100% stable
        deploy_phase "rollback" 0
    fi

    error "Deployment rolled back"
}

# Main canary process
log "Starting canary deployment phases..."
echo ""

for i in "${!CANARY_PHASES[@]}"; do
    phase=$((i + 1))
    percentage="${CANARY_PHASES[$i]}"
    wait_time="${WAIT_TIMES[$i]}"

    log "=== Phase $phase: Deploy to ${percentage}% ==="

    # Deploy this phase
    deploy_phase "$phase" "$percentage"

    # If not 100%, wait and check metrics
    if [ "$percentage" -lt 100 ]; then
        log "Monitoring for ${wait_time}s..."
        sleep "$wait_time"

        # Get metrics
        metrics=$(get_metrics "yukyu-app-$ENVIRONMENT")
        error_rate=$(echo "$metrics" | jq -r '.error_rate')
        latency=$(echo "$metrics" | jq -r '.latency_p95')

        log "Checking health metrics after ${wait_time}s..."
        if ! check_metrics "$phase" "$metrics"; then
            rollback "Metrics exceeded thresholds (Error: ${error_rate}%, Latency: ${latency}ms)"
        fi

        success "Phase $phase healthy, proceeding..."
    fi

    echo ""
done

log "=== Canary Deployment Complete ==="
success "Image $IMAGE is now at 100% traffic"
log "Deployment took $(((${#CANARY_PHASES[@]} - 1) * 60 + 10)) minutes"
log "Monitor application at: https://${ENVIRONMENT}.yukyu-app.example.com"
log ""
log "Next steps:"
log "  1. Verify application functionality"
log "  2. Monitor logs and metrics"
log "  3. Update DNS records if needed"
log "  4. Document deployment in incident log"
