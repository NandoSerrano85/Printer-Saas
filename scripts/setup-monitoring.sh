#!/bin/bash

# =============================================================================
# MONITORING SETUP SCRIPT
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_DIR/monitoring"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARNING] $1${NC}"; }

create_prometheus_config() {
    log "Creating Prometheus configuration..."
    
    mkdir -p "$MONITORING_DIR"
    
    cat > "$MONITORING_DIR/prometheus.yml" << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'printer-saas'

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'printer-saas-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s

  - job_name: 'celery-worker'
    static_configs:
      - targets: ['celery-worker:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
EOF

    log "Prometheus configuration created"
}

create_alert_rules() {
    log "Creating Prometheus alert rules..."
    
    cat > "$MONITORING_DIR/alert_rules.yml" << 'EOF'
groups:
  - name: printer-saas-alerts
    rules:
      # Application Health Alerts
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "Service {{ $labels.instance }} has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      # Database Alerts
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Database connections high"
          description: "Database connection usage is above 80%"

      - alert: DatabaseDiskSpaceHigh
        expr: (pg_database_size_bytes / 1024 / 1024 / 1024) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database disk space high"
          description: "Database size is {{ $value }}GB"

      # Redis Alerts
      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Redis memory usage high"
          description: "Redis memory usage is above 90%"

      # Integration Alerts
      - alert: EtsyAPIError
        expr: increase(etsy_api_errors_total[5m]) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High Etsy API error rate"
          description: "{{ $value }} Etsy API errors in the last 5 minutes"

      - alert: ShopifyAPIError
        expr: increase(shopify_api_errors_total[5m]) > 10
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High Shopify API error rate"
          description: "{{ $value }} Shopify API errors in the last 5 minutes"

      # Business Logic Alerts
      - alert: OrderSyncFailure
        expr: increase(order_sync_failures_total[10m]) > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Order sync failures detected"
          description: "{{ $value }} order sync failures in the last 10 minutes"

      - alert: WebhookProcessingFailure
        expr: increase(webhook_processing_failures_total[10m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Webhook processing failures"
          description: "{{ $value }} webhook processing failures in the last 10 minutes"
EOF

    log "Alert rules created"
}

create_grafana_config() {
    log "Creating Grafana configuration..."
    
    mkdir -p "$MONITORING_DIR/grafana/provisioning/datasources"
    mkdir -p "$MONITORING_DIR/grafana/provisioning/dashboards"
    mkdir -p "$MONITORING_DIR/grafana/dashboards"
    
    # Datasource configuration
    cat > "$MONITORING_DIR/grafana/provisioning/datasources/datasources.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    # Dashboard provider configuration
    cat > "$MONITORING_DIR/grafana/provisioning/dashboards/dashboards.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    log "Grafana configuration created"
}

create_application_dashboard() {
    log "Creating application dashboard..."
    
    cat > "$MONITORING_DIR/grafana/dashboards/printer-saas-overview.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Printer SaaS Overview",
    "tags": ["printer-saas"],
    "timezone": "UTC",
    "panels": [
      {
        "title": "HTTP Requests per Second",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "stat",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Active Integrations",
        "type": "stat",
        "targets": [
          {
            "expr": "etsy_connected_shops",
            "legendFormat": "Etsy Shops"
          },
          {
            "expr": "shopify_connected_shops",
            "legendFormat": "Shopify Shops"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
EOF

    log "Application dashboard created"
}

create_integration_dashboard() {
    log "Creating integration dashboard..."
    
    cat > "$MONITORING_DIR/grafana/dashboards/integrations.json" << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "Integration Monitoring",
    "tags": ["printer-saas", "integrations"],
    "timezone": "UTC",
    "panels": [
      {
        "title": "Etsy API Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(etsy_api_requests_total[5m])",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "Shopify API Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(shopify_api_requests_total[5m])",
            "legendFormat": "{{endpoint}}"
          }
        ]
      },
      {
        "title": "API Error Rates",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(etsy_api_errors_total[5m])",
            "legendFormat": "Etsy Errors"
          },
          {
            "expr": "rate(shopify_api_errors_total[5m])",
            "legendFormat": "Shopify Errors"
          }
        ]
      },
      {
        "title": "Sync Operations",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(order_sync_total[5m])",
            "legendFormat": "Order Syncs"
          },
          {
            "expr": "rate(product_sync_total[5m])",
            "legendFormat": "Product Syncs"
          }
        ]
      }
    ],
    "time": {
      "from": "now-6h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
EOF

    log "Integration dashboard created"
}

setup_log_aggregation() {
    log "Setting up log aggregation configuration..."
    
    mkdir -p "$MONITORING_DIR/loki"
    
    cat > "$MONITORING_DIR/loki/config.yml" << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 168h

storage_config:
  boltdb:
    directory: /loki/index
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
EOF

    log "Log aggregation configuration created"
}

main() {
    log "Setting up monitoring for Printer SaaS..."
    
    create_prometheus_config
    create_alert_rules
    create_grafana_config
    create_application_dashboard
    create_integration_dashboard
    setup_log_aggregation
    
    log "Monitoring setup complete!"
    
    echo
    echo "=============================================================================="
    echo " MONITORING SETUP COMPLETE"
    echo "=============================================================================="
    echo
    echo "📊 Configuration files created:"
    echo "   Prometheus:     $MONITORING_DIR/prometheus.yml"
    echo "   Alert Rules:    $MONITORING_DIR/alert_rules.yml"
    echo "   Grafana Config: $MONITORING_DIR/grafana/"
    echo "   Dashboards:     $MONITORING_DIR/grafana/dashboards/"
    echo
    echo "🚀 To start monitoring:"
    echo "   ./deploy.sh development --monitoring"
    echo
    echo "🔗 Access URLs (after deployment):"
    echo "   Prometheus:     http://localhost:9090"
    echo "   Grafana:        http://localhost:3001 (admin/admin)"
    echo
    echo "📈 Available Dashboards:"
    echo "   - Printer SaaS Overview"
    echo "   - Integration Monitoring"
    echo
    echo "⚠️  Alert Rules Configured:"
    echo "   - Service health monitoring"
    echo "   - Database performance alerts"
    echo "   - Integration API error alerts"
    echo "   - Business logic failure alerts"
    echo
    echo "=============================================================================="
}

main "$@"