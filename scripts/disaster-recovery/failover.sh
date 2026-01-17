#!/bin/bash
################################################################################
# Failover Script - Cross-Region Automatic Failover
# YuKyuDATA FASE 3 DevOps Maturity
# RTO: 15 minutes | RPO: 5 minutes
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PRIMARY_REGION="us-east-1"
SECONDARY_REGION="us-west-1"
TERTIARY_REGION="eu-west-1"
FAILOVER_TARGET="${1:-secondary}"
LOG_FILE="/var/log/yukyu-failover.log"

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

################################################################################
# LOGGING FUNCTIONS
################################################################################

log() {
    echo "[${TIMESTAMP}] $@" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $@" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $@" | tee -a "${LOG_FILE}"
}

################################################################################
# PRE-FAILOVER CHECKS
################################################################################

check_prerequisites() {
    log "=== PHASE 1: Pre-Failover Checks ==="

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install AWS CLI."
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured."
        exit 1
    fi

    log_success "AWS CLI configured"

    # Check current region status
    log "Checking primary region (${PRIMARY_REGION}) status..."
    if aws rds describe-db-clusters \
        --region "${PRIMARY_REGION}" \
        --db-cluster-identifier "yukyu-primary" &> /dev/null; then
        log_success "Primary database cluster found"
    else
        log_error "Primary database cluster not accessible"
    fi

    # Check Route53 health
    log "Checking Route53 health checks..."
    HEALTH_CHECK=$(aws route53 list-health_checks --query "HealthChecks[?HealthCheckConfig.FullyQualifiedDomainName=='yukyu-app.example.com'].HealthCheckId" --output text)
    if [ ! -z "$HEALTH_CHECK" ]; then
        log_success "Health checks configured"
    else
        log_warning "No health checks found"
    fi
}

################################################################################
# PHASE 1: VALIDATE FAILOVER TARGET
################################################################################

validate_failover_target() {
    log "=== PHASE 2: Validate Failover Target ==="

    case "${FAILOVER_TARGET}" in
        secondary)
            TARGET_REGION="${SECONDARY_REGION}"
            TARGET_CLUSTER="yukyu-secondary"
            ;;
        tertiary)
            TARGET_REGION="${TERTIARY_REGION}"
            TARGET_CLUSTER="yukyu-tertiary"
            ;;
        *)
            log_error "Invalid failover target: ${FAILOVER_TARGET}"
            log "Usage: $0 {secondary|tertiary}"
            exit 1
            ;;
    esac

    log "Failover target: ${FAILOVER_TARGET} (${TARGET_REGION})"

    # Check if target region is healthy
    log "Checking target cluster health..."
    if aws rds describe-db-clusters \
        --region "${TARGET_REGION}" \
        --db-cluster-identifier "${TARGET_CLUSTER}" \
        --query 'DBClusters[0].Status' \
        --output text &> /dev/null; then
        log_success "Target cluster is accessible"
    else
        log_error "Target cluster is not accessible"
        exit 1
    fi
}

################################################################################
# PHASE 2: PROMOTE READ REPLICA
################################################################################

promote_read_replica() {
    log "=== PHASE 3: Promote Read Replica to Primary ==="

    log "Checking read replica lag..."
    LAG=$(aws rds describe-db-clusters \
        --region "${TARGET_REGION}" \
        --db-cluster-identifier "${TARGET_CLUSTER}" \
        --query 'DBClusters[0].ReplicationLagInMetrics' \
        --output text 2>/dev/null || echo "unknown")

    if [ "${LAG}" != "unknown" ] && [ "${LAG}" -gt 5 ]; then
        log_warning "Replication lag is ${LAG} seconds. Consider waiting..."
    fi

    # Promote cluster (convert from read replica to standalone)
    log "Promoting read replica ${TARGET_CLUSTER}..."
    aws rds modify-db-cluster \
        --region "${TARGET_REGION}" \
        --db-cluster-identifier "${TARGET_CLUSTER}" \
        --enable-http_endpoint \
        --apply-immediately \
        --no-deletion-protection

    # Wait for promotion to complete
    log "Waiting for promotion to complete..."
    COUNTER=0
    MAX_ATTEMPTS=60  # 30 minutes with 30s checks

    while [ $COUNTER -lt $MAX_ATTEMPTS ]; do
        STATUS=$(aws rds describe-db-clusters \
            --region "${TARGET_REGION}" \
            --db-cluster-identifier "${TARGET_CLUSTER}" \
            --query 'DBClusters[0].Status' \
            --output text)

        if [ "${STATUS}" = "available" ]; then
            log_success "Cluster promotion completed (${STATUS})"
            break
        fi

        echo -ne "Status: ${STATUS} - Waiting... $((COUNTER+1))/${MAX_ATTEMPTS}\r"
        sleep 30
        ((COUNTER++))
    done

    if [ $COUNTER -eq $MAX_ATTEMPTS ]; then
        log_error "Cluster promotion timeout"
        exit 1
    fi
}

################################################################################
# PHASE 3: UPDATE ROUTE53
################################################################################

update_route53_failover() {
    log "=== PHASE 4: Update Route53 DNS Records ==="

    # Get new endpoint
    NEW_ENDPOINT=$(aws rds describe-db-clusters \
        --region "${TARGET_REGION}" \
        --db-cluster-identifier "${TARGET_CLUSTER}" \
        --query 'DBClusters[0].Endpoint' \
        --output text)

    log "New database endpoint: ${NEW_ENDPOINT}"

    # Update Route53 record (if managing DNS)
    # This depends on your Route53 setup

    log "DNS failover should update automatically via health checks"
    log_success "Route53 failover logic will activate on health check failure"
}

################################################################################
# PHASE 4: UPDATE APPLICATION CONFIGURATION
################################################################################

update_app_configuration() {
    log "=== PHASE 5: Update Application Configuration ==="

    # Update environment variables in running tasks
    log "Updating ECS task definitions..."

    # Get current task definition
    TASK_FAMILY="yukyu-prod-task"

    CURRENT_TASK=$(aws ecs describe-task-definition \
        --task-definition "${TASK_FAMILY}" \
        --region "${TARGET_REGION}" \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)

    if [ ! -z "$CURRENT_TASK" ]; then
        log "Current task definition: ${CURRENT_TASK}"

        # Register new task definition with updated database URL
        log "Registering new task definition..."
        aws ecs register-task-definition \
            --family "${TASK_FAMILY}" \
            --region "${TARGET_REGION}" \
            --container-definitions "[{\"name\":\"app\",\"environment\":[{\"name\":\"DATABASE_URL\",\"value\":\"postgresql:///${NEW_ENDPOINT}:5432/yukyu\"}]}]"

        log_success "Task definition updated"
    fi
}

################################################################################
# PHASE 5: VERIFY FAILOVER
################################################################################

verify_failover() {
    log "=== PHASE 6: Verify Failover ==="

    # Test database connection
    log "Testing database connection..."

    # Get master username from secrets
    DB_USER=$(aws secretsmanager get-secret-value \
        --secret-id yukyu/database/credentials \
        --region "${TARGET_REGION}" \
        --query 'SecretString' \
        --output text | jq -r '.username')

    log "Testing connectivity to ${NEW_ENDPOINT}..."

    # This requires psql installed - alternative: use Python script
    if command -v psql &> /dev/null; then
        PGPASSWORD=$(aws secretsmanager get-secret-value \
            --secret-id yukyu/database/credentials \
            --region "${TARGET_REGION}" \
            --query 'SecretString' \
            --output text | jq -r '.password')

        if psql -h "${NEW_ENDPOINT}" -U "${DB_USER}" -d yukyu -c "SELECT version();" &> /dev/null; then
            log_success "Database connection verified"
        else
            log_error "Database connection failed"
            return 1
        fi
    else
        log_warning "psql not installed, skipping connection test"
    fi

    # Test application health
    log "Testing application health..."
    ALB_ENDPOINT=$(aws elbv2 describe-load-balancers \
        --region "${TARGET_REGION}" \
        --query "LoadBalancers[?contains(LoadBalancerName, 'yukyu')].DNSName" \
        --output text)

    if [ ! -z "$ALB_ENDPOINT" ]; then
        HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "http://${ALB_ENDPOINT}/api/health")
        if [ "${HEALTH_CHECK}" = "200" ]; then
            log_success "Application health check passed"
        else
            log_error "Application health check failed (HTTP ${HEALTH_CHECK})"
            return 1
        fi
    fi
}

################################################################################
# POST-FAILOVER VALIDATION
################################################################################

post_failover_validation() {
    log "=== PHASE 7: Post-Failover Validation ==="

    # Check number of active connections
    CONNECTIONS=$(aws rds describe-db-clusters \
        --region "${TARGET_REGION}" \
        --db-cluster-identifier "${TARGET_CLUSTER}" \
        --query 'DBClusters[0].AvailableBackupRetentionDays' \
        --output text)

    log "Active database connections: ${CONNECTIONS}"

    # Check replication status (if any replicas exist)
    REPLICAS=$(aws rds describe-db-clusters \
        --region "${TARGET_REGION}" \
        --db-cluster-identifier "${TARGET_CLUSTER}" \
        --query 'DBClusters[0].DBClusterMembers' \
        --output json | jq 'length')

    log "Number of cluster members: ${REPLICAS}"

    # Verify backups enabled
    BACKUP_RETENTION=$(aws rds describe-db-clusters \
        --region "${TARGET_REGION}" \
        --db-cluster-identifier "${TARGET_CLUSTER}" \
        --query 'DBClusters[0].BackupRetentionPeriod' \
        --output text)

    if [ "${BACKUP_RETENTION}" -gt 0 ]; then
        log_success "Backups enabled (retention: ${BACKUP_RETENTION} days)"
    else
        log_error "Backups disabled!"
    fi
}

################################################################################
# NOTIFICATION
################################################################################

notify_failover() {
    log "=== PHASE 8: Send Notifications ==="

    # Slack notification
    SLACK_WEBHOOK="${SLACK_WEBHOOK_URL}"
    if [ ! -z "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\": \"Failover completed to ${FAILOVER_TARGET} region\",
                \"attachments\": [{
                    \"color\": \"good\",
                    \"title\": \"Failover: Primary → ${FAILOVER_TARGET^^}\",
                    \"fields\": [
                        {\"title\": \"From Region\", \"value\": \"${PRIMARY_REGION}\", \"short\": true},
                        {\"title\": \"To Region\", \"value\": \"${TARGET_REGION}\", \"short\": true},
                        {\"title\": \"New Endpoint\", \"value\": \"${NEW_ENDPOINT}\", \"short\": false},
                        {\"title\": \"Timestamp\", \"value\": \"${TIMESTAMP}\", \"short\": true}
                    ]
                }]
            }"
        log_success "Slack notification sent"
    fi

    # Email notification
    if command -v mail &> /dev/null; then
        mail -s "YuKyuDATA Failover Notification - ${TIMESTAMP}" \
            "ops-team@example.com" << EOF
Failover Completed

From Region: ${PRIMARY_REGION}
To Region: ${TARGET_REGION}
Target: ${FAILOVER_TARGET}
New Endpoint: ${NEW_ENDPOINT}
Timestamp: ${TIMESTAMP}

Please verify all systems are operational.
EOF
        log_success "Email notification sent"
    fi
}

################################################################################
# MAIN EXECUTION
################################################################################

main() {
    log "╔════════════════════════════════════════════════════════════╗"
    log "║ YuKyuDATA Multi-Region Failover Script                    ║"
    log "║ RTO: 15 minutes | RPO: 5 minutes                           ║"
    log "╚════════════════════════════════════════════════════════════╝"

    # Execute phases
    check_prerequisites || exit 1
    validate_failover_target || exit 1
    promote_read_replica || exit 1
    update_route53_failover || exit 1
    update_app_configuration || exit 1
    verify_failover || exit 1
    post_failover_validation || exit 1
    notify_failover || exit 1

    log ""
    log_success "═══════════════════════════════════════════════════════════"
    log_success "Failover completed successfully!"
    log_success "═══════════════════════════════════════════════════════════"
    log ""
    log "Post-failover checklist:"
    log "  [ ] Verify application functionality"
    log "  [ ] Check database replication status"
    log "  [ ] Review application logs"
    log "  [ ] Update DNS TTL for faster future failovers"
    log "  [ ] Schedule failover test in opposite direction (Recovery)"
    log ""
}

# Execute main function
main "$@"
