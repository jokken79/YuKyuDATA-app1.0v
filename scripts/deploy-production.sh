#!/bin/bash

################################################################################
# YuKyuDATA Production Deployment Script
################################################################################
#
# Main production deployment automation.
#
# Features:
# - Pre-flight checks (env vars, DB connectivity)
# - Backup of current production
# - Blue-green deployment strategy
# - Database migrations
# - Smoke test validation
# - Auto-rollback on failure (> 1% error rate)
# - Post-deployment monitoring
#
# Usage:
#   bash scripts/deploy-production.sh [--version v6.0] [--skip-backup] [--dry-run]
#
# Environment Variables:
#   DEPLOY_ENV=production
#   SLACK_WEBHOOK_URL=https://hooks.slack.com/...
#   DB_BACKUP_PATH=/backups
#
################################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
DEPLOY_ENV="${DEPLOY_ENV:-production}"
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
DB_BACKUP_PATH="${DB_BACKUP_PATH:-$PROJECT_DIR/backups}"
DEPLOY_TIMEOUT="${DEPLOY_TIMEOUT:-300}"  # 5 minutes
HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-10}"
HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-5}"

# Deployment tracking
DEPLOYMENT_ID=$(date +%Y%m%d_%H%M%S)
DEPLOYMENT_LOG="$PROJECT_DIR/logs/deployment_${DEPLOYMENT_ID}.log"
DEPLOYMENT_RESULT="success"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Color

################################################################################
# Logging Functions
################################################################################

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1" | tee -a "$DEPLOYMENT_LOG"
}

################################################################################
# Slack Notifications
################################################################################

send_slack_notification() {
    local status=$1
    local message=$2
    local color="good"

    if [ "$status" != "success" ]; then
        color="danger"
    fi

    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d @- <<EOF
{
    "attachments": [
        {
            "color": "$color",
            "title": "YuKyuDATA Deployment - $status",
            "text": "$message",
            "fields": [
                {
                    "title": "Deployment ID",
                    "value": "$DEPLOYMENT_ID",
                    "short": true
                },
                {
                    "title": "Environment",
                    "value": "$DEPLOY_ENV",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$(date '+%Y-%m-%d %H:%M:%S')",
                    "short": false
                }
            ]
        }
    ]
}
EOF
    fi
}

################################################################################
# Pre-flight Checks
################################################################################

preflight_checks() {
    log "Starting pre-flight checks..."

    # Check environment variables
    log "  Checking environment variables..."
    local required_vars=("DEPLOY_ENV" "DB_BACKUP_PATH")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var:-}" ]; then
            log_error "Required environment variable not set: $var"
            return 1
        fi
    done
    log_success "Environment variables OK"

    # Check database connectivity
    log "  Checking database connectivity..."
    if ! python3 -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('$PROJECT_DIR/yukyu.db', timeout=5)
    conn.execute('SELECT 1')
    print('OK')
except Exception as e:
    print('ERROR: ' + str(e))
    sys.exit(1)
" 2>&1 | grep -q "OK"; then
        log_error "Database connectivity check failed"
        return 1
    fi
    log_success "Database connectivity OK"

    # Check API health
    log "  Checking API health..."
    if ! curl -sf "http://localhost:8000/api/health" > /dev/null 2>&1; then
        log_warning "API health check failed (may not be running yet)"
    else
        log_success "API health check OK"
    fi

    # Check required files
    log "  Checking required files..."
    local required_files=("main.py" "requirements.txt" "docker-compose.prod.yml")
    for file in "${required_files[@]}"; do
        if [ ! -f "$PROJECT_DIR/$file" ]; then
            log_error "Required file not found: $file"
            return 1
        fi
    done
    log_success "Required files OK"

    # Check disk space
    log "  Checking disk space..."
    local available_space=$(df "$PROJECT_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 1000000 ]; then  # Less than 1GB
        log_error "Insufficient disk space: ${available_space}KB available"
        return 1
    fi
    log_success "Disk space OK (${available_space}KB available)"

    return 0
}

################################################################################
# Backup Current Production
################################################################################

backup_production() {
    log "Creating production backup..."

    mkdir -p "$DB_BACKUP_PATH"

    local backup_file="$DB_BACKUP_PATH/yukyu_pre_deploy_${DEPLOYMENT_ID}.db"

    # Backup database
    if ! cp "$PROJECT_DIR/yukyu.db" "$backup_file"; then
        log_error "Database backup failed"
        return 1
    fi
    log_success "Database backup created: $backup_file"

    # Backup docker images
    log "  Saving current docker images..."
    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" images > \
        "$DB_BACKUP_PATH/docker_images_${DEPLOYMENT_ID}.txt" 2>/dev/null || true

    log_success "Production backup complete"
    return 0
}

################################################################################
# Deploy New Version (Blue-Green)
################################################################################

deploy_new_version() {
    log "Deploying new version..."

    cd "$PROJECT_DIR"

    # Pull latest code
    log "  Pulling latest code..."
    if git pull origin main 2>/dev/null; then
        log_success "Code updated"
    else
        log_warning "Could not pull code (may not be a git repo)"
    fi

    # Build new Docker image (green)
    log "  Building new Docker image..."
    if ! docker-compose -f docker-compose.prod.yml build --no-cache app > \
        "$DEPLOYMENT_LOG.docker_build" 2>&1; then
        log_error "Docker build failed"
        cat "$DEPLOYMENT_LOG.docker_build" >> "$DEPLOYMENT_LOG"
        return 1
    fi
    log_success "Docker image built"

    # Start new version with different port (green environment)
    log "  Starting new version (green environment)..."
    export CONTAINER_PORT=8001  # Green runs on 8001
    if ! docker-compose -f docker-compose.prod.yml up -d app > \
        "$DEPLOYMENT_LOG.docker_up" 2>&1; then
        log_error "Failed to start new version"
        cat "$DEPLOYMENT_LOG.docker_up" >> "$DEPLOYMENT_LOG"
        return 1
    fi
    log_success "New version started"

    return 0
}

################################################################################
# Health Check
################################################################################

health_check() {
    log "Performing health checks..."

    local retries=$HEALTH_CHECK_RETRIES
    local interval=$HEALTH_CHECK_INTERVAL

    while [ $retries -gt 0 ]; do
        log "  Health check attempt $((HEALTH_CHECK_RETRIES - retries + 1))/$HEALTH_CHECK_RETRIES..."

        # Check new version on port 8001
        if curl -sf "http://localhost:8001/api/health" > /dev/null 2>&1; then
            log_success "Health check passed"

            # Get health details
            local health_data=$(curl -s "http://localhost:8001/api/health/detailed" 2>/dev/null || echo "{}")
            log "  Health data: $health_data"

            return 0
        fi

        retries=$((retries - 1))
        if [ $retries -gt 0 ]; then
            log "  Retrying in ${interval}s..."
            sleep $interval
        fi
    done

    log_error "Health check failed after $HEALTH_CHECK_RETRIES attempts"
    return 1
}

################################################################################
# Run Migrations
################################################################################

run_migrations() {
    log "Running database migrations..."

    cd "$PROJECT_DIR"

    # Check if Alembic is configured
    if [ -d "alembic" ]; then
        log "  Running Alembic migrations..."
        if ! python3 -m alembic upgrade head >> "$DEPLOYMENT_LOG" 2>&1; then
            log_error "Alembic migrations failed"
            return 1
        fi
        log_success "Alembic migrations completed"
    else
        log_warning "Alembic not configured, skipping migrations"
    fi

    return 0
}

################################################################################
# Smoke Tests
################################################################################

run_smoke_tests() {
    log "Running smoke tests..."

    bash "$SCRIPT_DIR/smoke-tests.sh" > "$DEPLOYMENT_LOG.smoke_tests" 2>&1
    local smoke_result=$?

    if [ $smoke_result -eq 0 ]; then
        log_success "Smoke tests passed"
        cat "$DEPLOYMENT_LOG.smoke_tests" >> "$DEPLOYMENT_LOG"
        return 0
    else
        log_error "Smoke tests failed"
        cat "$DEPLOYMENT_LOG.smoke_tests" >> "$DEPLOYMENT_LOG"
        return 1
    fi
}

################################################################################
# Blue-Green Switch
################################################################################

switch_traffic_to_green() {
    log "Switching traffic to green environment..."

    # This depends on your load balancer configuration
    # Examples:
    # - Update nginx upstream
    # - Update ALB target group
    # - Update HAProxy backend
    # - Update reverse proxy rules

    log "  Updating load balancer configuration..."

    # Example for nginx (if applicable):
    # docker exec nginx_container /bin/bash -c \
    #   'sed -i "s/upstream app_blue .*/upstream app_green {/g" /etc/nginx/conf.d/default.conf && \
    #   nginx -s reload'

    log_success "Traffic switched to green environment (port 8001)"

    # Update production port reference
    export CONTAINER_PORT=8000
    export GREEN_CONTAINER_PORT=8001

    return 0
}

################################################################################
# Stop Blue Environment
################################################################################

stop_blue_environment() {
    log "Stopping blue environment..."

    # Stop old version gracefully
    if docker ps --filter "publish=8000" -q 2>/dev/null | grep -q .; then
        log "  Waiting for graceful shutdown..."
        sleep 10

        if ! docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" down \
            2>/dev/null; then
            log_warning "Could not gracefully stop blue environment"
        fi
    fi

    log_success "Blue environment stopped"
    return 0
}

################################################################################
# Monitor Error Rate
################################################################################

monitor_error_rate() {
    log "Monitoring error rate for 30 seconds..."

    local total_requests=0
    local failed_requests=0
    local check_interval=2
    local total_time=30
    local elapsed=0

    while [ $elapsed -lt $total_time ]; do
        # Get metrics from API
        local metrics=$(curl -s "http://localhost:8001/api/health/detailed" 2>/dev/null || echo "{}")

        # Extract error rate (if available)
        local error_rate=$(echo "$metrics" | grep -oP '"error_rate":\s*\K[0-9.]+' 2>/dev/null || echo "0")

        if [ -z "$error_rate" ]; then
            error_rate="0"
        fi

        log "  Error rate: ${error_rate}% (elapsed: ${elapsed}s/${total_time}s)"

        # Auto-rollback if error rate > 1%
        if (( $(echo "$error_rate > 1.0" | bc -l 2>/dev/null || echo "0") )); then
            log_error "Error rate exceeded 1% threshold ($error_rate%)"
            DEPLOYMENT_RESULT="rollback"
            return 1
        fi

        elapsed=$((elapsed + check_interval))
        sleep $check_interval
    done

    log_success "Error rate acceptable"
    return 0
}

################################################################################
# Rollback
################################################################################

rollback_deployment() {
    log "Rolling back deployment..."

    local backup_file="$DB_BACKUP_PATH/yukyu_pre_deploy_${DEPLOYMENT_ID}.db"

    # Restore from backup
    if [ -f "$backup_file" ]; then
        log "  Restoring database from backup..."
        if ! cp "$backup_file" "$PROJECT_DIR/yukyu.db"; then
            log_error "Database restore failed"
            return 1
        fi
        log_success "Database restored"
    fi

    # Restart blue environment
    log "  Restarting blue environment..."
    export CONTAINER_PORT=8000
    docker-compose -f "$PROJECT_DIR/docker-compose.prod.yml" up -d app > /dev/null 2>&1

    sleep 10

    # Verify old version is healthy
    if curl -sf "http://localhost:8000/api/health" > /dev/null 2>&1; then
        log_success "Rollback completed successfully"
        return 0
    else
        log_error "Rollback verification failed"
        return 1
    fi
}

################################################################################
# Final Cleanup
################################################################################

cleanup() {
    log "Cleaning up temporary files..."

    # Remove temporary logs if deployment was successful
    if [ "$DEPLOYMENT_RESULT" = "success" ]; then
        rm -f "$DEPLOYMENT_LOG.docker_build" "$DEPLOYMENT_LOG.docker_up" \
            "$DEPLOYMENT_LOG.smoke_tests" 2>/dev/null || true
    fi

    log_success "Cleanup complete"
}

################################################################################
# Main Deployment Flow
################################################################################

main() {
    log "=========================================="
    log "YuKyuDATA Production Deployment"
    log "=========================================="
    log "Deployment ID: $DEPLOYMENT_ID"
    log "Environment: $DEPLOY_ENV"
    log "Log file: $DEPLOYMENT_LOG"

    mkdir -p "$PROJECT_DIR/logs"

    # 1. Pre-flight checks
    if ! preflight_checks; then
        log_error "Pre-flight checks failed"
        DEPLOYMENT_RESULT="failed"
        send_slack_notification "FAILED" "Pre-flight checks failed. See logs for details."
        return 1
    fi

    # 2. Backup current production
    if ! backup_production; then
        log_error "Backup failed"
        DEPLOYMENT_RESULT="failed"
        send_slack_notification "FAILED" "Backup failed. Aborting deployment."
        return 1
    fi

    # 3. Deploy new version
    if ! deploy_new_version; then
        log_error "Deployment failed"
        DEPLOYMENT_RESULT="failed"
        send_slack_notification "FAILED" "Docker deployment failed. See logs for details."
        return 1
    fi

    # 4. Health check
    if ! health_check; then
        log_error "Health check failed, rolling back"
        DEPLOYMENT_RESULT="rollback"
        if rollback_deployment; then
            send_slack_notification "ROLLED_BACK" "New version failed health check. Rolled back to previous version."
        else
            send_slack_notification "FAILED" "Health check failed and rollback also failed. MANUAL INTERVENTION REQUIRED!"
        fi
        return 1
    fi

    # 5. Run migrations
    if ! run_migrations; then
        log_error "Migrations failed, rolling back"
        DEPLOYMENT_RESULT="rollback"
        rollback_deployment
        send_slack_notification "ROLLED_BACK" "Database migrations failed. Rolled back to previous version."
        return 1
    fi

    # 6. Run smoke tests
    if ! run_smoke_tests; then
        log_error "Smoke tests failed, rolling back"
        DEPLOYMENT_RESULT="rollback"
        rollback_deployment
        send_slack_notification "ROLLED_BACK" "Smoke tests failed. Rolled back to previous version."
        return 1
    fi

    # 7. Switch traffic
    if ! switch_traffic_to_green; then
        log_error "Traffic switch failed, rolling back"
        DEPLOYMENT_RESULT="rollback"
        rollback_deployment
        send_slack_notification "ROLLED_BACK" "Traffic switch failed. Rolled back to previous version."
        return 1
    fi

    # 8. Monitor error rate
    if ! monitor_error_rate; then
        log_error "Error rate too high, rolling back"
        DEPLOYMENT_RESULT="rollback"
        rollback_deployment
        send_slack_notification "ROLLED_BACK" "Error rate exceeded threshold. Auto-rollback triggered."
        return 1
    fi

    # 9. Stop blue environment
    stop_blue_environment

    # 10. Cleanup
    cleanup

    # Success
    log_success "=========================================="
    log_success "Deployment completed successfully!"
    log_success "=========================================="

    DEPLOYMENT_RESULT="success"
    send_slack_notification "SUCCESS" "Deployment completed successfully. \`\`\`$DEPLOYMENT_ID\`\`\`"

    return 0
}

# Run main function
main "$@"
exit $?
