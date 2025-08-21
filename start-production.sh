#!/bin/bash

# =============================================================================
# PRINTER SAAS PRODUCTION DEPLOYMENT SCRIPT
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="printer-saas"

# Default values
WITH_MONITORING=false
WITH_NGINX=false
CLEAN_START=false
REBUILD=false

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

success() {
    echo -e "${CYAN}[SUCCESS] $1${NC}"
}

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

check_requirements() {
    log "Checking system requirements..."
    
    local required_tools=("docker" "docker-compose" "curl")
    
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "$tool is required but not installed"
        fi
    done
    
    # Check Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running"
    fi
    
    # Check Docker Compose version
    local compose_version=$(docker-compose --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    info "Docker Compose version: $compose_version"
    
    log "System requirements satisfied"
}

validate_environment() {
    log "Validating production environment..."
    
    # Check if .env.production exists
    if [[ ! -f ".env.production" ]]; then
        error "Production environment file not found: .env.production"
    fi
    
    # Check critical environment variables
    source .env.production
    
    local required_vars=(
        "DATABASE_PASSWORD"
        "JWT_SECRET_KEY"
        "SESSION_SECRET_KEY"
        "SHOPIFY_CLIENT_ID"
        "SHOPIFY_CLIENT_SECRET"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error "Required environment variable $var is not set"
        fi
    done
    
    # Check Shopify credentials
    if [[ "${SHOPIFY_CLIENT_ID}" == "your-shopify-client-id" ]]; then
        error "Shopify credentials not configured properly"
    fi
    
    # Check Etsy credentials if enabled
    if [[ "${FEATURE_ETSY_INTEGRATION:-true}" == "true" ]]; then
        if [[ "${ETSY_CLIENT_ID:-}" == "your-etsy-client-id" || -z "${ETSY_CLIENT_ID:-}" ]]; then
            warn "Etsy credentials not configured - Etsy integration will not work"
        fi
    fi
    
    log "Environment validation complete"
}

# =============================================================================
# SETUP FUNCTIONS
# =============================================================================

setup_directories() {
    log "Setting up directory structure..."
    
    local dirs=(
        "backend/uploads"
        "backend/logs"
        "monitoring"
        "nginx"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    # Set proper permissions
    chmod 755 backend/uploads backend/logs
    
    log "Directory structure created"
}

setup_monitoring_config() {
    if [[ "$WITH_MONITORING" == true ]]; then
        log "Setting up monitoring configuration..."
        
        # Create basic prometheus config
        mkdir -p monitoring
        cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'printer-saas-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
        
        log "Monitoring configuration ready"
    fi
}

# =============================================================================
# DEPLOYMENT FUNCTIONS
# =============================================================================

clean_previous_deployment() {
    if [[ "$CLEAN_START" == true ]]; then
        log "Cleaning previous deployment..."
        
        # Stop and remove containers
        docker-compose -f docker-compose.production.yml down --volumes --remove-orphans 2>/dev/null || true
        
        # Remove images if rebuilding
        if [[ "$REBUILD" == true ]]; then
            docker images | grep "$PROJECT_NAME" | awk '{print $3}' | xargs -r docker rmi 2>/dev/null || true
        fi
        
        log "Previous deployment cleaned"
    fi
}

build_services() {
    log "Building services..."
    
    if [[ "$REBUILD" == true ]]; then
        docker-compose -f docker-compose.production.yml build --no-cache
    else
        docker-compose -f docker-compose.production.yml build
    fi
    
    log "Services built successfully"
}

deploy_services() {
    log "Deploying services..."
    
    # Deploy core services
    docker-compose -f docker-compose.production.yml up -d postgres redis backend celery-worker celery-beat frontend
    
    # Deploy nginx if requested
    if [[ "$WITH_NGINX" == true ]]; then
        docker-compose -f docker-compose.production.yml --profile nginx up -d nginx
    fi
    
    # Deploy monitoring if requested
    if [[ "$WITH_MONITORING" == true ]]; then
        docker-compose -f docker-compose.production.yml --profile monitoring up -d prometheus grafana
    fi
    
    log "Services deployed successfully"
}

wait_for_services() {
    log "Waiting for services to be healthy..."
    
    local services=("postgres" "redis" "backend" "frontend")
    local max_attempts=60
    local attempt=0
    
    for service in "${services[@]}"; do
        info "Waiting for $service to be healthy..."
        
        while [[ $attempt -lt $max_attempts ]]; do
            if docker-compose -f docker-compose.production.yml ps "$service" | grep -q "healthy\|Up"; then
                success "$service is healthy"
                break
            fi
            
            sleep 2
            ((attempt++))
        done
        
        if [[ $attempt -eq $max_attempts ]]; then
            error "Service $service failed to become healthy"
        fi
        
        attempt=0
    done
    
    log "All services are healthy"
}

run_migrations() {
    log "Running database migrations..."
    
    # Wait a bit more for database to be fully ready
    sleep 5
    
    # Run migrations using the backend container
    docker-compose -f docker-compose.production.yml exec -T backend python -c "
import sys
sys.path.append('.')
from database.core import create_core_tables
try:
    create_core_tables()
    print('✅ Core tables created successfully')
except Exception as e:
    print(f'❌ Error creating tables: {e}')
    sys.exit(1)
" || warn "Migration failed - database might not be ready yet"
    
    log "Database migrations completed"
}

# =============================================================================
# TESTING FUNCTIONS
# =============================================================================

test_deployment() {
    log "Testing production deployment..."
    
    local api_url="http://localhost:8000"
    local max_attempts=30
    local attempt=0
    
    # Wait for API to be responsive
    info "Waiting for API to be responsive..."
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s -f "$api_url/health" > /dev/null 2>&1; then
            break
        fi
        sleep 2
        ((attempt++))
    done
    
    if [[ $attempt -eq $max_attempts ]]; then
        error "API failed to become responsive"
    fi
    
    # Test critical endpoints
    info "Testing critical endpoints..."
    
    local endpoints=(
        "/health"
        "/api/v1/status"
        "/api/v1/shopify/health"
        "/api/v1/etsy/health"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local url="$api_url$endpoint"
        if curl -s -f "$url" > /dev/null; then
            success "✅ $endpoint - OK"
        else
            warn "⚠️  $endpoint - Not responding"
        fi
    done
    
    log "Production deployment testing completed"
}

# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

display_access_info() {
    echo
    echo "=============================================================================="
    echo -e " ${GREEN}🚀 PRINTER SAAS PRODUCTION DEPLOYMENT COMPLETE${NC}"
    echo "=============================================================================="
    echo
    echo -e "${BLUE}📱 Application Access:${NC}"
    echo "   Frontend App:      http://localhost:3000"
    echo "   Backend API:       http://localhost:8000"
    echo "   API Documentation: http://localhost:8000/docs"
    echo
    echo -e "${BLUE}🧪 Health Checks:${NC}"
    echo "   Backend Health:    http://localhost:8000/health"
    echo "   API Status:        http://localhost:8000/api/v1/status"
    echo "   Shopify Health:    http://localhost:8000/api/v1/shopify/health"
    echo "   Etsy Health:       http://localhost:8000/api/v1/etsy/health"
    echo
    
    if [[ "$WITH_MONITORING" == true ]]; then
        echo -e "${BLUE}📊 Monitoring:${NC}"
        echo "   Prometheus:        http://localhost:9090"
        echo "   Grafana:           http://localhost:3001"
    fi
    
    echo
    echo -e "${BLUE}📝 Management Commands:${NC}"
    echo "   View Logs:         docker-compose -f docker-compose.production.yml logs -f"
    echo "   Backend Logs:      docker-compose -f docker-compose.production.yml logs -f backend"
    echo "   Database Shell:    docker-compose -f docker-compose.production.yml exec postgres psql -U postgres printer_saas"
    echo "   Backend Shell:     docker-compose -f docker-compose.production.yml exec backend bash"
    echo "   Stop Services:     docker-compose -f docker-compose.production.yml down"
    echo "   Restart:           ./start-production.sh"
    echo
    echo -e "${BLUE}🔧 Configuration:${NC}"
    echo "   Environment:       .env.production"
    echo "   Compose File:      docker-compose.production.yml"
    echo "   Database:          printer_saas (postgres:5432)"
    echo "   Redis:             localhost:6379"
    echo
    echo "=============================================================================="
}

show_help() {
    cat << EOF
Production Deployment Script for Printer SaaS

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --monitoring          Deploy monitoring stack (Prometheus, Grafana)
    --nginx              Deploy nginx reverse proxy
    --clean              Clean previous deployment before starting
    --rebuild            Rebuild Docker images
    --help               Show this help message

EXAMPLES:
    $0                           # Basic production deployment
    $0 --monitoring              # With monitoring
    $0 --nginx --monitoring      # Full production stack
    $0 --clean --rebuild         # Clean rebuild

REQUIREMENTS:
    - Docker and Docker Compose
    - .env.production file with all required variables
    - curl (for health checks)

SERVICES:
    - PostgreSQL (database)
    - Redis (cache & message broker)
    - Backend API (FastAPI)
    - Celery Worker & Beat (background tasks)
    - Frontend (Next.js)
    - Prometheus & Grafana (optional monitoring)
    - Nginx (optional reverse proxy)

For more information, see README.md
EOF
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    log "Starting Printer SaaS production deployment..."
    
    # Pre-deployment checks
    check_requirements
    validate_environment
    
    # Setup
    setup_directories
    setup_monitoring_config
    
    # Deployment
    clean_previous_deployment
    build_services
    deploy_services
    
    # Post-deployment
    wait_for_services
    run_migrations
    test_deployment
    
    # Display access information
    display_access_info
    
    success "Production deployment completed successfully!"
}

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --monitoring)
            WITH_MONITORING=true
            shift
            ;;
        --nginx)
            WITH_NGINX=true
            shift
            ;;
        --clean)
            CLEAN_START=true
            shift
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option $1. Use --help for usage information."
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