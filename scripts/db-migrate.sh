#!/bin/bash

# =============================================================================
# DATABASE MIGRATION UTILITY SCRIPT
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}"; exit 1; }

# Default values
ENVIRONMENT="${1:-development}"
COMMAND="${2:-migrate}"
TARGET_VERSION="${3:-}"

# Load environment
case "$ENVIRONMENT" in
    "development"|"dev")
        ENV_FILE="$PROJECT_DIR/.env.development"
        DATABASE_URL="postgresql://postgres:password@localhost:5432/printer_saas"
        ;;
    "staging")
        ENV_FILE="$PROJECT_DIR/.env.staging"
        DATABASE_URL="${DATABASE_URL:-postgresql://postgres:password@staging-db:5432/printer_saas}"
        ;;
    "production"|"prod")
        ENV_FILE="$PROJECT_DIR/.env.production"
        DATABASE_URL="${DATABASE_URL:-postgresql://postgres:password@prod-db:5432/printer_saas}"
        ;;
    *)
        error "Unknown environment: $ENVIRONMENT"
        ;;
esac

# Load environment file if it exists
if [[ -f "$ENV_FILE" ]]; then
    log "Loading environment from $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Override DATABASE_URL if provided in environment
if [[ -n "${DATABASE_URL:-}" ]]; then
    log "Using database URL from environment"
fi

# Migration commands
case "$COMMAND" in
    "migrate"|"up")
        log "Running migrations..."
        if [[ -n "$TARGET_VERSION" ]]; then
            log "Migrating to version: $TARGET_VERSION"
            python "$PROJECT_DIR/backend/database/migrations/migration_manager.py" \
                --database-url "$DATABASE_URL" \
                migrate --target "$TARGET_VERSION"
        else
            log "Migrating to latest version"
            python "$PROJECT_DIR/backend/database/migrations/migration_manager.py" \
                --database-url "$DATABASE_URL" \
                migrate
        fi
        ;;
    
    "rollback"|"down")
        if [[ -z "$TARGET_VERSION" ]]; then
            error "Target version required for rollback"
        fi
        log "Rolling back to version: $TARGET_VERSION"
        python "$PROJECT_DIR/backend/database/migrations/migration_manager.py" \
            --database-url "$DATABASE_URL" \
            rollback --target "$TARGET_VERSION"
        ;;
    
    "status"|"list")
        log "Checking migration status..."
        python "$PROJECT_DIR/backend/database/migrations/migration_manager.py" \
            --database-url "$DATABASE_URL" \
            list
        ;;
    
    "info")
        log "Getting migration info..."
        python "$PROJECT_DIR/backend/database/migrations/migration_manager.py" \
            --database-url "$DATABASE_URL" \
            info
        ;;
    
    "create-tenant")
        if [[ -z "$TARGET_VERSION" ]]; then
            error "Tenant ID required for create-tenant command"
        fi
        local tenant_id="$TARGET_VERSION"
        local schema_name="tenant_${tenant_id}"
        log "Creating tenant: $tenant_id with schema: $schema_name"
        python "$PROJECT_DIR/backend/database/migrations/migration_manager.py" \
            --database-url "$DATABASE_URL" \
            create-tenant --tenant-id "$tenant_id" --schema-name "$schema_name"
        ;;
    
    "help")
        cat << EOF
Database Migration Utility

USAGE:
    $0 [ENVIRONMENT] [COMMAND] [TARGET_VERSION]

ENVIRONMENTS:
    development (default)   Local development database
    staging                 Staging database
    production              Production database

COMMANDS:
    migrate, up             Run all pending migrations (default)
    rollback, down          Rollback to target version
    status, list            Show migration status
    info                    Show migration information
    create-tenant           Create new tenant schema
    help                    Show this help

EXAMPLES:
    $0 development migrate              # Run all pending migrations
    $0 production migrate 003          # Migrate to version 003
    $0 staging rollback 002            # Rollback to version 002
    $0 development status              # Show migration status
    $0 development create-tenant acme  # Create tenant 'acme'

ENVIRONMENT VARIABLES:
    DATABASE_URL           Override database connection URL
EOF
        ;;
    
    *)
        error "Unknown command: $COMMAND. Use '$0 help' for usage information"
        ;;
esac

log "Database operation completed successfully"