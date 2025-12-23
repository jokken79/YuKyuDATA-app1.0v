# FASE 3 Phase 7: Alerting System & Configuration

## Overview

Phase 7 Part 2 implements comprehensive alerting for performance monitoring, enabling automatic notification when metrics exceed configured thresholds.

**Status:** Complete ✅
**Date:** 2025-12-23

---

## Alerting System Components

### 1. Alert Configuration 📋

**File:** `monitoring/alerts_config.yml` (200+ lines)

YAML-based configuration defining:

#### Alert Categories

**Performance Alerts**
```yaml
- Slow Query Alert: >500ms
- Cache Hit Ratio Low: <80% (warning), <50% (critical)
```

**Table Health Alerts**
```yaml
- Table Bloat Warning: >20% dead rows
- Table Bloat Critical: >50% dead rows
- High Dead Row Count: >10,000 rows
```

**Index Alerts**
```yaml
- Unused Index: 0 scans
- Missing Index Opportunity: >100 sequential scans
```

**Connection Alerts**
```yaml
- High Connection Usage: >80% of max
- Connection Pool Exhausted: >95% of max
- Idle in Transaction: >5 connections
```

**Storage Alerts**
```yaml
- Database Size Growing: >10% per day
- Low Disk Space: >80% usage
```

**Baseline Alerts**
```yaml
- Performance Degradation: >10% worse than baseline
- Baseline Out of Date: >30 days old
```

#### Alert Properties

```yaml
name: Alert display name
metric: Metric to monitor
threshold: Alert trigger value
severity: "info" | "warning" | "critical"
comparison: "greater_than" | "less_than" | "equals"
description: Human-readable description
action: Actions to take (log, notify, alert)
enabled: Boolean to enable/disable
evaluation_window: Time window for evaluation
```

#### Actions

```yaml
action:
  - log: "Log message to file"
  - notify: "Send to notification channel"
  - alert: "Trigger PagerDuty escalation"
  - remediate: "Auto-fix if possible"
```

### 2. Alert Manager 🔔

**File:** `monitoring/alert_manager.py` (300+ lines)

Python implementation for alert management:

#### Features

- ✅ **Configuration Loading** - Reads alerts_config.yml
- ✅ **Alert Deduplication** - Prevents alert spam
- ✅ **Multi-Channel Notifications** - Log, email, Slack, PagerDuty
- ✅ **Alert History** - Tracks sent alerts for deduplication
- ✅ **Threshold Checking** - Validates configured thresholds
- ✅ **Test Mode** - Test alert configuration safely

#### Notification Channels

| Channel | Configuration | Status |
|---------|---------------|--------|
| **Log File** | Path in config | ✅ Ready |
| **Console** | stdout | ✅ Ready |
| **Email (SMTP)** | Environment vars | 🔧 Configure SMTP |
| **Slack** | Webhook URL | 🔧 Configure webhook |
| **PagerDuty** | API key | 🔧 Configure API |

#### Usage

**Test Alert Configuration**
```bash
python monitoring/alert_manager.py --test
```

**Check All Thresholds**
```bash
python monitoring/alert_manager.py --check
```

**Send Specific Alert**
```bash
python monitoring/alert_manager.py --send-alert "Cache Hit < 80%"
```

### 3. Alert Thresholds

#### Performance Thresholds

| Metric | Severity | Threshold | Action |
|--------|----------|-----------|--------|
| Query Time | Warning | >500ms | Log alert |
| Query Time | Critical | >2000ms | Page on-call |
| Cache Hit Ratio | Warning | <80% | Log alert |
| Cache Hit Ratio | Critical | <50% | Page on-call |

#### Table Health Thresholds

| Metric | Severity | Threshold | Action |
|--------|----------|-----------|--------|
| Table Bloat | Warning | >20% | Log alert |
| Table Bloat | Critical | >50% | Page on-call |
| Dead Rows | Warning | >10,000 | Log alert |
| Dead Rows | Critical | >50,000 | Page on-call |

#### Connection Thresholds

| Metric | Severity | Threshold | Action |
|--------|----------|-----------|--------|
| Active Connections | Warning | >80% max | Log alert |
| Active Connections | Critical | >95% max | Page on-call |
| Idle in Transaction | Warning | >5 | Log alert |
| Idle in Transaction | Critical | >10 | Page on-call |

#### Storage Thresholds

| Metric | Severity | Threshold | Action |
|--------|----------|-----------|--------|
| DB Size Growth | Info | >10%/day | Daily report |
| Disk Usage | Warning | >80% | Log alert |
| Disk Usage | Critical | >95% | Page on-call |

---

## Configuration Guide

### 1. Basic Setup

**Enable Log Alerts (Default)**
```yaml
notifications:
  log:
    enabled: true
    location: "/var/log/yukyu_alerts.log"
```

**Enable Console Alerts**
```yaml
notifications:
  console:
    enabled: true
```

### 2. Email Alerts

**Configure SMTP**
```bash
export SMTP_SERVER="smtp.company.com:25"
export ALERT_EMAIL_FROM="alerts@company.com"
export ALERT_EMAIL_TO="dba@company.com,ops@company.com"
```

**Enable in Config**
```yaml
notifications:
  email:
    enabled: true
    smtp_server: "localhost:25"
    from: "alerts@yukyu.local"
```

### 3. Slack Alerts

**Get Webhook URL**
1. Create Slack webhook: https://api.slack.com/messaging/webhooks
2. Set environment variable:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**Enable in Config**
```yaml
notifications:
  slack:
    enabled: true
    webhook_url: ""  # Uses env var
    channels:
      default: "#alerts"
      critical: "#critical-alerts"
```

### 4. PagerDuty Escalation

**Configure PagerDuty**
```bash
export PAGERDUTY_API_KEY="your-api-key"
export PAGERDUTY_SERVICE_ID="service-id"
```

**Enable in Config**
```yaml
notifications:
  pagerduty:
    enabled: true
    api_key: ""  # Uses env var
```

---

## Alert Deduplication

Prevents sending the same alert repeatedly:

```yaml
aggregation:
  deduplication:
    enabled: true
    window: "1h"  # Don't repeat same alert within 1 hour
```

**Example:**
- 10:00 - "Cache Hit < 80%" alert sent
- 10:30 - Cache still < 80%, but alert suppressed (within 1h window)
- 11:05 - Cache still < 80%, alert sent again (1h+ has passed)

---

## Maintenance Windows

Suppress alerts during scheduled maintenance:

```yaml
suppression:
  maintenance_windows:
    - name: "Sunday Maintenance"
      start_time: "02:00"
      end_time: "04:00"
      day_of_week: "Sunday"
      enabled: true

    - name: "Monthly Backups"
      start_time: "23:00"
      end_time: "05:00"
      day_of_month: "1"
      enabled: true
```

---

## Cron Integration

### Daily Alert Checks

```bash
# Run alert checks every 6 hours
0 */6 * * * /usr/bin/python3 /path/to/monitoring/alert_manager.py --check >> /var/log/alert_checks.log 2>&1

# Send alert test weekly
0 9 * * 1 /usr/bin/python3 /path/to/monitoring/alert_manager.py --test >> /var/log/alert_test.log 2>&1
```

### Integration with Performance Monitor

```bash
# Run performance check and send alerts
0 * * * * /usr/bin/python3 /path/to/monitoring/performance_monitor.py > /tmp/perf_metrics.json 2>&1 && \
  /usr/bin/python3 /path/to/monitoring/alert_manager.py --check >> /var/log/alerts.log 2>&1
```

---

## Testing Alerts

### Test Configuration

```bash
python monitoring/alert_manager.py --test
```

**Output:**
```
🧪 Testing alert system...

🚨 Sending alert: Test Alert - Info (info)
  ✅ Alert logged to /var/log/yukyu_alerts.log

🚨 Sending alert: Test Alert - Warning (warning)
  ✅ Alert logged to /var/log/yukyu_alerts.log

🚨 Sending alert: Test Alert - Critical (critical)
  ✅ Alert logged to /var/log/yukyu_alerts.log

✅ Alert test completed
```

### Test Individual Alerts

```bash
# Send specific alert
python monitoring/alert_manager.py --send-alert "Cache Hit < 80%"

# Output: 🚨 Sending alert: Cache Hit < 80% (warning)
#   Cache monitoring alert message
#   ✅ Alert logged to /var/log/yukyu_alerts.log
```

### Verify Alert Delivery

**Check Log File**
```bash
tail -f /var/log/yukyu_alerts.log
# [2025-12-23T15:30:45...] Cache Hit Ratio Low: Database cache hit ratio below 80%
```

---

## Integration with Phase 7 Monitoring

### Combined Monitoring & Alerting Workflow

```bash
# 1. Run performance analysis
python monitoring/performance_monitor.py --detailed > /tmp/perf_metrics.json

# 2. Parse metrics and check thresholds
python monitoring/alert_manager.py --check

# 3. Send any triggered alerts
# (Alerts sent automatically if thresholds exceeded)
```

### Daily Operations

```bash
#!/bin/bash
# daily_monitoring.sh

LOG_DIR="/var/log/yukyu"
METRICS_DIR="/var/metrics/yukyu"

# Ensure directories exist
mkdir -p $LOG_DIR $METRICS_DIR

# Run performance analysis
python monitoring/performance_monitor.py > $METRICS_DIR/perf_$(date +%Y%m%d_%H%M%S).json

# Check baselines
python monitoring/baseline_collector.py --compare >> $LOG_DIR/baseline.log

# Check alerts
python monitoring/alert_manager.py --check >> $LOG_DIR/alerts.log

echo "Daily monitoring complete - $(date)"
```

**Schedule with cron:**
```bash
0 2 * * * /path/to/daily_monitoring.sh
```

---

## Alert Response Procedures

### Info Level Alerts

**Example:** "Baseline Out of Date"

**Response:**
1. Check alert log for details
2. Create new baseline when convenient
3. No immediate action required

### Warning Level Alerts

**Example:** "Cache Hit Ratio < 80%"

**Response:**
1. Log alert automatically
2. Check performance_monitor.py for details
3. Schedule optimization session
4. Apply suggested fixes

**Example Actions:**
```bash
# Check cache statistics
python monitoring/performance_monitor.py | grep -A 5 "cache"

# Create baseline before optimization
python monitoring/baseline_collector.py --create

# Apply optimization
# (increase shared_buffers, restart PostgreSQL)

# Verify improvement
python monitoring/baseline_collector.py --compare
```

### Critical Level Alerts

**Example:** "Connection Pool Exhausted"

**Response - IMMEDIATE ACTION:**
1. Alert auto-escalated to on-call via PagerDuty
2. Check current connections:

```bash
psql -U yukyu_user -d yukyu -c "
  SELECT count(*) FROM pg_stat_activity;
"
```

3. Identify long-running queries:

```bash
psql -U yukyu_user -d yukyu -c "
  SELECT pid, usename, query, query_start
  FROM pg_stat_activity
  WHERE state != 'idle'
  ORDER BY query_start DESC;
"
```

4. Kill idle connections if safe:

```bash
psql -U postgres -c "
  SELECT pg_terminate_backend(pid)
  FROM pg_stat_activity
  WHERE state = 'idle' AND query_start < now() - interval '1 hour';
"
```

5. Increase connection limit if needed:

```bash
export DB_POOL_SIZE=30
# Restart application
systemctl restart yukyu-app
```

---

## Monitoring Dashboard Integration

### Alert Summary Report

```bash
#!/bin/bash
# Generate daily alert summary

echo "=== Alert Summary - $(date) ==="
echo ""

echo "Log Alerts:"
tail -20 /var/log/yukyu_alerts.log | grep "\[" | tail -10

echo ""
echo "Recent Thresholds Checked:"
tail -20 /var/log/alert_checks.log | tail -10

echo ""
echo "Alert History (Last 7 Days):"
find /var/log -name "*alert*" -mtime -7 -exec wc -l {} +
```

---

## Environment Variables

Configure alert delivery through environment:

```bash
# Email
export SMTP_SERVER="smtp.company.com:25"
export ALERT_EMAIL_FROM="alerts@company.com"
export ALERT_EMAIL_TO="dba@company.com"

# Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."

# PagerDuty
export PAGERDUTY_API_KEY="your-api-key"
export PAGERDUTY_SERVICE_ID="service-id"
```

---

## Files Created

```
monitoring/
├── alerts_config.yml            (200+ lines) - Alert configuration
├── alert_manager.py             (300+ lines) - Alert implementation
└── .alert_history.json          (auto-created) - Alert deduplication
```

---

## Phase 7 Summary

### Part 1: Monitoring Systems ✅
- ✅ performance_monitor.py
- ✅ query_optimizer.py
- ✅ baseline_collector.py

### Part 2: Alerting Systems ✅
- ✅ alerts_config.yml
- ✅ alert_manager.py
- ✅ Multi-channel notifications
- ✅ Alert deduplication
- ✅ Threshold configuration

### Part 3: Documentation ✅
- ✅ FASE3_PHASE7_MONITORING.md
- ✅ FASE3_PHASE7_QUICK_REFERENCE.md
- ✅ FASE3_PHASE7_ALERTING.md (this file)

---

## Next Steps

### Phase 8: Dashboard (Optional)
- Create web dashboard for metrics
- Real-time visualization
- Alert timeline
- Historical trends

### Phase 9: Full-Text Search (Scheduled)
- Implement PostgreSQL tsvector
- Add GIN indexes
- Create search API endpoints

### Phase 10: PITR Backups (Scheduled)
- Configure WAL archiving
- Automated backup scheduling
- Point-in-time recovery setup

---

**Phase 7 Status:** ✅ COMPLETE
**Monitoring & Alerting:** Production Ready
**Date:** 2025-12-23
