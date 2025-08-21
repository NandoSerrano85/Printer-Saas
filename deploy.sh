#!/bin/bash

# =============================================================================
# PRINTER SAAS DEPLOYMENT SCRIPT
# =============================================================================
# This script handles deployment of the Printer SaaS application with 
# Etsy and Shopify integrations
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="printer-saas"
DEFAULT_ENV="development"
REQUIRED_TOOLS=("docker" "docker-compose" "curl")

# Default values
ENVIRONMENT="${1:-$DEFAULT_ENV}"
SKIP_MIGRATIONS=false
SKIP_BUILD=false
MONITORING=false
DEVELOPMENT_TOOLS=false
FORCE_RECREATE=false

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

check_requirements() {
    log "Checking system requirements..."
    
    for tool in "${REQUIRED_TOOLS[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is required but not installed"
        fi
    done
    
    # Check Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running"
    fi
    
    log "System requirements satisfied"
}

validate_environment() {
    log "Validating environment configuration..."
    
    local env_file=""
    case "$ENVIRONMENT" in
        "development")
            env_file=".env.development"
            ;;
        "staging")
            env_file=".env.staging"
            ;;
        "production")
            env_file=".env.production"
            ;;
        *)
            env_file=".env"
            ;;
    esac
    
    if [[ -f "$env_file" ]]; then
        info "Using environment file: $env_file"
        export $(grep -v '^#' "$env_file" | xargs)
    else
        warn "Environment file $env_file not found, using defaults"
    fi
    
    # Validate required environment variables for production
    if [[ "$ENVIRONMENT" == "production" ]]; then
        local required_vars=(
            "DATABASE_PASSWORD"
            "JWT_SECRET_KEY"
            "SESSION_SECRET_KEY"
        )
        
        for var in "${required_vars[@]}"; do
            if [[ -z "${!var:-}" ]]; then
                error "Required environment variable $var is not set for production"
            fi
        done
        
        # Warn about missing API credentials
        if [[ -z "${ETSY_CLIENT_ID:-}" ]] || [[ -z "${ETSY_CLIENT_SECRET:-}" ]]; then
            warn "Etsy API credentials not set - Etsy integration will be disabled"
        fi
        
        if [[ -z "${SHOPIFY_CLIENT_ID:-}" ]] || [[ -z "${SHOPIFY_CLIENT_SECRET:-}" ]]; then
            warn "Shopify API credentials not set - Shopify integration will be disabled"
        fi
    fi
    
    log "Environment validation complete"
}

# =============================================================================
# INFRASTRUCTURE FUNCTIONS
# =============================================================================

setup_directories() {
    log "Setting up directory structure..."
    
    local dirs=(
        "backend/uploads"
        "backend/logs"
        "backend/temp"
        "monitoring"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
        "database/backups"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    # Set proper permissions
    chmod 755 backend/uploads backend/logs backend/temp
    
    log "Directory structure created"
}

setup_monitoring_config() {
    if [[ "$MONITORING" == true ]]; then
        log "Setting up monitoring configuration..."
        
        # Create Prometheus configuration
        cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files: []

scrape_configs:
  - job_name: 'printer-saas-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s
EOF

        # Create Grafana datasource configuration
        mkdir -p monitoring/grafana/datasources
        cat > monitoring/grafana/datasources/prometheus.yml << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

        log "Monitoring configuration created"
    fi
}

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

run_migrations() {
    if [[ "$SKIP_MIGRATIONS" == false ]]; then
        log "Running database migrations..."
        
        # Wait for database to be ready
        info "Waiting for database to be ready..."
        timeout 60 bash -c 'until docker-compose exec -T postgres pg_isready -U postgres; do sleep 2; done'
        
        # Run migrations
        docker-compose exec -T backend python -m database.migrations.migration_manager \
            --database-url "postgresql://postgres:${DATABASE_PASSWORD:-password}@postgres:5432/printer_saas" \
            migrate
        
        log "Database migrations completed"
    else
        info "Skipping database migrations"
    fi
}

backup_database() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log "Creating database backup..."
        
        local backup_file="database/backups/backup_$(date +%Y%m%d_%H%M%S).sql"
        
        docker-compose exec -T postgres pg_dump \
            -U postgres \
            -d printer_saas \
            --no-owner \
            --no-privileges \
            --clean \
            --if-exists > "$backup_file"
        
        # Compress backup
        gzip "$backup_file"
        
        log "Database backup created: $backup_file.gz"
        
        # Keep only last 10 backups
        ls -t database/backups/backup_*.sql.gz | tail -n +11 | xargs -r rm
    fi
}

# =============================================================================
# APPLICATION FUNCTIONS
# =============================================================================

build_application() {
    if [[ "$SKIP_BUILD" == false ]]; then
        log "Building application images..."
        
        local build_args=""
        if [[ "$FORCE_RECREATE" == true ]]; then
            build_args="--no-cache"
        fi
        
        docker-compose build $build_args
        
        log "Application images built successfully"
    else
        info "Skipping application build"
    fi
}

deploy_application() {
    log "Deploying application..."
    
    local compose_args=()
    
    # Add profile arguments based on configuration
    if [[ "$MONITORING" == true ]]; then
        compose_args+=("--profile" "monitoring")
    fi
    
    if [[ "$DEVELOPMENT_TOOLS" == true ]]; then
        compose_args+=("--profile" "development")
    fi
    
    # Deploy services
    if [[ "$FORCE_RECREATE" == true ]]; then
        docker-compose "${compose_args[@]}" up -d --force-recreate
    else
        docker-compose "${compose_args[@]}" up -d
    fi
    
    log "Application deployed successfully"
}

wait_for_services() {
    log "Waiting for services to be healthy..."
    
    local services=("postgres" "redis" "backend")
    local max_attempts=30
    local attempt=0
    
    for service in "${services[@]}"; do
        info "Waiting for $service to be healthy..."
        
        while [[ $attempt -lt $max_attempts ]]; do
            if docker-compose ps "$service" | grep -q "healthy\|Up"; then
                break
            fi
            
            sleep 5
            ((attempt++))
        done
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Service $service failed to become healthy"
        fi
        
        attempt=0
    done
    
    log "All services are healthy"
}

verify_deployment() {
    log "Verifying deployment..."
    
    # Check API health
    local api_url="http://localhost:${BACKEND_PORT:-8000}"
    local health_endpoint="$api_url/health"
    
    info "Checking API health at $health_endpoint"
    
    local response
    if response=$(curl -s -f "$health_endpoint"); then
        info "API health check passed"
        echo "$response" | jq . 2>/dev/null || echo "$response"
    else
        error "API health check failed"
    fi
    
    # Check API status
    local status_endpoint="$api_url/api/v1/status"
    info "Checking API status at $status_endpoint"
    
    if response=$(curl -s -f "$status_endpoint"); then
        info "API status check passed"
        echo "$response" | jq . 2>/dev/null || echo "$response"
    else
        warn "API status check failed"
    fi
    
    # Check integration endpoints
    local integrations=("etsy" "shopify")
    for integration in "${integrations[@]}"; do
        local integration_endpoint="$api_url/api/v1/$integration/health"
        if curl -s -f "$integration_endpoint" > /dev/null; then
            info "$integration integration is available"
        else
            warn "$integration integration endpoint is not responding"
        fi
    done
    
    log "Deployment verification complete"
}

# =============================================================================
# CLEANUP FUNCTIONS
# =============================================================================

cleanup_old_images() {
    log "Cleaning up old Docker images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old project images (keep last 3)
    docker images "$PROJECT_NAME*" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | \
        tail -n +2 | sort -k2 | head -n -3 | awk '{print $1}' | xargs -r docker rmi
    
    log "Docker cleanup complete"
}

# =============================================================================
# MAIN DEPLOYMENT FUNCTION
# =============================================================================

main() {
    log "Starting deployment for environment: $ENVIRONMENT"
    
    # Pre-deployment checks
    check_requirements
    validate_environment
    
    # Setup
    setup_directories
    setup_monitoring_config
    
    # Backup (production only)
    backup_database
    
    # Build and deploy
    build_application
    deploy_application
    
    # Post-deployment
    wait_for_services
    run_migrations
    verify_deployment
    
    # Cleanup
    cleanup_old_images
    
    log "Deployment completed successfully!"
    
    # Display access information
    echo
    echo "=============================================================================="
    echo " PRINTER SAAS DEPLOYMENT COMPLETE"
    echo "=============================================================================="
    echo
    echo "🚀 Application Access:"
    echo "   Backend API:    http://localhost:${BACKEND_PORT:-8000}"
    echo "   API Docs:       http://localhost:${BACKEND_PORT:-8000}/docs"
    echo "   Frontend:       http://localhost:${FRONTEND_PORT:-3000}"
    echo
    
    if [[ "$MONITORING" == true ]]; then
        echo "📊 Monitoring:"
        echo "   Prometheus:     http://localhost:${PROMETHEUS_PORT:-9090}"
        echo "   Grafana:        http://localhost:${GRAFANA_PORT:-3001}"
        echo
    fi
    
    if [[ "$DEVELOPMENT_TOOLS" == true ]]; then
        echo "🛠  Development Tools:"
        echo "   PgAdmin:        http://localhost:${PGADMIN_PORT:-5050}"
        echo "   Redis Commander: http://localhost:${REDIS_COMMANDER_PORT:-8081}"
        echo
    fi
    
    echo "🔗 Integration Endpoints:"
    echo "   Etsy OAuth:     http://localhost:${BACKEND_PORT:-8000}/api/v1/etsy/oauth/init"
    echo "   Shopify OAuth:  http://localhost:${BACKEND_PORT:-8000}/api/v1/shopify/oauth/init"
    echo
    echo "📝 Logs:"
    echo "   View logs:      docker-compose logs -f"
    echo "   Backend logs:   docker-compose logs -f backend"
    echo
    echo "⚙️  Management:"
    echo "   Stop:           docker-compose down"
    echo "   Restart:        ./deploy.sh $ENVIRONMENT"
    echo "   Update:         ./deploy.sh $ENVIRONMENT --force-recreate"
    echo
    echo "==============================================================================="
}

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

show_help() {
    cat << EOF
Printer SaaS Deployment Script

USAGE:
    $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENTS:
    development     Local development environment (default)
    staging         Staging environment
    production      Production environment

OPTIONS:
    --skip-migrations     Skip database migrations
    --skip-build          Skip Docker image building
    --monitoring          Deploy monitoring stack (Prometheus, Grafana)
    --development-tools   Deploy development tools (PgAdmin, Redis Commander)
    --force-recreate      Force recreate all containers
    --help               Show this help message

EXAMPLES:
    $0                                    # Deploy development environment
    $0 production                         # Deploy production environment
    $0 development --monitoring           # Deploy with monitoring
    $0 staging --skip-migrations          # Deploy staging without migrations
    $0 production --force-recreate        # Force recreate production deployment

REQUIREMENTS:
    - Docker and Docker Compose
    - curl (for health checks)
    - Environment file (.env.{environment} or .env)

ENVIRONMENT VARIABLES:
    DATABASE_PASSWORD     Database password
    JWT_SECRET_KEY       JWT secret key
    SESSION_SECRET_KEY   Session secret key
    ETSY_CLIENT_ID       Etsy API client ID
    ETSY_CLIENT_SECRET   Etsy API client secret
    SHOPIFY_CLIENT_ID    Shopify API client ID
    SHOPIFY_CLIENT_SECRET Shopify API client secret

For more information, see README.md
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-migrations)
            SKIP_MIGRATIONS=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --monitoring)
            MONITORING=true
            shift
            ;;
        --development-tools)
            DEVELOPMENT_TOOLS=true
            shift
            ;;
        --force-recreate)
            FORCE_RECREATE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        -*)
            error "Unknown option $1"
            ;;
        *)
            # Assume it's an environment if no other args processed
            if [[ "$1" != "$ENVIRONMENT" ]]; then
                ENVIRONMENT="$1"
            fi
            shift
            ;;
    esac
done

# =============================================================================
# SCRIPT EXECUTION
# =============================================================================

# Change to script directory
cd "$SCRIPT_DIR"

# Run main deployment
main "$@"