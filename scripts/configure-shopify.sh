#!/bin/bash

# =============================================================================
# SHOPIFY CONFIGURATION HELPER SCRIPT
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }
info() { echo -e "${BLUE}[INFO] $1${NC}"; }
warn() { echo -e "${YELLOW}[WARNING] $1${NC}"; }
error() { echo -e "${RED}[ERROR] $1${NC}"; exit 1; }

# Configuration variables
SHOPIFY_CLIENT_ID=""
SHOPIFY_CLIENT_SECRET=""
SHOPIFY_REDIRECT_URI=""
SHOPIFY_WEBHOOK_ENDPOINT=""
SHOPIFY_WEBHOOK_SECRET=""
TEST_STORE_URL=""
ENVIRONMENT="development"

show_help() {
    cat << 'EOF'
Shopify Configuration Helper

This script helps configure your Shopify integration with your Partner app credentials.

USAGE:
    ./configure-shopify.sh [OPTIONS]

OPTIONS:
    --client-id CLIENT_ID       Shopify app API key
    --client-secret SECRET      Shopify app secret key  
    --redirect-uri URI          OAuth redirect URI
    --webhook-endpoint URI      Webhook endpoint URI
    --webhook-secret SECRET     Webhook HMAC secret
    --test-store URL            Test store URL (.myshopify.com)
    --environment ENV           Environment (development/staging/production)
    --interactive               Interactive configuration mode
    --help                      Show this help message

EXAMPLES:
    # Interactive mode (recommended)
    ./configure-shopify.sh --interactive
    
    # Direct configuration
    ./configure-shopify.sh \
        --client-id "your_client_id" \
        --client-secret "your_secret" \
        --redirect-uri "http://localhost:8000/api/v1/shopify/oauth/callback"

EOF
}

interactive_setup() {
    log "Starting interactive Shopify configuration..."
    echo
    
    # Get credentials
    echo -e "${BLUE}📋 Shopify App Credentials${NC}"
    echo "From your Partner Dashboard → Apps → [Your App] → App info"
    echo
    read -p "Shopify Client ID (API Key): " SHOPIFY_CLIENT_ID
    read -s -p "Shopify Client Secret: " SHOPIFY_CLIENT_SECRET
    echo
    echo
    
    # Get domain configuration
    echo -e "${BLUE}🌐 Domain Configuration${NC}"
    echo "Choose your setup:"
    echo "1) Local development (http://localhost:8000)"
    echo "2) Ngrok tunnel (for external testing)"
    echo "3) Custom domain"
    echo
    read -p "Choice (1-3): " domain_choice
    
    case $domain_choice in
        1)
            SHOPIFY_REDIRECT_URI="http://localhost:8000/api/v1/shopify/oauth/callback"
            SHOPIFY_WEBHOOK_ENDPOINT="http://localhost:8000/api/v1/shopify/webhooks"
            ;;
        2)
            read -p "Enter your ngrok URL (e.g., https://abc123.ngrok.io): " ngrok_url
            SHOPIFY_REDIRECT_URI="${ngrok_url}/api/v1/shopify/oauth/callback"
            SHOPIFY_WEBHOOK_ENDPOINT="${ngrok_url}/api/v1/shopify/webhooks"
            ;;
        3)
            read -p "Enter your domain (e.g., https://yourdomain.com): " custom_domain
            SHOPIFY_REDIRECT_URI="${custom_domain}/api/v1/shopify/oauth/callback"
            SHOPIFY_WEBHOOK_ENDPOINT="${custom_domain}/api/v1/shopify/webhooks"
            ;;
        *)
            error "Invalid choice"
            ;;
    esac
    
    # Generate webhook secret
    echo
    echo -e "${BLUE}🔐 Security Configuration${NC}"
    read -p "Generate random webhook secret? (y/n): " generate_secret
    if [[ "$generate_secret" =~ ^[Yy] ]]; then
        SHOPIFY_WEBHOOK_SECRET=$(openssl rand -hex 32)
        info "Generated webhook secret: $SHOPIFY_WEBHOOK_SECRET"
    else
        read -p "Enter webhook secret (or press Enter to generate): " SHOPIFY_WEBHOOK_SECRET
        if [[ -z "$SHOPIFY_WEBHOOK_SECRET" ]]; then
            SHOPIFY_WEBHOOK_SECRET=$(openssl rand -hex 32)
            info "Generated webhook secret: $SHOPIFY_WEBHOOK_SECRET"
        fi
    fi
    
    # Test store
    echo
    echo -e "${BLUE}🏪 Test Store Configuration${NC}"
    read -p "Test store URL (e.g., mystore.myshopify.com): " TEST_STORE_URL
    
    # Environment
    echo
    echo -e "${BLUE}⚙️ Environment Configuration${NC}"
    read -p "Environment (development/staging/production) [development]: " env_input
    ENVIRONMENT="${env_input:-development}"
}

validate_configuration() {
    log "Validating configuration..."
    
    local errors=0
    
    if [[ -z "$SHOPIFY_CLIENT_ID" ]]; then
        error "Shopify Client ID is required"
        ((errors++))
    fi
    
    if [[ -z "$SHOPIFY_CLIENT_SECRET" ]]; then
        error "Shopify Client Secret is required"
        ((errors++))
    fi
    
    if [[ -z "$SHOPIFY_REDIRECT_URI" ]]; then
        error "Redirect URI is required"
        ((errors++))
    fi
    
    if [[ ! "$SHOPIFY_REDIRECT_URI" =~ ^https?:// ]]; then
        error "Redirect URI must start with http:// or https://"
        ((errors++))
    fi
    
    if [[ $errors -gt 0 ]]; then
        error "Configuration validation failed with $errors errors"
    fi
    
    log "Configuration validation passed"
}

update_environment_file() {
    local env_file="$PROJECT_DIR/.env.$ENVIRONMENT"
    
    log "Updating environment file: $env_file"
    
    # Create backup
    if [[ -f "$env_file" ]]; then
        cp "$env_file" "$env_file.backup.$(date +%s)"
        info "Created backup: $env_file.backup.$(date +%s)"
    fi
    
    # Update or create environment file
    {
        echo "# Shopify Integration Configuration"
        echo "# Generated on $(date)"
        echo
        echo "# Shopify API Credentials"
        echo "SHOPIFY_CLIENT_ID=\"$SHOPIFY_CLIENT_ID\""
        echo "SHOPIFY_CLIENT_SECRET=\"$SHOPIFY_CLIENT_SECRET\""
        echo
        echo "# OAuth Configuration"
        echo "SHOPIFY_OAUTH_REDIRECT_URI=\"$SHOPIFY_REDIRECT_URI\""
        echo "SHOPIFY_OAUTH_SCOPES=\"read_products,write_products,read_orders,write_orders,read_customers,write_customers,read_inventory,write_inventory,read_files\""
        echo
        echo "# Webhook Configuration"
        echo "SHOPIFY_WEBHOOK_ENDPOINT=\"$SHOPIFY_WEBHOOK_ENDPOINT\""
        echo "SHOPIFY_WEBHOOK_SECRET=\"$SHOPIFY_WEBHOOK_SECRET\""
        echo
        echo "# Feature Flags"
        echo "FEATURE_SHOPIFY_INTEGRATION=true"
        echo "FEATURE_BATCH_OPERATIONS=true"
        echo "FEATURE_WEBHOOK_PROCESSING=true"
        echo
        if [[ -n "$TEST_STORE_URL" ]]; then
            echo "# Test Store"
            echo "SHOPIFY_TEST_STORE_URL=\"$TEST_STORE_URL\""
            echo
        fi
    } >> "$env_file"
    
    log "Environment file updated successfully"
}

create_partner_dashboard_instructions() {
    local instructions_file="$PROJECT_DIR/SHOPIFY_PARTNER_SETUP.md"
    
    log "Creating Partner Dashboard setup instructions..."
    
    cat > "$instructions_file" << EOF
# Shopify Partner Dashboard Configuration

## 🔧 **App Settings to Configure**

### **1. App Info**
\`\`\`
App URL: $(echo "$SHOPIFY_REDIRECT_URI" | sed 's|/api/v1/shopify/oauth/callback||')
Contact email: your-email@domain.com
\`\`\`

### **2. App Setup → Allowed redirection URLs**
Add this URL to your allowed redirection URLs:
\`\`\`
$SHOPIFY_REDIRECT_URI
\`\`\`

### **3. App Setup → Webhooks**
Configure webhooks with these settings:

**Webhook endpoint URL:**
\`\`\`
$SHOPIFY_WEBHOOK_ENDPOINT
\`\`\`

**Webhook format:** JSON

**Webhook version:** 2023-10

**Events to subscribe to:**
- orders/create
- orders/updated  
- orders/paid
- orders/cancelled
- products/create
- products/update
- app/uninstalled

### **4. App Setup → App permissions**
Request these scopes:
- read_products
- write_products  
- read_orders
- write_orders
- read_customers
- write_customers
- read_inventory
- write_inventory
- read_files

## 🧪 **Testing Your Setup**

### **1. Start the application**
\`\`\`bash
./deploy.sh $ENVIRONMENT
\`\`\`

### **2. Test OAuth flow**
Visit: \`$(echo "$SHOPIFY_REDIRECT_URI" | sed 's|/oauth/callback|/oauth/init|')\`

### **3. Check integration status**
\`\`\`bash
curl "$(echo "$SHOPIFY_REDIRECT_URI" | sed 's|/api/v1/shopify/oauth/callback||')/api/v1/shopify/health"
\`\`\`

## 🔗 **Important URLs**

- **OAuth Init**: \`$(echo "$SHOPIFY_REDIRECT_URI" | sed 's|/oauth/callback|/oauth/init|')\`
- **OAuth Callback**: \`$SHOPIFY_REDIRECT_URI\`
- **Webhook Endpoint**: \`$SHOPIFY_WEBHOOK_ENDPOINT\`
- **Health Check**: \`$(echo "$SHOPIFY_REDIRECT_URI" | sed 's|/api/v1/shopify/oauth/callback||')/api/v1/shopify/health\`

$(if [[ -n "$TEST_STORE_URL" ]]; then
echo "## 🏪 **Test Store**"
echo ""
echo "Your test store: \`https://$TEST_STORE_URL\`"
echo ""
echo "To install your app on the test store:"
echo "1. Go to Partner Dashboard → Apps → [Your App]"
echo "2. Click 'Select store' and choose your test store"
echo "3. Click 'Install app'"
fi)

## 🔐 **Security Information**

**Webhook Secret (HMAC verification):**
\`\`\`
$SHOPIFY_WEBHOOK_SECRET
\`\`\`

**⚠️ Keep this secret secure and never share it publicly!**

---

Generated on $(date)
EOF

    log "Partner Dashboard instructions created: $instructions_file"
}

test_configuration() {
    log "Testing Shopify configuration..."
    
    # Test if backend service can start with new configuration
    info "Checking if configuration is valid..."
    
    # Simple validation - check if we can import the service
    if command -v python3 >/dev/null; then
        cd "$PROJECT_DIR/backend"
        if python3 -c "
import sys
sys.path.append('.')
try:
    from services.shopify.client import ShopifyAPIClient
    print('✅ Shopify client import successful')
except Exception as e:
    print(f'❌ Shopify client import failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
            info "Configuration test passed"
        else
            warn "Configuration test failed - check your setup"
        fi
        cd - >/dev/null
    else
        info "Python not found, skipping configuration test"
    fi
}

display_summary() {
    echo
    echo "=============================================================================="
    echo -e " ${GREEN}SHOPIFY CONFIGURATION COMPLETE${NC}"
    echo "=============================================================================="
    echo
    echo -e "${BLUE}📋 Configuration Summary:${NC}"
    echo "   Client ID:       $SHOPIFY_CLIENT_ID"
    echo "   Redirect URI:    $SHOPIFY_REDIRECT_URI"
    echo "   Webhook Endpoint: $SHOPIFY_WEBHOOK_ENDPOINT"
    echo "   Environment:     $ENVIRONMENT"
    if [[ -n "$TEST_STORE_URL" ]]; then
        echo "   Test Store:      $TEST_STORE_URL"
    fi
    echo
    echo -e "${BLUE}📁 Files Updated:${NC}"
    echo "   Environment:     .env.$ENVIRONMENT"
    echo "   Instructions:    SHOPIFY_PARTNER_SETUP.md"
    echo
    echo -e "${BLUE}🚀 Next Steps:${NC}"
    echo "   1. Configure your Partner Dashboard using SHOPIFY_PARTNER_SETUP.md"
    echo "   2. Deploy the application: ./deploy.sh $ENVIRONMENT"
    echo "   3. Test OAuth flow and API integration"
    echo
    echo -e "${BLUE}🧪 Test URLs:${NC}"
    echo "   Health Check:    $(echo "$SHOPIFY_REDIRECT_URI" | sed 's|/api/v1/shopify/oauth/callback||')/api/v1/shopify/health"
    echo "   OAuth Flow:      $(echo "$SHOPIFY_REDIRECT_URI" | sed 's|/oauth/callback|/oauth/init|')"
    echo
    echo "=============================================================================="
}

main() {
    log "Shopify Configuration Helper"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --client-id)
                SHOPIFY_CLIENT_ID="$2"
                shift 2
                ;;
            --client-secret)
                SHOPIFY_CLIENT_SECRET="$2"
                shift 2
                ;;
            --redirect-uri)
                SHOPIFY_REDIRECT_URI="$2"
                shift 2
                ;;
            --webhook-endpoint)
                SHOPIFY_WEBHOOK_ENDPOINT="$2"
                shift 2
                ;;
            --webhook-secret)
                SHOPIFY_WEBHOOK_SECRET="$2"
                shift 2
                ;;
            --test-store)
                TEST_STORE_URL="$2"
                shift 2
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --interactive)
                interactive_setup
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
    
    # If no arguments provided, start interactive mode
    if [[ -z "$SHOPIFY_CLIENT_ID" && -z "$SHOPIFY_CLIENT_SECRET" ]]; then
        interactive_setup
    fi
    
    # Generate webhook secret if not provided
    if [[ -z "$SHOPIFY_WEBHOOK_SECRET" ]]; then
        SHOPIFY_WEBHOOK_SECRET=$(openssl rand -hex 32)
        info "Generated webhook secret"
    fi
    
    # Set default webhook endpoint if not provided
    if [[ -z "$SHOPIFY_WEBHOOK_ENDPOINT" && -n "$SHOPIFY_REDIRECT_URI" ]]; then
        SHOPIFY_WEBHOOK_ENDPOINT=$(echo "$SHOPIFY_REDIRECT_URI" | sed 's|/oauth/callback|/webhooks|')
    fi
    
    # Validate configuration
    validate_configuration
    
    # Update files
    update_environment_file
    create_partner_dashboard_instructions
    
    # Test configuration
    test_configuration
    
    # Show summary
    display_summary
}

# Change to project directory
cd "$PROJECT_DIR"

# Run main function
main "$@"