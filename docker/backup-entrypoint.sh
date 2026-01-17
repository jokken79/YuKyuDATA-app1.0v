#!/bin/bash
# =============================================================================
# YuKyuDATA Backup Service Entrypoint
# =============================================================================
# Automated SQLite backup with retention and optional S3 upload
# =============================================================================

set -e

# Logging function
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        INFO)  echo "[$timestamp] [INFO] $message" ;;
        WARN)  echo "[$timestamp] [WARN] $message" >&2 ;;
        ERROR) echo "[$timestamp] [ERROR] $message" >&2 ;;
        *)     echo "[$timestamp] $message" ;;
    esac
}

# Validate environment
validate_env() {
    if [ -z "$DB_PATH" ]; then
        log ERROR "DB_PATH is not set"
        exit 1
    fi

    if [ -z "$BACKUP_DIR" ]; then
        log ERROR "BACKUP_DIR is not set"
        exit 1
    fi

    if [ "$S3_ENABLED" = "true" ] && [ -z "$S3_BUCKET" ]; then
        log ERROR "S3_ENABLED is true but S3_BUCKET is not set"
        exit 1
    fi
}

# Create backup
create_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="yukyu_backup_${timestamp}"
    local backup_file="${BACKUP_DIR}/${backup_name}.db"

    # Check if database exists
    if [ ! -f "$DB_PATH" ]; then
        log WARN "Database file not found at $DB_PATH, skipping backup"
        return 1
    fi

    # Create backup using SQLite backup command (safe for live databases)
    log INFO "Creating backup: $backup_name"
    sqlite3 "$DB_PATH" ".backup '$backup_file'"

    # Verify backup
    if ! sqlite3 "$backup_file" "PRAGMA integrity_check;" > /dev/null 2>&1; then
        log ERROR "Backup integrity check failed!"
        rm -f "$backup_file"
        return 1
    fi

    # Compress if enabled
    if [ "$COMPRESS" = "true" ]; then
        log INFO "Compressing backup..."
        gzip "$backup_file"
        backup_file="${backup_file}.gz"
    fi

    # Get file size
    local size=$(du -h "$backup_file" | cut -f1)
    log INFO "Backup created: $(basename $backup_file) ($size)"

    # Upload to S3 if enabled
    if [ "$S3_ENABLED" = "true" ]; then
        upload_to_s3 "$backup_file"
    fi

    return 0
}

# Upload to S3
upload_to_s3() {
    local file=$1
    local filename=$(basename "$file")
    local s3_path="s3://${S3_BUCKET}/${S3_PREFIX}${filename}"

    log INFO "Uploading to S3: $s3_path"

    if aws s3 cp "$file" "$s3_path" --quiet; then
        log INFO "S3 upload successful"
    else
        log ERROR "S3 upload failed!"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log INFO "Cleaning up backups older than $BACKUP_RETENTION_DAYS days..."

    # Local cleanup
    local deleted_count=$(find "$BACKUP_DIR" -name "yukyu_backup_*.db*" -mtime +$BACKUP_RETENTION_DAYS -delete -print | wc -l)

    if [ "$deleted_count" -gt 0 ]; then
        log INFO "Deleted $deleted_count old local backup(s)"
    fi

    # S3 cleanup if enabled
    if [ "$S3_ENABLED" = "true" ]; then
        log INFO "Cleaning up old S3 backups..."
        local cutoff_date=$(date -d "-${BACKUP_RETENTION_DAYS} days" +%Y-%m-%d 2>/dev/null || date -v-${BACKUP_RETENTION_DAYS}d +%Y-%m-%d)

        # List and delete old files from S3
        aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}" 2>/dev/null | while read -r line; do
            local file_date=$(echo "$line" | awk '{print $1}')
            local file_name=$(echo "$line" | awk '{print $4}')

            if [[ "$file_date" < "$cutoff_date" ]] && [[ "$file_name" == yukyu_backup_* ]]; then
                aws s3 rm "s3://${S3_BUCKET}/${S3_PREFIX}${file_name}" --quiet
                log INFO "Deleted old S3 backup: $file_name"
            fi
        done
    fi
}

# Main loop
main() {
    log INFO "=========================================="
    log INFO "YuKyuDATA Backup Service Starting"
    log INFO "=========================================="
    log INFO "Database: $DB_PATH"
    log INFO "Backup directory: $BACKUP_DIR"
    log INFO "Backup interval: ${BACKUP_INTERVAL}s"
    log INFO "Retention: ${BACKUP_RETENTION_DAYS} days"
    log INFO "Compression: $COMPRESS"
    log INFO "S3 enabled: $S3_ENABLED"
    if [ "$S3_ENABLED" = "true" ]; then
        log INFO "S3 bucket: $S3_BUCKET"
    fi
    log INFO "=========================================="

    validate_env

    # Run initial backup
    create_backup && cleanup_old_backups

    # Record last run time
    date +%s > /tmp/backup_last_run

    # Main loop
    while true; do
        log INFO "Sleeping for ${BACKUP_INTERVAL} seconds..."
        sleep "$BACKUP_INTERVAL"

        create_backup && cleanup_old_backups
        date +%s > /tmp/backup_last_run
    done
}

# Handle signals
trap 'log INFO "Received shutdown signal, exiting..."; exit 0' SIGTERM SIGINT

# Run main
main
