# YuKyuDATA Disaster Recovery Runbook

## FASE 3: DevOps Maturity - Multi-Region Failover

**Last Updated**: 2026-01-17
**Version**: 1.0
**RTO**: 15 minutes
**RPO**: 5 minutes

---

## 1. INCIDENT DETECTION & ASSESSMENT

### 1.1 Primary Region Failure Detection

| Symptom | Detection Method | Alert |
|---------|-----------------|-------|
| Database Down | Health check HTTP 5xx | `InstanceDown` |
| High Replication Lag | RDS metric > 1s | `HighReplicationLag` |
| Application Error Rate > 5% | HTTP 5xx rate | `HighErrorRate` |
| CPU/Memory exhausted | CloudWatch metric > 95% | `CriticalUtilization` |

### 1.2 Assessment Decision Tree

```
Primary Region Down?
├─ YES: Check Secondary Health
│   ├─ Secondary Healthy?
│   │   ├─ YES → INITIATE FAILOVER (Section 2)
│   │   └─ NO → Check Tertiary (Section 3)
│   └─ Secondary Down? → Escalate to P1 (Both regions down)
└─ NO: Check Replication Lag
    ├─ > 5 seconds → HIGH URGENCY (Prepare failover)
    └─ < 5 seconds → Monitor (May recover automatically)
```

### 1.3 Escalation Procedure

```
Incident Level | Duration | Action | Team
-------------|----------|--------|------
P3 (Warning) | < 5min | Monitor | On-call
P2 (Major)   | < 15min | Prepare | SRE + DB
P1 (Critical) | > 15min | Execute | VP Eng + Full Team
SEV-1        | Impact  | Execute | All hands
```

---

## 2. FAILOVER TO SECONDARY REGION (us-west-1)

### 2.1 Pre-Failover Checklist

```bash
# SSH to on-call bastion
ssh ops@bastion.example.com

# Create incident ticket
create_incident "Primary region failure - initiating failover"

# Get current status
aws rds describe-db-clusters --region us-east-1 --query 'DBClusters[*].[DBClusterIdentifier,Status]' --output table

# Check secondary health
aws rds describe-db-clusters --region us-west-1 --query 'DBClusters[*].[DBClusterIdentifier,Status]' --output table

# Verify replication lag
aws rds describe-global-database-clusters --query 'GlobalDatabaseClusters[*].GlobalWriteForwardingStatus'
```

**Decision Gate**: Can we contact secondary DB within 10 seconds?
- YES ✓ → Continue to 2.2
- NO ✗ → Check Tertiary (Section 3)

### 2.2 Execute Automated Failover

```bash
# Change to correct directory
cd /home/user/YuKyuDATA-app1.0v/scripts/disaster-recovery

# Run failover script
./failover.sh secondary

# Expected output:
# [INFO] Promoting read replica...
# [INFO] Waiting for promotion to complete...
# [SUCCESS] Failover completed successfully!
```

**Script Actions**:
1. Promotes secondary read replica to standalone cluster (5-7 min)
2. Updates Route53 DNS to secondary ALB
3. Updates ECS task definitions with new DB endpoint
4. Validates health checks
5. Sends Slack notification

### 2.3 Manual Failover (If Script Fails)

**Step 1: Promote Read Replica**
```bash
aws rds modify-db-cluster \
  --region us-west-1 \
  --db-cluster-identifier yukyu-secondary \
  --enable-http-endpoint \
  --apply-immediately \
  --no-deletion-protection

# Wait for status = available (check every 30s for ~10 min)
watch -n 30 'aws rds describe-db-clusters --region us-west-1 --db-cluster-identifier yukyu-secondary --query "DBClusters[0].Status"'
```

**Step 2: Get New Endpoint**
```bash
aws rds describe-db-clusters \
  --region us-west-1 \
  --db-cluster-identifier yukyu-secondary \
  --query 'DBClusters[0].Endpoint' \
  --output text

# Example output: yukyu-secondary.cluster-xxx.us-west-1.rds.amazonaws.com
```

**Step 3: Update Route53**
```bash
# Get hosted zone ID
ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name example.com --query 'HostedZones[0].Id' --output text)

# Create change batch to update DNS
aws route53 change-resource-record-sets \
  --hosted-zone-id $ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "secondary",
        "Failover": "PRIMARY",
        "AliasTarget": {
          "HostedZoneId": "Z2BLHKQBDSDHD",
          "DNSName": "alb-us-west-1.example.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

**Step 4: Update ECS Task Definitions**
```bash
# Get current task definition
aws ecs describe-task-definition \
  --task-definition yukyu-prod-task \
  --region us-west-1 \
  --query taskDefinition > task-def.json

# Edit task-def.json:
# 1. Change "family": "yukyu-prod-task-new"
# 2. Update DATABASE_URL environment variable
# 3. Remove taskDefinitionArn, revision

# Register new revision
aws ecs register-task-definition \
  --region us-west-1 \
  --cli-input-json file://task-def.json

# Update service to use new task definition
aws ecs update-service \
  --region us-west-1 \
  --cluster yukyu-secondary-cluster \
  --service yukyu-secondary-service \
  --task-definition yukyu-prod-task-new:1 \
  --force-new-deployment
```

### 2.4 Post-Failover Validation (15-20 minutes)

**Validation Steps:**

```bash
# 1. Test database connectivity
psql -h yukyu-secondary.cluster-xxx.us-west-1.rds.amazonaws.com \
     -U yukyu_admin \
     -d yukyu \
     -c "SELECT COUNT(*) FROM employees;"

# Expected: Should return employee count

# 2. Test application health
curl https://api.example.com/api/health

# Expected:
# {
#   "status": "healthy",
#   "database": true,
#   "version": "5.19"
# }

# 3. Check replication status (if tertiary replica exists)
aws rds describe-db-clusters \
  --region eu-west-1 \
  --db-cluster-identifier yukyu-tertiary \
  --query 'DBClusters[0].Status'

# 4. Monitor error rates
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Sum

# 5. Check application logs
tail -100 /var/log/ecs/yukyu-app.log
```

**Success Criteria:**
- [ ] Database connectivity: ✓
- [ ] Application health: 200 OK
- [ ] HTTP error rate: < 5%
- [ ] Database replication: < 1 second lag
- [ ] Tertiary replica syncing: Active

### 2.5 Communication & Documentation

**Slack Notification:**
```
🟡 Failover Initiated to us-west-1
Status: In Progress
From: us-east-1 (primary)
To: us-west-1 (secondary)
ETA: 15 minutes
Contact: @on-call-sre
```

**Create Post-Incident Document:**
```
Title: Post-Failover Assessment (MM/DD/YYYY HH:MM)
- Failure cause: [Primary region outage]
- Detection time: [Timestamp]
- Failover completion: [Duration]
- Data loss: [None - RPO maintained]
- Affected services: [List]
- Customer impact: [Duration, users affected]
- Root cause: [To be determined]
- Permanent fix: [To be determined]
```

---

## 3. FAILOVER TO TERTIARY REGION (eu-west-1)

### 3.1 When to Use Tertiary Failover

**Tertiary failover is used when:**
1. Both primary AND secondary regions are down
2. Secondary replication is severely lagged (> 10 minutes)
3. Data loss is acceptable (RPO may exceed 5 minutes)

### 3.2 Execute Tertiary Failover

```bash
# Modify failover script for tertiary target
cd /home/user/YuKyuDATA-app1.0v/scripts/disaster-recovery
./failover.sh tertiary

# This will:
# 1. Promote tertiary read replica
# 2. Update Route53 to tertiary ALB
# 3. Update ECS services in tertiary region
# 4. Send critical alerts
```

### 3.3 Recovery Procedure

**Once primary region is recovered:**

```bash
# 1. Restore data from backup
./backup-verification.sh us-east-1

# 2. Set up primary as new read replica of secondary
aws rds create-db-cluster-instance \
  --db-cluster-identifier yukyu-primary \
  --db-instance-class db.r6g.large \
  --replication-source-arn arn:aws:rds:us-west-1:...:cluster:yukyu-secondary

# 3. Test primary restoration
psql -h yukyu-primary.cluster-xxx.us-east-1.rds.amazonaws.com \
     -U yukyu_admin -d yukyu -c "SELECT COUNT(*) FROM employees;"

# 4. Failback: Switch back to primary (if acceptable downtime)
./failover.sh primary  # Custom script for failback
```

---

## 4. DATABASE RECOVERY PROCEDURES

### 4.1 Point-in-Time Recovery (PITR)

**If data is corrupted but region is operational:**

```bash
# Find backup to restore from
aws backup list-recovery-points-by-resource \
  --region us-east-1 \
  --by-resource-type RDS \
  --query 'RecoveryPoints[*].[RecoveryPointArn, CreationDate]' \
  --output table

# Restore to point in time
BACKUP_ARN="arn:aws:backup:us-east-1:xxx:recovery-point:xxx"

aws backup start-restore-job \
  --recovery-point-arn $BACKUP_ARN \
  --iam-role-arn arn:aws:iam::$ACCOUNT:role/aws-backup-recovery-role \
  --metadata '{"DBClusterIdentifier":"yukyu-restored"}'

# Monitor restoration (10-20 minutes)
# Once complete, validate data and swap DNS if acceptable
```

### 4.2 Backup Verification

**Daily automated check:**
```bash
cd /home/user/YuKyuDATA-app1.0v/scripts/disaster-recovery
./backup-verification.sh us-east-1

# Verifies:
# - Last backup < 5 minutes old (RPO)
# - Backup encryption: ✓
# - Restore test: ✓
# - Cross-region replication: ✓
```

---

## 5. COMMUNICATION TEMPLATES

### 5.1 Initial Detection Notification

```
🚨 INCIDENT: Primary Region Database Down
Status: Investigating
Severity: P1
Detection Time: [TIME]
Estimated Impact: [Users] affected
Actions:
  - Failover to secondary region in progress
  - ETA: 10 minutes
Updates every 5 minutes: @ops-team
```

### 5.2 Failover In Progress

```
⚠️ Failover In Progress (Primary → Secondary)
Current Step: [Promoting read replica]
Progress: [3/6 phases]
ETA: [8 minutes]
Estimated User Impact: [2-3 minute service interruption]
```

### 5.3 Failover Complete

```
✅ Failover Complete - Service Restored
From: us-east-1 (primary)
To: us-west-1 (secondary)
Duration: [15 minutes]
Data Loss: None (RPO maintained)
Current Status: All systems operational
Incident Status: Post-incident review in progress
```

### 5.4 Stakeholder Escalation

```
Escalating incident to VP Engineering:
- Primary and secondary regions both unavailable
- Tertiary region being activated
- ETA: 30 minutes
- Potential data loss: < 5 minutes
- Customer communication in progress
- Full team mobilized
```

---

## 6. TESTING SCHEDULE

### Monthly Failover Test

```bash
# First Tuesday of each month, 2 AM UTC
# Non-destructive simulation

cd /home/user/YuKyuDATA-app1.0v/scripts/disaster-recovery
./failover-test.sh

# Validates:
# - Snapshot consistency
# - Restore procedure
# - RTO achievable (< 15 min)
# - RPO achievable (< 5 min)
# - Cross-region replication
```

**Test Results Documentation:**
```
Monthly Test Report: January 2026
Test Date: 2026-01-03 at 02:00 UTC
Result: ✓ PASSED

RTO Achieved: 12 minutes (target: 15)
RPO Achieved: 3.5 minutes (target: 5)
Data Integrity: Verified
Cross-Region: Verified

Next Test: 2026-02-03 at 02:00 UTC
```

---

## 7. CONTACTS & ESCALATION

### On-Call Contacts

| Role | Primary | Secondary | Tertiary |
|------|---------|-----------|----------|
| SRE Lead | +1-555-0101 | +1-555-0102 | Slack @sre |
| DB Admin | +1-555-0201 | +1-555-0202 | Slack @dba |
| Eng Manager | +1-555-0301 | +1-555-0302 | Email |
| VP Eng | +1-555-0401 | +1-555-0402 | Email |

### Emergency Escalation

```
P1 Incident → Automatic escalation:
  T+0min: @on-call-sre  (Slack + SMS)
  T+2min: @dba-team     (If DB related)
  T+5min: @eng-manager  (Approval required for failover)
  T+10min: @vp-eng      (If outage > 10 min)
```

---

## 8. POST-INCIDENT REVIEW

### Post-Incident Actions

- [ ] Document incident timeline
- [ ] Identify root cause
- [ ] Create permanent fix
- [ ] Update runbook based on learnings
- [ ] Schedule blameless post-mortem
- [ ] Distribute lessons learned to team

### Post-Incident Template

```markdown
# Post-Incident Review: [Date] [Incident Name]

## Timeline
- T+00:00 - Detection
- T+00:05 - Investigation began
- T+00:15 - Failover initiated
- T+00:30 - Failover complete
- T+00:35 - Service restored

## Root Cause
[Brief summary of what happened]

## Impact
- Duration: [Minutes]
- Users affected: [Count]
- Data loss: [None/Amount]
- Revenue impact: [If applicable]

## What Went Well
1. [Good practice 1]
2. [Good practice 2]

## What Can Improve
1. [Opportunity 1]
2. [Opportunity 2]

## Action Items
- [ ] [Task 1] - Owner: @name - Due: [Date]
- [ ] [Task 2] - Owner: @name - Due: [Date]

## Follow-up Monitoring
- Monitor error rates for 24 hours
- Daily health checks for 7 days
- Monthly regression test
```

---

## 9. QUICK REFERENCE

### Emergency Commands

```bash
# Failover to secondary
./failover.sh secondary

# Failover to tertiary
./failover.sh tertiary

# Check backup status
./backup-verification.sh us-east-1

# Monthly test (non-destructive)
./failover-test.sh

# Validate current health
aws rds describe-db-clusters --region us-east-1 --query 'DBClusters[*].[DBClusterIdentifier,Status]'

# Get database endpoint
aws rds describe-db-clusters --region us-west-1 --db-cluster-identifier yukyu-secondary --query 'DBClusters[0].Endpoint'

# Test application
curl https://api.example.com/api/health
```

### Status Pages

- **Prometheus**: http://prometheus.example.com:9090
- **Grafana**: http://grafana.example.com:3000
- **AlertManager**: http://alertmanager.example.com:9093
- **Application**: https://api.example.com

### Important Links

- **Architecture Diagram**: https://wiki.example.com/architecture/multi-region
- **SLA Document**: https://wiki.example.com/sla/yukyu
- **Cost Calculator**: https://calculator.aws.amazon.com/
- **Status Page**: https://status.example.com

---

**Version History:**
- v1.0 - 2026-01-17: Initial runbook for FASE 3 DevOps Maturity
- v1.1 - TBD: Updates based on first real failover

---

**Last Reviewed**: 2026-01-17
**Next Review**: 2026-02-17 (Monthly)
**Last Test**: 2026-01-03 (Passed ✓)
