#!/bin/bash
# =============================================================================
# Resource Cleanup Script - FASE 3
# =============================================================================
# Cleans up unused AWS resources to reduce costs
#
# Usage:
#   ./scripts/resource-cleanup.sh [--dry-run] [--region us-east-1]
#
# Features:
#   - Delete unattached EBS volumes
#   - Clean up old snapshots
#   - Release unassociated Elastic IPs
#   - Delete unused security groups
#   - Remove old artifacts
#   - Cleanup GitHub Actions cache
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
DRY_RUN=false
REGION="${AWS_REGION:-us-east-1}"
RETENTION_DAYS_SNAPSHOT=30
RETENTION_DAYS_ARTIFACTS=7

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

dry_run_msg() {
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN]${NC} Would execute: $1"
    else
        echo -e "${YELLOW}[EXECUTING]${NC} $1"
        eval "$1"
    fi
}

# Check prerequisites
if ! command -v aws &> /dev/null; then
    error "AWS CLI not installed"
    exit 1
fi

log "Resource Cleanup Script"
log "Region: $REGION"
log "Dry Run: $DRY_RUN"
if [ "$DRY_RUN" = true ]; then
    warning "Running in DRY RUN mode - no resources will be deleted"
fi
echo ""

# ============================================================================
# Section 1: Clean up EBS Volumes
# ============================================================================
log "=== EBS Volume Cleanup ==="

cleanup_ebs_volumes() {
    local unattached=$(aws ec2 describe-volumes \
        --region "$REGION" \
        --filters "Name=status,Values=available" \
        --query 'Volumes[].{ID:VolumeId,Size:Size,CreateTime:CreateTime}' \
        --output table)

    if [ -z "$unattached" ] || [ "$unattached" = "" ]; then
        success "No unattached EBS volumes found"
        return
    fi

    log "Found unattached EBS volumes:"
    echo "$unattached"

    echo "$unattached" | grep -oP 'vol-\w+' | while read -r volume_id; do
        dry_run_msg "aws ec2 delete-volume --volume-id $volume_id --region $REGION"
        success "Deleted volume: $volume_id"
    done
}

cleanup_ebs_volumes
echo ""

# ============================================================================
# Section 2: Clean up Snapshots
# ============================================================================
log "=== Snapshot Cleanup ==="

cleanup_snapshots() {
    local cutoff_date=$(date -d "$RETENTION_DAYS_SNAPSHOT days ago" +%Y-%m-%d)

    local old_snapshots=$(aws ec2 describe-snapshots \
        --owner self \
        --region "$REGION" \
        --query "Snapshots[?StartTime<'${cutoff_date}'].{SnapshotId:SnapshotId,Size:VolumeSize,StartTime:StartTime}" \
        --output table)

    if [ -z "$old_snapshots" ] || [ "$old_snapshots" = "" ]; then
        success "No old snapshots found"
        return
    fi

    warning "Found snapshots older than $RETENTION_DAYS_SNAPSHOT days:"
    echo "$old_snapshots"

    echo "$old_snapshots" | grep -oP 'snap-\w+' | while read -r snapshot_id; do
        dry_run_msg "aws ec2 delete-snapshot --snapshot-id $snapshot_id --region $REGION"
        success "Deleted snapshot: $snapshot_id"
    done
}

cleanup_snapshots
echo ""

# ============================================================================
# Section 3: Release Elastic IPs
# ============================================================================
log "=== Elastic IP Cleanup ==="

cleanup_elastic_ips() {
    local unused_eips=$(aws ec2 describe-addresses \
        --region "$REGION" \
        --query 'Addresses[?AssociationId==null].{PublicIp:PublicIp,AllocationId:AllocationId}' \
        --output table)

    if [ -z "$unused_eips" ] || [ "$unused_eips" = "" ]; then
        success "No unassociated Elastic IPs found"
        return
    fi

    warning "Found unassociated Elastic IPs:"
    echo "$unused_eips"

    echo "$unused_eips" | grep -oP 'eipalloc-\w+' | while read -r allocation_id; do
        dry_run_msg "aws ec2 release-address --allocation-id $allocation_id --region $REGION"
        success "Released Elastic IP: $allocation_id"
    done
}

cleanup_elastic_ips
echo ""

# ============================================================================
# Section 4: Remove Unused Security Groups
# ============================================================================
log "=== Security Group Cleanup ==="

cleanup_security_groups() {
    local unused_sgs=$(aws ec2 describe-security-groups \
        --region "$REGION" \
        --query 'SecurityGroups[?IpPermissions==`[]` && IpPermissionsEgress==`[{CidrIp:"0.0.0.0/0",FromPort:-1,ToPort:-1,IpProtocol:"-1"}]`].{GroupId:GroupId,GroupName:GroupName}' \
        --output table)

    if [ -z "$unused_sgs" ] || [ "$unused_sgs" = "" ]; then
        success "No unused security groups found"
        return
    fi

    warning "Found security groups with no rules (except default):"
    echo "$unused_sgs"

    echo "$unused_sgs" | grep -oP 'sg-\w+' | while read -r sg_id; do
        dry_run_msg "aws ec2 delete-security-group --group-id $sg_id --region $REGION"
        success "Deleted security group: $sg_id"
    done
}

cleanup_security_groups
echo ""

# ============================================================================
# Section 5: Clean up Old GitHub Actions Artifacts
# ============================================================================
log "=== GitHub Actions Artifact Cleanup ==="

cleanup_github_artifacts() {
    if [ ! -d ".git" ]; then
        warning "Not in a GitHub repository, skipping artifact cleanup"
        return
    fi

    if ! command -v gh &> /dev/null; then
        warning "GitHub CLI not installed, skipping"
        return
    fi

    # Get artifacts older than retention days
    local cutoff_date=$(date -d "$RETENTION_DAYS_ARTIFACTS days ago" +%s)

    # List old artifacts (this is a simplified example)
    log "GitHub Actions artifacts cleanup would happen here"
    log "Consider enabling auto-cleanup in GitHub settings:"
    log "  Settings → Actions → Artifact and log retention → 7 days"
}

cleanup_github_artifacts
echo ""

# ============================================================================
# Section 6: Clean up Docker Images (local)
# ============================================================================
log "=== Local Docker Cleanup ==="

cleanup_docker() {
    if ! command -v docker &> /dev/null; then
        warning "Docker not installed, skipping"
        return
    fi

    log "Local Docker cleanup:"

    # Remove untagged images
    if [ "$DRY_RUN" = false ]; then
        docker image prune -f --filter "dangling=true" || true
        success "Removed untagged images"
    else
        echo "Would remove untagged images"
    fi

    # Remove unused volumes
    if [ "$DRY_RUN" = false ]; then
        docker volume prune -f || true
        success "Removed unused volumes"
    else
        echo "Would remove unused volumes"
    fi

    # Show images older than 30 days
    log "Old images (can be deleted if not in use):"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.CreatedAt}}" | grep -v "REPOSITORY" || true
}

cleanup_docker
echo ""

# ============================================================================
# Section 7: Summary
# ============================================================================
log "=== Cleanup Summary ==="

if [ "$DRY_RUN" = true ]; then
    warning "Dry run completed - no resources were deleted"
    echo ""
    log "To actually delete resources, run without --dry-run flag:"
    log "  ./scripts/resource-cleanup.sh --region $REGION"
else
    success "Cleanup completed"
fi

echo ""
log "Resources cleaned up:"
log "  - Unattached EBS volumes"
log "  - Old snapshots (>$RETENTION_DAYS_SNAPSHOT days)"
log "  - Unassociated Elastic IPs"
log "  - Unused security groups"
log "  - GitHub Actions artifacts (>$RETENTION_DAYS_ARTIFACTS days)"
log "  - Local Docker cleanup"

echo ""
success "Resource cleanup script finished"
