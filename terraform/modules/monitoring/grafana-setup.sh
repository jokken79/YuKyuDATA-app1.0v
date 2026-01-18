#!/bin/bash
################################################################################
# Grafana Setup Script - FASE 3 DevOps Maturity
################################################################################

set -e

echo "=== Grafana Server Setup ==="

# Update system
yum update -y
yum install -y wget curl git tar gzip

# Add Grafana repository
cat > /etc/yum.repos.d/grafana.repo << 'EOF'
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

# Install Grafana
yum install -y grafana

# Create Grafana directories
mkdir -p /var/lib/grafana /var/log/grafana /etc/grafana/provisioning/{datasources,dashboards}

# Create Grafana configuration
cat > /etc/grafana/grafana.ini << 'EOF'
[server]
http_port = 3000
enforce_domain = false

[database]
type = sqlite3
path = /var/lib/grafana/grafana.db

[auth.basic]
enabled = true

[users]
default_theme = dark
auto_assign_org = true

[security]
admin_user = admin
admin_password = ${GRAFANA_PASSWORD:-admin123456}

[analytics]
reporting_enabled = false

[log]
mode = console file
level = info
EOF

# Create Prometheus datasource
cat > /etc/grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    url: http://localhost:9090
    access: proxy
    isDefault: true
    editable: true
    jsonData:
      timeInterval: 15s
EOF

# Create dashboard provisioning config
cat > /etc/grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Dashboards'
    orgId: 1
    folder: 'YuKyuDATA'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

# Create YuKyuDATA dashboard
mkdir -p /var/lib/grafana/dashboards

cat > /var/lib/grafana/dashboards/yukyu-overview.json << 'EOF'
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 0,
            "gradientMode": "none",
            "hideFrom": {
              "tooltip": false,
              "viz": false,
              "legend": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "auto",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "none"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "red",
                "value": 80
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "id": 2,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])",
          "refId": "A"
        }
      ],
      "title": "Request Rate",
      "type": "timeseries"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "thresholds"
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              },
              {
                "color": "yellow",
                "value": 0.5
              },
              {
                "color": "red",
                "value": 1
              }
            ]
          },
          "unit": "s"
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "id": 3,
      "options": {
        "colorMode": "background",
        "graphMode": "area",
        "justifyMode": "auto",
        "orientation": "auto",
        "reduceOptions": {
          "values": false,
          "fields": "",
          "calcs": [
            "lastNotNull"
          ],
          "limit": 1
        },
        "text": {},
        "textMode": "auto"
      },
      "pluginVersion": "10.0.0",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, http_request_duration_seconds)",
          "refId": "A"
        }
      ],
      "title": "Request Latency P95",
      "type": "stat"
    },
    {
      "datasource": {
        "type": "prometheus",
        "uid": "prometheus"
      },
      "fieldConfig": {
        "defaults": {
          "color": {
            "mode": "palette-classic"
          },
          "custom": {
            "axisCenteredZero": false,
            "axisColorMode": "text",
            "axisLabel": "",
            "axisPlacement": "auto",
            "barAlignment": 0,
            "drawStyle": "line",
            "fillOpacity": 10,
            "gradientMode": "none",
            "hideFrom": {
              "tooltip": false,
              "viz": false,
              "legend": false
            },
            "lineInterpolation": "linear",
            "lineWidth": 1,
            "pointSize": 5,
            "scaleDistribution": {
              "type": "linear"
            },
            "showPoints": "never",
            "spanNulls": true,
            "stacking": {
              "group": "A",
              "mode": "normal"
            },
            "thresholdsStyle": {
              "mode": "off"
            }
          },
          "mappings": [],
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "green",
                "value": null
              }
            ]
          }
        },
        "overrides": []
      },
      "gridPos": {
        "h": 8,
        "w": 24,
        "x": 0,
        "y": 8
      },
      "id": 4,
      "options": {
        "legend": {
          "calcs": [],
          "displayMode": "list",
          "placement": "bottom",
          "showLegend": true
        },
        "tooltip": {
          "mode": "single",
          "sort": "none"
        }
      },
      "targets": [
        {
          "expr": "rate(http_requests_total{status=~\"2..\"}[5m])",
          "legendFormat": "Success",
          "refId": "A"
        },
        {
          "expr": "rate(http_requests_total{status=~\"5..\"}[5m])",
          "legendFormat": "Errors",
          "refId": "B"
        }
      ],
      "title": "Request Success vs Errors",
      "type": "timeseries"
    }
  ],
  "refresh": "10s",
  "schemaVersion": 38,
  "style": "dark",
  "tags": [
    "yukyu",
    "overview"
  ],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "timepicker": {},
  "timezone": "UTC",
  "title": "YuKyuDATA Overview",
  "uid": "yukyu-overview",
  "version": 1,
  "weekStart": ""
}
EOF

# Set permissions
chown -R grafana:grafana /var/lib/grafana /etc/grafana

# Start Grafana
systemctl daemon-reload
systemctl enable grafana-server
systemctl start grafana-server

# CloudWatch agent for logs
wget https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm
rpm -U ./amazon-cloudwatch-agent.rpm

echo "=== Grafana Setup Complete ==="
echo "Grafana UI: http://<ip>:3000"
echo "Default credentials: admin / admin123456"
