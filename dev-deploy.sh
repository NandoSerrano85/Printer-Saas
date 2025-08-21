#!/bin/bash

# =============================================================================
# PRINTER SAAS DEVELOPMENT DEPLOYMENT SCRIPT
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
PROJECT_NAME="printer-saas-dev"

# Default values
WITH_MONITORING=false
WITH_DEV_TOOLS=true
WITH_MOCK_SERVICES=false
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
    log "Validating development environment..."
    
    # Check if .env.development exists
    if [[ ! -f ".env.development" ]]; then
        warn ".env.development not found, using .env"
        if [[ ! -f ".env" ]]; then
            error "No environment file found. Please create .env.development or .env"
        fi
    fi
    
    # Check Shopify credentials
    if grep -q "2f764b0cf8afa8e196e1c7a8b586ca3b" .env.development 2>/dev/null; then
        success "Shopify credentials found in environment"
    else
        warn "Shopify credentials not found - Shopify integration will not work"
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
        "backend/temp"
        "monitoring"
    )
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    # Set proper permissions
    chmod 755 backend/uploads backend/logs backend/temp
    
    log "Directory structure created"
}

setup_monitoring_config() {
    if [[ "$WITH_MONITORING" == true ]]; then
        log "Setting up monitoring configuration..."
        
        # Run the monitoring setup script if it exists
        if [[ -f "scripts/setup-monitoring.sh" ]]; then
            ./scripts/setup-monitoring.sh
        else
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
EOF
        fi
        
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
        docker-compose -f docker-compose.dev.yml down --volumes --remove-orphans 2>/dev/null || true
        
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
        docker-compose -f docker-compose.dev.yml build --no-cache
    else
        docker-compose -f docker-compose.dev.yml build
    fi
    
    log "Services built successfully"
}

deploy_services() {
    log "Deploying services..."
    
    # Deploy core services
    docker-compose -f docker-compose.dev.yml up -d postgres redis backend celery-worker frontend
    
    # Deploy development tools if requested
    if [[ "$WITH_DEV_TOOLS" == true ]]; then
        docker-compose -f docker-compose.dev.yml up -d pgadmin redis-commander
    fi
    
    # Deploy monitoring if requested
    if [[ "$WITH_MONITORING" == true ]]; then
        docker-compose -f docker-compose.dev.yml up -d prometheus grafana
    fi
    
    # Deploy mock services if requested
    if [[ "$WITH_MOCK_SERVICES" == true ]]; then
        docker-compose -f docker-compose.dev.yml up -d mailhog
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
            if docker-compose -f docker-compose.dev.yml ps "$service" | grep -q "healthy\|Up"; then
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
    docker-compose -f docker-compose.dev.yml exec -T backend python -c "
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
    log "Testing deployment..."
    
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
    
    # Test health endpoints
    info "Testing health endpoints..."
    
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
    
    log "Deployment testing completed"
}

# =============================================================================
# DISPLAY FUNCTIONS
# =============================================================================

display_access_info() {
    echo
    echo "=============================================================================="
    echo -e " ${GREEN}🚀 PRINTER SAAS DEVELOPMENT DEPLOYMENT COMPLETE${NC}"
    echo "=============================================================================="
    echo
    echo -e "${BLUE}📱 Application Access:${NC}"
    echo "   Frontend App:      http://localhost:3000"
    echo "   Backend API:       http://localhost:8000"
    echo "   API Documentation: http://localhost:8000/docs"
    echo "   Interactive Docs:  http://localhost:8000/redoc"
    echo
    echo -e "${BLUE}🧪 Integration Testing:${NC}"
    echo "   Shopify Health:    http://localhost:8000/api/v1/shopify/health"
    echo "   Shopify OAuth:     http://localhost:8000/api/v1/shopify/oauth/init"
    echo "   Etsy Health:       http://localhost:8000/api/v1/etsy/health"
    echo "   Etsy OAuth:        http://localhost:8000/api/v1/etsy/oauth/init"
    echo
    
    if [[ "$WITH_DEV_TOOLS" == true ]]; then
        echo -e "${BLUE}🛠  Development Tools:${NC}"
        echo "   PgAdmin:           http://localhost:5050 (admin@printersaas.dev / admin123)"
        echo "   Redis Commander:   http://localhost:8081"
    fi
    
    if [[ "$WITH_MONITORING" == true ]]; then
        echo -e "${BLUE}📊 Monitoring:${NC}"
        echo "   Prometheus:        http://localhost:9090"
        echo "   Grafana:           http://localhost:3001 (admin / admin123)"
    fi
    
    if [[ "$WITH_MOCK_SERVICES" == true ]]; then
        echo -e "${BLUE}📧 Mock Services:${NC}"
        echo "   MailHog:           http://localhost:8025"
    fi
    
    echo
    echo -e "${BLUE}🔗 Quick Test Commands:${NC}"
    echo "   Health Check:      curl http://localhost:8000/health"
    echo "   API Status:        curl http://localhost:8000/api/v1/status"
    echo "   Shopify Test:      curl http://localhost:8000/api/v1/shopify/health"
    echo
    echo -e "${BLUE}📝 Useful Commands:${NC}"
    echo "   View Logs:         docker-compose -f docker-compose.dev.yml logs -f"
    echo "   Backend Logs:      docker-compose -f docker-compose.dev.yml logs -f backend"
    echo "   Database Shell:    docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres printer_saas"
    echo "   Backend Shell:     docker-compose -f docker-compose.dev.yml exec backend bash"
    echo "   Stop Services:     docker-compose -f docker-compose.dev.yml down"
    echo "   Restart:           ./dev-deploy.sh"
    echo
    echo -e "${BLUE}🔧 Configuration:${NC}"
    echo "   Environment:       .env.development"
    echo "   Compose File:      docker-compose.dev.yml"
    echo "   Database:          printer_saas (postgres:5432)"
    echo "   Redis:             localhost:6379"
    echo
    echo "=============================================================================="
}

show_help() {
    cat << EOF
Development Deployment Script for Printer SaaS

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --monitoring          Deploy monitoring stack (Prometheus, Grafana)
    --no-dev-tools        Skip development tools (PgAdmin, Redis Commander)
    --mock-services       Deploy mock services (MailHog, etc.)
    --clean               Clean previous deployment before starting
    --rebuild             Rebuild Docker images
    --help               Show this help message

EXAMPLES:
    $0                           # Basic development deployment
    $0 --monitoring              # With monitoring
    $0 --clean --rebuild         # Clean rebuild
    $0 --monitoring --mock-services --clean  # Full development stack

REQUIREMENTS:
    - Docker and Docker Compose
    - curl (for health checks)

SERVICES:
    - PostgreSQL (database)
    - Redis (cache & message broker)
    - Backend API (FastAPI)
    - Celery Worker (background tasks)
    - PgAdmin (database management)
    - Redis Commander (Redis management)

For more information, see DEPLOYMENT.md
EOF
}

# =============================================================================
# MAIN FUNCTION
# =============================================================================

main() {
    log "Starting Printer SaaS development deployment..."
    
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
    
    success "Development deployment completed successfully!"
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
        --no-dev-tools)
            WITH_DEV_TOOLS=false
            shift
            ;;
        --mock-services)
            WITH_MOCK_SERVICES=true
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