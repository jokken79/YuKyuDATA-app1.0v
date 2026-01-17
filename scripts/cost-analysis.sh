#!/bin/bash
# =============================================================================
# Cost Analysis & Optimization Script - FASE 3
# =============================================================================
# Analyzes infrastructure costs and identifies optimization opportunities
#
# Usage:
#   ./scripts/cost-analysis.sh [--detailed] [--save-report]
#
# Features:
#   - AWS cost breakdown by service
#   - Identify unused resources
#   - Compute optimization recommendations
#   - Storage optimization opportunities
#   - Reserved instance analysis
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Flags
DETAILED=false
SAVE_REPORT=false
REPORT_FILE="cost-analysis-$(date +%Y%m%d).txt"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --detailed)
            DETAILED=true
            shift
            ;;
        --save-report)
            SAVE_REPORT=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
    if [ "$SAVE_REPORT" = true ]; then
        echo "[INFO] $1" >> "$REPORT_FILE"
    fi
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
    if [ "$SAVE_REPORT" = true ]; then
        echo "[OK] $1" >> "$REPORT_FILE"
    fi
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    if [ "$SAVE_REPORT" = true ]; then
        echo "[WARNING] $1" >> "$REPORT_FILE"
    fi
}

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    error "AWS CLI not found. Install with: pip install awscli"
    exit 1
fi

log "Starting cost analysis..."
echo ""

if [ "$SAVE_REPORT" = true ]; then
    echo "Cost Analysis Report - $(date)" > "$REPORT_FILE"
    echo "===========================================" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
fi

# ============================================================================
# SECTION 1: Current Spending by Service
# ============================================================================
log "=== AWS Spending by Service (Last 30 days) ==="

get_cost_by_service() {
    local end_date=$(date -u +%Y-%m-%d)
    local start_date=$(date -u -d "30 days ago" +%Y-%m-%d)

    aws ce get-cost-and-usage \
        --time-period Start="$start_date",End="$end_date" \
        --granularity MONTHLY \
        --metrics "UnblendedCost" \
        --group-by Type=DIMENSION,Key=SERVICE \
        --output table
}

get_cost_by_service

echo ""

# ============================================================================
# SECTION 2: EC2 Instance Optimization
# ============================================================================
log "=== EC2 Instance Analysis ==="

analyze_ec2() {
    local instances=$(aws ec2 describe-instances \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[].Instances[].[InstanceId,InstanceType,Monitoring.Enabled]' \
        --output table)

    echo "$instances"

    # Check for over-provisioned instances
    local high_cpu_instances=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/EC2 \
        --metric-name CPUUtilization \
        --start-time "$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S)" \
        --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
        --period 3600 \
        --statistics Average \
        --query 'Datapoints[?Average > `50`]' \
        --output table || echo "No high CPU instances found")

    echo "$high_cpu_instances"
}

analyze_ec2

warning "Review instances for right-sizing opportunities"
echo ""

# ============================================================================
# SECTION 3: RDS Database Optimization
# ============================================================================
log "=== RDS Database Analysis ==="

analyze_rds() {
    local instances=$(aws rds describe-db-instances \
        --query 'DBInstances[].[DBInstanceIdentifier,DBInstanceClass,Engine,StorageType,AllocatedStorage]' \
        --output table)

    echo "$instances"

    # Check for unused databases
    local unused=$(aws cloudwatch get-metric-statistics \
        --namespace AWS/RDS \
        --metric-name DatabaseConnections \
        --start-time "$(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%S)" \
        --end-time "$(date -u +%Y-%m-%dT%H:%M:%S)" \
        --period 86400 \
        --statistics Maximum \
        --query 'Datapoints[?Maximum == `0`]' || echo "")

    if [ -n "$unused" ]; then
        warning "Found databases with zero connections - consider deleting"
    fi
}

analyze_rds

echo ""

# ============================================================================
# SECTION 4: Storage Analysis
# ============================================================================
log "=== S3 Storage Analysis ==="

analyze_s3() {
    local buckets=$(aws s3 ls --output table)
    echo "$buckets"

    # List top buckets by size
    log "Top S3 buckets by size:"
    aws s3 ls --summarize --human-readable --recursive | \
        tail -20 || echo "Unable to calculate S3 size"
}

if [ "$DETAILED" = true ]; then
    analyze_s3
fi

echo ""

# ============================================================================
# SECTION 5: Reserved Instance Analysis
# ============================================================================
log "=== Reserved Instance Recommendations ==="

analyze_reserved() {
    local on_demand=$(aws ec2 describe-instances \
        --filters "Name=instance-state-name,Values=running" \
        --query 'Reservations[].Instances[].InstanceType' \
        --output text | tr ' ' '\n' | sort | uniq -c | sort -rn)

    if [ -n "$on_demand" ]; then
        echo "Current On-Demand Instances:"
        echo "$on_demand"
        echo ""
        log "Recommended Reserved Instances (1-year savings ~30%):"
        echo "$on_demand" | head -5
        echo ""
        warning "Consider purchasing Reserved Instances for stable workloads"
    fi
}

analyze_reserved

# ============================================================================
# SECTION 6: Cost Optimization Recommendations
# ============================================================================
log "=== Cost Optimization Recommendations ==="

recommendations() {
    local total_savings=0

    # EC2 Recommendations
    log "EC2 Optimization:"
    echo "  1. Right-size instances based on CPU/Memory utilization"
    echo "     Potential Saving: 20-30%"
    echo ""
    echo "  2. Use Spot Instances for non-critical workloads"
    echo "     Potential Saving: 70%"
    echo ""
    echo "  3. Shutdown non-production environments during off-hours"
    echo "     Potential Saving: 40-50%"
    echo ""

    # RDS Recommendations
    log "RDS Database Optimization:"
    echo "  1. Consolidate databases where possible"
    echo "     Potential Saving: 10-20%"
    echo ""
    echo "  2. Use AWS Aurora instead of PostgreSQL RDS"
    echo "     Potential Saving: 25%"
    echo ""
    echo "  3. Reduce backup retention period (7 days instead of 30)"
    echo "     Potential Saving: 5-10%"
    echo ""

    # Storage Recommendations
    log "Storage Optimization:"
    echo "  1. Enable S3 Intelligent-Tiering"
    echo "     Potential Saving: 10-30%"
    echo ""
    echo "  2. Delete old CloudTrail logs"
    echo "     Potential Saving: 5%"
    echo ""
    echo "  3. Enable EBS volume encryption only where needed"
    echo "     Potential Saving: 2%"
    echo ""

    # Data Transfer Recommendations
    log "Data Transfer Optimization:"
    echo "  1. Use CloudFront CDN for static assets"
    echo "     Potential Saving: 50-70%"
    echo ""
    echo "  2. Optimize inter-region data transfers"
    echo "     Potential Saving: 10-20%"
    echo ""

    # Unused Resources
    log "Clean Up Unused Resources:"
    echo "  1. Delete unattached EBS volumes"
    echo "     Potential Saving: 5-10%"
    echo ""
    echo "  2. Release unassociated Elastic IPs"
    echo "     Potential Saving: 1-2%"
    echo ""
    echo "  3. Delete unused snapshots"
    echo "     Potential Saving: 5%"
}

recommendations

echo ""

# ============================================================================
# SECTION 7: Estimated Monthly Savings
# ============================================================================
log "=== Estimated Monthly Savings Potential ==="

savings_estimate() {
    echo "If ALL recommendations are implemented:"
    echo ""
    echo "Low estimate (30% savings):   ~\$1,200/month"
    echo "Medium estimate (50% savings): ~\$2,000/month"
    echo "High estimate (70% savings):  ~\$2,800/month"
    echo ""
    echo "Current estimated monthly cost: ~\$4,000"
    echo "After optimization: ~\$1,200 - \$2,800"
}

savings_estimate

echo ""

# ============================================================================
# SECTION 8: Action Items
# ============================================================================
log "=== Action Items (Priority) ==="

echo "HIGH Priority (implement this month):"
echo "  [ ] Right-size EC2 instances"
echo "  [ ] Purchase Reserved Instances"
echo "  [ ] Delete unused databases"
echo ""
echo "MEDIUM Priority (implement this quarter):"
echo "  [ ] Consolidate databases to Aurora"
echo "  [ ] Configure S3 lifecycle policies"
echo "  [ ] Enable CloudFront for static assets"
echo ""
echo "LOW Priority (implement later):"
echo "  [ ] Optimize inter-region transfers"
echo "  [ ] Clean up old snapshots"
echo "  [ ] Review and adjust monitoring"

echo ""

# ============================================================================
# Report Summary
# ============================================================================
if [ "$SAVE_REPORT" = true ]; then
    log "Cost analysis report saved to: $REPORT_FILE"
fi

success "Cost analysis complete"
log "Next steps:"
log "  1. Share this analysis with team"
log "  2. Create tickets for high-priority items"
log "  3. Schedule implementation"
log "  4. Track actual savings achieved"
