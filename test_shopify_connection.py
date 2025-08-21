#!/usr/bin/env python3
"""
Quick test script to verify Shopify Partner app connection
"""

import os
import sys
import requests
from urllib.parse import urlencode

# Add backend to path
sys.path.append('/Users/fserrano/Documents/Startups/Printer Saas/backend')

def load_env_file():
    """Load environment variables from .env file"""
    env_file = '/Users/fserrano/Documents/Startups/Printer Saas/backend/.env'
    env_vars = {}
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"').strip("'")
                    env_vars[key] = value
                    os.environ[key] = value
        return env_vars
    except FileNotFoundError:
        print("❌ .env file not found")
        return {}

def test_credentials():
    """Test if Shopify credentials are properly configured"""
    print("🔍 Testing Shopify credentials...")
    
    client_id = os.getenv('SHOPIFY_CLIENT_ID')
    client_secret = os.getenv('SHOPIFY_CLIENT_SECRET')
    api_version = os.getenv('SHOPIFY_API_VERSION', '2023-10')
    redirect_uri = os.getenv('SHOPIFY_OAUTH_REDIRECT_URI')
    
    print(f"📋 Configuration:")
    print(f"   Client ID: {client_id[:8]}..." if client_id else "   Client ID: Not set")
    print(f"   Client Secret: {client_secret[:8]}..." if client_secret else "   Client Secret: Not set")
    print(f"   API Version: {api_version}")
    print(f"   Redirect URI: {redirect_uri}")
    
    if not client_id or not client_secret:
        print("❌ Shopify credentials not properly configured")
        return False
    
    print("✅ Shopify credentials are configured")
    return True

def test_oauth_url_generation():
    """Test OAuth URL generation"""
    print("\n🔗 Testing OAuth URL generation...")
    
    try:
        from services.shopify.client import ShopifyAPIClient
        
        client = ShopifyAPIClient()
        
        # Test OAuth URL generation
        oauth_response = client.generate_oauth_url(
            shop_domain="test-shop",
            redirect_uri=os.getenv('SHOPIFY_OAUTH_REDIRECT_URI'),
            state="test_state_123"
        )
        
        print(f"✅ OAuth URL generated successfully:")
        print(f"   URL: {oauth_response.oauth_url[:100]}...")
        print(f"   Shop Domain: {oauth_response.shop_domain}")
        print(f"   Scopes: {oauth_response.scopes}")
        
        return True
        
    except Exception as e:
        print(f"❌ OAuth URL generation failed: {e}")
        return False

def test_shopify_service_import():
    """Test if Shopify service can be imported"""
    print("\n📦 Testing Shopify service import...")
    
    try:
        from services.shopify.service import ShopifyService
        from services.shopify.models import ShopifyOAuthInitRequest
        
        print("✅ Shopify service imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Shopify service import failed: {e}")
        return False

def generate_partner_dashboard_urls():
    """Generate URLs for Partner Dashboard configuration"""
    print("\n🔧 Partner Dashboard Configuration URLs:")
    
    redirect_uri = os.getenv('SHOPIFY_OAUTH_REDIRECT_URI')
    webhook_endpoint = os.getenv('SHOPIFY_WEBHOOK_ENDPOINT', '/api/v1/shopify/webhooks')
    
    if redirect_uri:
        base_url = redirect_uri.replace('/api/v1/shopify/oauth/callback', '')
        
        print(f"\n📋 Configure these URLs in your Partner Dashboard:")
        print(f"   App URL: {base_url}")
        print(f"   Allowed redirection URLs: {redirect_uri}")
        print(f"   Webhook endpoint: {base_url}{webhook_endpoint}")
        
        print(f"\n🧪 Test URLs (after deployment):")
        print(f"   Health Check: {base_url}/api/v1/shopify/health")
        print(f"   OAuth Init: {base_url}/api/v1/shopify/oauth/init")
        print(f"   API Status: {base_url}/api/v1/status")

def test_environment_variables():
    """Test all required environment variables"""
    print("\n🌍 Testing environment variables...")
    
    required_vars = [
        'SHOPIFY_CLIENT_ID',
        'SHOPIFY_CLIENT_SECRET',
        'SHOPIFY_OAUTH_REDIRECT_URI',
        'SHOPIFY_OAUTH_SCOPES'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def main():
    """Main test function"""
    print("🧪 SHOPIFY PARTNER APP CONNECTION TEST")
    print("=" * 50)
    
    # Load environment
    env_vars = load_env_file()
    if not env_vars:
        print("❌ Failed to load environment variables")
        return
    
    # Run tests
    tests = [
        test_environment_variables,
        test_credentials,
        test_shopify_service_import,
        test_oauth_url_generation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    # Generate configuration URLs
    generate_partner_dashboard_urls()
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Passed: {passed}/{total} tests")
    
    if passed == total:
        print("🎉 All tests passed! Shopify integration is properly configured.")
        print("\n🚀 Next steps:")
        print("1. Configure the URLs above in your Shopify Partner Dashboard")
        print("2. Deploy the application: ./deploy.sh development")
        print("3. Test the OAuth flow with a Shopify store")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()