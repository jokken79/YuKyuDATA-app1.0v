#!/bin/bash

################################################################################
# YuKyuDATA Production Rollback Script
################################################################################
#
# Emergency rollback procedure.
#
# Restores the previous stable version:
# - Restores database from backup
# - Switches traffic back to previous version
# - Verifies system health
# - Notifies team
#
# Usage:
#   bash scripts/rollback-production.sh [--deployment-id 20260118_123456]
#
################################################################################

set -euo pipefail

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
DB_BACKUP_PATH="${DB_BACKUP_PATH:-$PROJECT_DIR/backups}"
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
DEPLOYMENT_ID="${1:-latest}"

# Rollback tracking
ROLLBACK_LOG="$PROJECT_DIR/logs/rollback_$(date +%Y%m%d_%H%M%S).log"
ROLLBACK_SUCCESS=true

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

################################################################################
# Logging Functions
################################################################################

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1" | tee -a "$ROLLBACK_LOG"
}

################################################################################
# Slack Notifications
################################################################################

send_slack_notification() {
    local message=$1

    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d @- <<EOF
{
    "attachments": [
        {
            "color": "danger",
            "title": "YuKyuDATA Rollback - MANUAL INTERVENTION",
            "text": "$message",
            "fields": [
                {
                    "title": "Deployment ID",
                    "value": "$DEPLOYMENT_ID",
                    "short": true
                },
                {
                    "title": "Time",
                    "value": "$(date '+%Y-%m-%d %H:%M:%S')",
                    "short": true
                },
                {
                    "title": "Log File",
                    "value": "$ROLLBACK_LOG",
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
# Find Backup
################################################################################

find_backup() {
    log "Looking for backup..."

    if [ "$DEPLOYMENT_ID" = "latest" ]; then
        # Find most recent backup
        local latest=$(ls -t "$DB_BACKUP_PATH"/yukyu_pre_deploy_*.db 2>/dev/null | head -1)

        if [ -z "$latest" ]; then
            log_error "No backups found in $DB_BACKUP_PATH"
            return 1
        fi

        BACKUP_FILE="$latest"
        log_success "Found latest backup: $BACKUP_FILE"
    else
        # Look for specific deployment backup
        BACKUP_FILE="$DB_BACKUP_PATH/yukyu_pre_deploy_${DEPLOYMENT_ID}.db"

        if [ ! -f "$BACKUP_FILE" ]; then
            log_error "Backup not found: $BACKUP_FILE"
            return 1
        fi

        log_success "Found backup: $BACKUP_FILE"
    fi

    return 0
}

################################################################################
# Restore Database
################################################################################

restore_database() {
    log "Restoring database..."

    # Create safety backup of current state
    local safety_backup="$DB_BACKUP_PATH/yukyu_broken_$(date +%Y%m%d_%H%M%S).db"
    if [ -f "$PROJECT_DIR/yukyu.db" ]; then
        log "  Creating safety backup of current state..."
        cp "$PROJECT_DIR/yukyu.db" "$safety_backup"
        log "  Safety backup: $safety_backup"
    fi

    # Restore from backup
    log "  Restoring from backup..."
    if ! cp "$BACKUP_FILE" "$PROJECT_DIR/yukyu.db"; then
        log_error "Database restore failed"
        ROLLBACK_SUCCESS=false
        return 1
    fi

    log_success "Database restored"
    return 0
}

################################################################################
# Restart Application
################################################################################

restart_application() {
    log "Restarting application..."

    cd "$PROJECT_DIR"

    # Stop current containers
    log "  Stopping current containers..."
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true

    sleep 5

    # Start previous version
    log "  Starting previous version..."
    export CONTAINER_PORT=8000
    if ! docker-compose -f docker-compose.prod.yml up -d app > "$ROLLBACK_LOG.docker" 2>&1; then
        log_error "Failed to start application"
        cat "$ROLLBACK_LOG.docker" >> "$ROLLBACK_LOG"
        ROLLBACK_SUCCESS=false
        return 1
    fi

    log_success "Application started"
    return 0
}

################################################################################
# Health Check
################################################################################

health_check_after_rollback() {
    log "Verifying rollback health..."

    local retries=10
    local interval=5

    while [ $retries -gt 0 ]; do
        log "  Health check attempt $((11 - retries))/10..."

        if curl -sf "http://localhost:8000/api/health" > /dev/null 2>&1; then
            log_success "Health check passed"
            return 0
        fi

        retries=$((retries - 1))
        if [ $retries -gt 0 ]; then
            log "  Retrying in ${interval}s..."
            sleep $interval
        fi
    done

    log_error "Health check failed"
    ROLLBACK_SUCCESS=false
    return 1
}

################################################################################
# Verify Data Integrity
################################################################################

verify_data_integrity() {
    log "Verifying data integrity..."

    # Test database queries
    if ! python3 -c "
import sqlite3
try:
    conn = sqlite3.connect('$PROJECT_DIR/yukyu.db', timeout=5)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM employees')
    count = c.fetchone()[0]
    print(f'Employees table: {count} records')
    conn.close()
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
" >> "$ROLLBACK_LOG" 2>&1; then
        log_error "Data integrity check failed"
        ROLLBACK_SUCCESS=false
        return 1
    fi

    log_success "Data integrity verified"
    return 0
}

################################################################################
# Cleanup
################################################################################

cleanup() {
    log "Cleaning up..."

    rm -f "$ROLLBACK_LOG.docker" 2>/dev/null || true

    log_success "Cleanup complete"
}

################################################################################
# Main Rollback Flow
################################################################################

main() {
    log "=========================================="
    log "YuKyuDATA Production Rollback"
    log "=========================================="
    log "Deployment ID: $DEPLOYMENT_ID"
    log "Log file: $ROLLBACK_LOG"

    mkdir -p "$PROJECT_DIR/logs"

    # 1. Find backup
    if ! find_backup; then
        log_error "Rollback FAILED: Backup not found"
        ROLLBACK_SUCCESS=false
    fi

    # 2. Restore database
    if [ "$ROLLBACK_SUCCESS" = true ]; then
        if ! restore_database; then
            log_error "Rollback FAILED: Database restore failed"
            ROLLBACK_SUCCESS=false
        fi
    fi

    # 3. Restart application
    if [ "$ROLLBACK_SUCCESS" = true ]; then
        if ! restart_application; then
            log_error "Rollback FAILED: Application restart failed"
            ROLLBACK_SUCCESS=false
        fi
    fi

    # 4. Health check
    if [ "$ROLLBACK_SUCCESS" = true ]; then
        if ! health_check_after_rollback; then
            log_error "Rollback FAILED: Health check failed"
            ROLLBACK_SUCCESS=false
        fi
    fi

    # 5. Verify data
    if [ "$ROLLBACK_SUCCESS" = true ]; then
        if ! verify_data_integrity; then
            log_error "Rollback FAILED: Data integrity check failed"
            ROLLBACK_SUCCESS=false
        fi
    fi

    # 6. Cleanup
    cleanup

    # Final status
    if [ "$ROLLBACK_SUCCESS" = true ]; then
        log_success "=========================================="
        log_success "Rollback completed successfully!"
        log_success "=========================================="

        send_slack_notification "Rollback completed successfully. System is operational."

        return 0
    else
        log_error "=========================================="
        log_error "Rollback FAILED - MANUAL INTERVENTION REQUIRED"
        log_error "=========================================="

        send_slack_notification "Rollback procedure failed. MANUAL INTERVENTION REQUIRED. Check logs at $ROLLBACK_LOG"

        return 1
    fi
}

# Run main function
main "$@"
exit $?
