#!/bin/bash
################################################################################
# Prometheus Setup Script - FASE 3 DevOps Maturity
################################################################################

set -e

echo "=== Prometheus Server Setup ==="

# Update system
yum update -y
yum install -y wget curl git tar gzip

# Create prometheus user
useradd --no-create-home --shell /bin/false prometheus || true

# Download and install Prometheus
PROM_VERSION="2.48.1"
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz
tar -xvzf prometheus-${PROM_VERSION}.linux-amd64.tar.gz

# Create directories
mkdir -p /etc/prometheus /var/lib/prometheus

# Copy binaries
cp /tmp/prometheus-${PROM_VERSION}.linux-amd64/prometheus /usr/local/bin/
cp /tmp/prometheus-${PROM_VERSION}.linux-amd64/promtool /usr/local/bin/

# Copy config
cp /tmp/prometheus-${PROM_VERSION}.linux-amd64/prometheus.yml /etc/prometheus/

# Create prometheus configuration
cat > /etc/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'yukyu-prometheus'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - localhost:9093

rule_files:
  - '/etc/prometheus/alert_rules.yml'

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'application'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'postgresql'
    static_configs:
      - targets: ['localhost:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']
EOF

# Create alert rules
cat > /etc/prometheus/alert_rules.yml << 'EOF'
groups:
  - name: yukyu_alerts
    interval: 30s
    rules:
      # Application alerts
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High request latency detected"

      # Database alerts
      - alert: DatabaseReplicationLag
        expr: pg_replication_lag_seconds > 1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database replication lag exceeds 1 second"

      - alert: HighDatabaseConnections
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of database connections"

      # Infrastructure alerts
      - alert: HighCPUUtilization
        expr: node_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU utilization detected"

      - alert: HighMemoryUtilization
        expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory utilization detected"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{fstype=~"ext4|xfs"} / node_filesystem_size_bytes) < 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Disk space running low"
EOF

# Download and install Node Exporter
NODE_VERSION="1.7.0"
cd /tmp
wget https://github.com/prometheus/node_exporter/releases/download/v${NODE_VERSION}/node_exporter-${NODE_VERSION}.linux-amd64.tar.gz
tar -xvzf node_exporter-${NODE_VERSION}.linux-amd64.tar.gz
cp /tmp/node_exporter-${NODE_VERSION}.linux-amd64/node_exporter /usr/local/bin/

# Download and install AlertManager
ALERTMANAGER_VERSION="0.26.0"
cd /tmp
wget https://github.com/prometheus/alertmanager/releases/download/v${ALERTMANAGER_VERSION}/alertmanager-${ALERTMANAGER_VERSION}.linux-amd64.tar.gz
tar -xvzf alertmanager-${ALERTMANAGER_VERSION}.linux-amd64.tar.gz
mkdir -p /etc/alertmanager /var/lib/alertmanager
cp /tmp/alertmanager-${ALERTMANAGER_VERSION}.linux-amd64/alertmanager /usr/local/bin/
cp /tmp/alertmanager-${ALERTMANAGER_VERSION}.linux-amd64/alertmanager.yml /etc/alertmanager/

# Create AlertManager configuration with Slack integration
cat > /etc/alertmanager/alertmanager.yml << 'EOF'
global:
  resolve_timeout: 5m
  slack_api_url: '${slack_webhook}'

route:
  receiver: 'default'
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'default'
    slack_configs:
      - channel: '#alerts'
        title: 'YuKyuDATA Alert: {{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
        send_resolved: true
EOF

# Set permissions
chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus /etc/alertmanager /var/lib/alertmanager

# Create systemd services
cat > /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus/ \
  --web.console.templates=/etc/prometheus/consoles \
  --web.console.libraries=/etc/prometheus/console_libraries

Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/node-exporter.service << 'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/node_exporter
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/alertmanager.service << 'EOF'
[Unit]
Description=AlertManager
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/alertmanager \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/var/lib/alertmanager
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF

# Start services
systemctl daemon-reload
systemctl enable prometheus
systemctl start prometheus
systemctl enable node-exporter
systemctl start node-exporter
systemctl enable alertmanager
systemctl start alertmanager

# CloudWatch agent setup for logs
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

# CloudWatch agent configuration
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/prometheus.log",
            "log_group_name": "/prometheus/prod",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  },
  "metrics": {
    "namespace": "Prometheus",
    "metrics_collected": {
      "cpu": {
        "measurement": [
          "cpu_usage_idle",
          "cpu_usage_iowait"
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
EOF

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -s \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

echo "=== Prometheus Setup Complete ==="
echo "Prometheus UI: http://<ip>:9090"
echo "AlertManager UI: http://<ip>:9093"
