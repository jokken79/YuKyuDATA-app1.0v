#!/bin/bash
# PostgreSQL Point-in-Time Recovery (PITR) Procedures
#
# This script provides step-by-step recovery procedures
# for PostgreSQL database restoration

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="${BACKUP_DIR:-.}/backups"
WAL_ARCHIVE_DIR="${WAL_ARCHIVE_DIR:-.}/backups/wal_archive"
POSTGRES_VERSION="${POSTGRES_VERSION:-14}"
POSTGRES_DATA_DIR="/var/lib/postgresql/$POSTGRES_VERSION/main"
POSTGRES_USER="postgres"
RESTORE_DIR="${RESTORE_DIR:-.}/restore_$(date +%Y%m%d_%H%M%S)"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# 1. Pre-Recovery Checks
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if backups exist
    if [ ! -d "$BACKUP_DIR" ]; then
        log_error "Backup directory not found: $BACKUP_DIR"
        return 1
    fi

    if [ ! -d "$WAL_ARCHIVE_DIR" ]; then
        log_error "WAL archive directory not found: $WAL_ARCHIVE_DIR"
        return 1
    fi

    # Check if PostgreSQL is installed
    if ! command -v pg_basebackup &> /dev/null; then
        log_error "PostgreSQL tools not found. Install postgresql-client"
        return 1
    fi

    # Check if pg_restore is available
    if ! command -v pg_restore &> /dev/null; then
        log_warning "pg_restore not found. Install postgresql-$POSTGRES_VERSION"
    fi

    log_success "All prerequisites met"
    return 0
}

# 2. List Available Backups
list_backups() {
    log_info "Available backups:\n"

    if [ ! -f "$BACKUP_DIR/backup_metadata.json" ]; then
        log_warning "No backup metadata found"
        return 1
    fi

    # Show backup files
    if ls -lh "$BACKUP_DIR"/backup_* 2>/dev/null | awk '{print $5, $9}'; then
        log_success "Backups listed"
    else
        log_warning "No backup files found"
    fi
}

# 3. Stop PostgreSQL Service
stop_postgresql() {
    log_info "Stopping PostgreSQL service..."

    if sudo systemctl stop postgresql; then
        log_success "PostgreSQL stopped"
        sleep 2
        return 0
    else
        log_error "Failed to stop PostgreSQL"
        return 1
    fi
}

# 4. Backup Current Data Directory
backup_current_data() {
    log_info "Backing up current data directory..."

    if [ ! -d "$POSTGRES_DATA_DIR" ]; then
        log_warning "PostgreSQL data directory not found: $POSTGRES_DATA_DIR"
        return 0
    fi

    CURRENT_BACKUP="$POSTGRES_DATA_DIR.backup.$(date +%Y%m%d_%H%M%S)"

    if sudo mv "$POSTGRES_DATA_DIR" "$CURRENT_BACKUP"; then
        log_success "Current data backed up: $CURRENT_BACKUP"
        return 0
    else
        log_error "Failed to backup current data directory"
        return 1
    fi
}

# 5. Extract Base Backup
extract_backup() {
    local backup_file=$1

    log_info "Extracting base backup: $backup_file"

    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    mkdir -p "$RESTORE_DIR"

    if [ "${backup_file##*.}" = "gz" ]; then
        if tar -xzf "$backup_file" -C "$RESTORE_DIR"; then
            log_success "Backup extracted"
            return 0
        fi
    else
        if tar -xf "$backup_file" -C "$RESTORE_DIR"; then
            log_success "Backup extracted"
            return 0
        fi
    fi

    log_error "Failed to extract backup"
    return 1
}

# 6. Create Recovery Configuration
create_recovery_config() {
    local recovery_time=$1
    local recovery_conf="$RESTORE_DIR/recovery.conf"

    log_info "Creating recovery configuration..."

    cat > "$recovery_conf" << EOF
# PostgreSQL Recovery Configuration
# Point-in-Time Recovery

recovery_target_timeline = 'latest'
recovery_target_time = '$recovery_time'
recovery_target_inclusive = true

# WAL restore command
restore_command = 'cp $WAL_ARCHIVE_DIR/%f "%p"'

# Recovery target name (if using named savepoints)
# recovery_target_name = 'my_savepoint'

# Pause recovery at target for manual intervention (optional)
# pause_at_recovery_target = true

# Restore point statistics
recovery_target_lsn = ''
recovery_min_apply_delay = 0
EOF

    log_success "Recovery configuration created: $recovery_conf"
    return 0
}

# 7. Restore Data Directory
restore_data_directory() {
    log_info "Restoring data directory..."

    if sudo mv "$RESTORE_DIR" "$POSTGRES_DATA_DIR"; then
        log_success "Data directory restored"

        # Fix permissions
        if sudo chown -R $POSTGRES_USER:$POSTGRES_USER "$POSTGRES_DATA_DIR"; then
            log_success "Permissions fixed"
            return 0
        fi
    fi

    log_error "Failed to restore data directory"
    return 1
}

# 8. Start PostgreSQL Service
start_postgresql() {
    log_info "Starting PostgreSQL service..."

    if sudo systemctl start postgresql; then
        log_success "PostgreSQL started"
        sleep 3
        return 0
    else
        log_error "Failed to start PostgreSQL"
        return 1
    fi
}

# 9. Verify Recovery
verify_recovery() {
    log_info "Verifying recovery..."

    # Check PostgreSQL is running
    if ! sudo systemctl is-active --quiet postgresql; then
        log_error "PostgreSQL is not running"
        return 1
    fi

    log_success "PostgreSQL is running"

    # Check connectivity
    if sudo -u postgres psql -c "SELECT now();" > /dev/null 2>&1; then
        log_success "Database is accessible"

        # Show recovery info
        echo ""
        log_info "Recovery Information:"
        sudo -u postgres psql -c "\
            SELECT datname, state, redo_lsn, redo_wal_file \
            FROM pg_control_recovery() \
            LIMIT 1;"

        return 0
    else
        log_error "Failed to connect to database"
        return 1
    fi
}

# 10. Full Recovery Workflow
perform_full_recovery() {
    local backup_file=$1
    local recovery_time=$2

    log_info "Starting full PITR recovery workflow\n"

    check_prerequisites || return 1
    list_backups || log_warning "Could not list backups"
    stop_postgresql || return 1
    backup_current_data || return 1
    extract_backup "$backup_file" || return 1
    create_recovery_config "$recovery_time" || return 1
    restore_data_directory || return 1
    start_postgresql || return 1
    verify_recovery || return 1

    log_success "\nRecovery completed successfully!"
    return 0
}

# 11. Rollback After Failed Recovery
rollback_recovery() {
    log_warning "Rolling back recovery...\n"

    log_info "Stopping PostgreSQL..."
    sudo systemctl stop postgresql 2>/dev/null || true

    log_info "Removing failed restore..."
    if [ -d "$POSTGRES_DATA_DIR" ]; then
        sudo rm -rf "$POSTGRES_DATA_DIR"
    fi

    # Find and restore backup
    for backup in "$POSTGRES_DATA_DIR".backup.*; do
        if [ -d "$backup" ]; then
            log_info "Restoring from: $backup"
            if sudo mv "$backup" "$POSTGRES_DATA_DIR"; then
                log_success "Data directory restored from backup"
                break
            fi
        fi
    done

    log_info "Starting PostgreSQL..."
    sudo systemctl start postgresql

    log_success "Rollback complete"
}

# 12. Usage Information
show_usage() {
    cat << EOF
PostgreSQL Point-in-Time Recovery (PITR) - Procedures

Usage:
    $0 [command] [options]

Commands:
    check               Check prerequisites
    list                List available backups
    recover <backup> <time>
                        Perform full recovery
                        Example: $0 recover backup_20251223_150000 "2025-12-23 15:30:00"
    rollback            Rollback recovery to previous state
    verify              Verify recovery configuration

Options:
    --backup-dir DIR    Backup directory (default: ./backups)
    --wal-dir DIR       WAL archive directory (default: ./backups/wal_archive)
    --postgres-ver N    PostgreSQL version (default: 14)
    --help              Show this message

Examples:
    # Check prerequisites
    $0 check

    # List available backups
    $0 list

    # Recover to specific time
    $0 recover backup_20251223_150000 "2025-12-23 15:30:00"

    # Rollback after failed recovery
    $0 rollback

Recovery Process:
    1. Checks prerequisites (PostgreSQL tools, directories)
    2. Lists available backups for selection
    3. Stops PostgreSQL service
    4. Backs up current data directory
    5. Extracts base backup (tar/tar.gz)
    6. Creates recovery configuration
    7. Restores data directory
    8. Starts PostgreSQL service
    9. Verifies recovery and shows info

Security Notes:
    - This script requires sudo/root access
    - WAL files must be archived for PITR to work
    - Test recovery procedures in non-production environment
    - Keep multiple backup copies (local + remote)
EOF
}

# Main script execution
main() {
    if [ $# -eq 0 ]; then
        show_usage
        return 0
    fi

    case "$1" in
        check)
            check_prerequisites
            ;;
        list)
            list_backups
            ;;
        recover)
            if [ $# -lt 3 ]; then
                log_error "Usage: $0 recover <backup_file> <recovery_time>"
                return 1
            fi
            perform_full_recovery "$2" "$3"
            ;;
        rollback)
            rollback_recovery
            ;;
        verify)
            verify_recovery
            ;;
        --help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $1"
            show_usage
            return 1
            ;;
    esac
}

# Run main function
main "$@"
