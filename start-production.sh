#!/bin/bash
# start-production.sh

set -euo pipefail

# Configuration
PROJECT_NAME="etsy-saas"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env.production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running on QNAP
check_qnap_environment() {
    if [[ ! -d "/share/Container" ]]; then
        error "This script is designed for QNAP Container Station environment"
        exit 1
    fi
    
    log "✅ QNAP Container Station environment detected"
}

# Pre-flight checks
pre_flight_checks() {
    log "🔍 Running pre-flight checks..."
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if required files exist
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    # Check available disk space (minimum 10GB)
    available_space=$(df /share/Container | awk 'NR==2 {print $4}')
    required_space=$((10 * 1024 * 1024))  # 10GB in KB
    
    if [[ $available_space -lt $required_space ]]; then
        error "Insufficient disk space. Required: 10GB, Available: $(($available_space / 1024 / 1024))GB"
        exit 1
    fi
    
    # Check available memory (minimum 4GB)
    available_memory=$(free -m | awk 'NR==2 {print $7}')
    required_memory=4096
    
    if [[ $available_memory -lt $required_memory ]]; then
        warning "Low available memory. Available: ${available_memory}MB, Recommended: ${required_memory}MB"
    fi
    
    log "✅ Pre-flight checks completed"
}

# Create necessary directories
setup_directories() {
    log "📁 Setting up directory structure..."
    
    directories=(
        "/share/Container/volumes/postgres"
        "/share/Container/volumes/redis"
        "/share/Container/volumes/minio"
        "/share/Container/volumes/prometheus"
        "/share/Container/volumes/grafana"
        "/share/Container/volumes/loki"
        "/share/Container/backups"
        "/share/Container/logs"
        "./letsencrypt"
        "./monitoring/prometheus"
        "./monitoring/grafana/provisioning/dashboards"
        "./monitoring/grafana/provisioning/datasources"
        "./monitoring/loki"
        "./monitoring/promtail"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        info "Created directory: $dir"
    done
    
    # Set proper permissions
    chmod -R 755 /share/Container/volumes
    chmod 600 ./letsencrypt
    
    log "✅ Directory structure setup completed"
}

# Generate monitoring configurations
setup_monitoring_config() {
    log "📊 Setting up monitoring configurations..."
    
    # Prometheus configuration
    cat > ./monitoring/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'etsy-services'
    static_configs:
      - targets: [
          'api-gateway:9090',
          'auth-service:9090',
          'etsy-service:9090',
          'design-service:9090',
          'analytics-service:9090'
        ]
    scrape_interval: 30s
    metrics_path: '/metrics'

  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']
EOF

    # Grafana datasource configuration
    mkdir -p ./monitoring/grafana/provisioning/datasources
    cat > ./monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: true
EOF

    # Loki configuration
    cat > ./monitoring/loki/config.yaml << EOF
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    instance_addr: 127.0.0.1
    kvstore:
      store: inmemory

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 100

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

ruler:
  alertmanager_url: http://localhost:9093

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

compactor:
  working_directory: /loki/boltdb-shipper-compactor
  shared_store: filesystem
  compaction_interval: 10m
  retention_enabled: true
  retention_delete_delay: 2h
  retention_delete_worker_count: 150

ingester:
  max_chunk_age: 1h
  chunk_idle_period: 30s
  chunk_block_size: 262144
  chunk_target_size: 1048576
  chunk_retain_period: 30s
  max_transfer_retries: 0
  wal:
    enabled: true
    dir: /loki/wal
EOF

    # Promtail configuration
    cat > ./monitoring/promtail/config.yml << EOF
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/log/containers/*.log

  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'logstream'
      - source_labels: ['__meta_docker_container_label_logging']
        target_label: 'logging'
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            message: message
            service: service
            tenant_id: tenant_id
      - timestamp:
          source: timestamp
          format: RFC3339Nano
      - labels:
          level:
          service:
          tenant_id:
EOF

    log "✅ Monitoring configuration setup completed"
}

# Database initialization
init_database() {
    log "🗄️ Initializing database..."
    
    # Create database initialization script
    cat > ./init-scripts/01-create-extensions.sql << EOF
-- Create necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create core schema
CREATE SCHEMA IF NOT EXISTS core;

-- Set up connection limits
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '512MB';
ALTER SYSTEM SET effective_cache_size = '2GB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

SELECT pg_reload_conf();
EOF

    cat > ./init-scripts/02-create-core-tables.sql << EOF
-- Core tenant management tables
CREATE TABLE IF NOT EXISTS core.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subdomain VARCHAR(63) UNIQUE NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    subscription_tier VARCHAR(50) DEFAULT 'starter',
    database_schema VARCHAR(63) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Etsy Integration
    etsy_shop_id VARCHAR(100),
    etsy_access_token TEXT,
    etsy_refresh_token TEXT,
    etsy_token_expires_at TIMESTAMP,
    
    -- Billing
    stripe_customer_id VARCHAR(100),
    billing_email VARCHAR(255),
    
    -- Settings
    settings JSONB DEFAULT '{}',
    
    CONSTRAINT valid_subdomain CHECK (subdomain ~ '^[a-z0-9][a-z0-9-]*[a-z0-9]network
    restart: unless-stopped

  # API Gateway
  api-gateway:
    build: 
      context: ./services/gateway
      dockerfile: Dockerfile.prod
    container_name: etsy-gateway
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/etsy_saas
      - JWT_SECRET=${JWT_SECRET}
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
        reservations:
          memory: 256M
          cpus: '0.5'
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api-gateway.rule=PathPrefix(`/api`)"
      - "traefik.http.routers.api-gateway.tls=true"
      - "traefik.http.routers.api-gateway.tls.certresolver=letsencrypt"
    depends_on:
      - postgres
      - redis
    networks:
      - etsy-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Authentication Service
  auth-service:
    build: 
      context: ./services/auth
      dockerfile: Dockerfile.prod
    container_name: etsy-auth
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/etsy_saas
      - REDIS_URL=redis://redis:6379/1
      - JWT_SECRET=${JWT_SECRET}
      - BCRYPT_ROUNDS=12
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    depends_on:
      - postgres
      - redis
    networks:
      - etsy-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Etsy Integration Service
  etsy-service:
    build: 
      context: ./services/etsy
      dockerfile: Dockerfile.prod
    container_name: etsy-integration
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/etsy_saas
      - REDIS_URL=redis://redis:6379/2
      - ETSY_API_BASE_URL=https://api.etsy.com/v3
      - ETSY_RATE_LIMIT_CALLS=10000
      - ETSY_RATE_LIMIT_WINDOW=3600
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    depends_on:
      - postgres
      - redis
    networks:
      - etsy-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Design Management Service
  design-service:
    build: 
      context: ./services/design
      dockerfile: Dockerfile.prod
    container_name: etsy-design
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/etsy_saas
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=${MINIO_ACCESS_KEY}
      - MINIO_SECRET_KEY=${MINIO_SECRET_KEY}
      - MINIO_SECURE=false
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
        reservations:
          memory: 1G
          cpus: '1.0'
    depends_on:
      - postgres
      - minio
    networks:
      - etsy-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Analytics Service
  analytics-service:
    build: 
      context: ./services/analytics
      dockerfile: Dockerfile.prod
    container_name: etsy-analytics
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/etsy_saas
      - REDIS_URL=redis://redis:6379/3
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    depends_on:
      - postgres
      - redis
    networks:
      - etsy-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Job Processing Workers
  job-worker:
    build: 
      context: ./services/jobs
      dockerfile: Dockerfile.prod
    container_name: etsy-worker
    environment:
      - DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/etsy_saas
      - REDIS_URL=redis://redis:6379/4
      - WORKER_CONCURRENCY=4
      - WORKER_MAX_MEMORY=1G
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    depends_on:
      - redis
      - postgres
    networks:
      - etsy-network
    restart: unless-stopped

  # Notification Service
  notification-service:
    build: 
      context: ./services/notifications
      dockerfile: Dockerfile.prod
    container_name: etsy-notifications
    environment:
      - REDIS_URL=redis://redis:6379/5
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
    depends_on:
      - redis
    networks:
      - etsy-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Infrastructure Services
  postgres:
    image: postgres:15
    container_name: etsy-postgres
    environment:
      - POSTGRES_DB=etsy_saas
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_SHARED_BUFFERS=512MB
      - POSTGRES_EFFECTIVE_CACHE_SIZE=2GB
      - POSTGRES_MAINTENANCE_WORK_MEM=128MB
      - POSTGRES_WAL_BUFFERS=16MB
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
      - ./postgres-config:/etc/postgresql/postgresql.conf
    ports:
      - "5432:5432"
    deploy:
      resources:
        limits:
          memory: 3G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    networks:
      - etsy-# Multi-Tenant Etsy Seller Automater Backend Architecture Deep Dive

## Executive Summary

This document outlines the backend architecture for transforming the existing Etsy Seller Automater into a scalable multi-tenant SaaS platform, leveraging Python and Go microservices deployed on QNAP TBS-464 NAS infrastructure.

## Current State Analysis

### Existing Architecture
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Authentication**: OAuth 2.0 with PKCE for Etsy API
- **Frontend**: React with Tailwind CSS
- **Deployment**: Docker Compose
- **Key Features**: 
  - Etsy shop analytics
  - Design management and mockup creation
  - Listing automation
  - Mask creator for product images

## Proposed Multi-Tenant Architecture

### 1. Service Architecture Overview