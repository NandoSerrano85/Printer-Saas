#!/usr/bin/env python3
"""
Simple Shopify configuration test (no external dependencies)
"""

import os
import sys

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

def test_shopify_credentials():
    """Test Shopify credentials"""
    print("🧪 SHOPIFY PARTNER APP CONFIGURATION TEST")
    print("=" * 50)
    
    # Load environment
    env_vars = load_env_file()
    
    client_id = os.getenv('SHOPIFY_CLIENT_ID')
    client_secret = os.getenv('SHOPIFY_CLIENT_SECRET')
    api_version = os.getenv('SHOPIFY_API_VERSION', '2023-10')
    redirect_uri = os.getenv('SHOPIFY_OAUTH_REDIRECT_URI')
    scopes = os.getenv('SHOPIFY_OAUTH_SCOPES')
    webhook_secret = os.getenv('SHOPIFY_WEBHOOK_SECRET')
    
    print("📋 CURRENT CONFIGURATION:")
    print(f"   Client ID: {client_id}")
    print(f"   Client Secret: {client_secret[:8]}***{client_secret[-4:] if client_secret else 'Not set'}")
    print(f"   API Version: {api_version}")
    print(f"   Redirect URI: {redirect_uri}")
    print(f"   Scopes: {scopes}")
    print(f"   Webhook Secret: {'✅ Set' if webhook_secret else '❌ Not set'}")
    
    # Validation
    issues = []
    
    if not client_id:
        issues.append("❌ SHOPIFY_CLIENT_ID is missing")
    elif len(client_id) != 32:
        issues.append("⚠️  SHOPIFY_CLIENT_ID format looks unusual (should be 32 characters)")
    else:
        print("✅ Client ID is configured")
    
    if not client_secret:
        issues.append("❌ SHOPIFY_CLIENT_SECRET is missing")
    elif len(client_secret) != 32:
        issues.append("⚠️  SHOPIFY_CLIENT_SECRET format looks unusual (should be 32 characters)")
    else:
        print("✅ Client Secret is configured")
    
    if not redirect_uri:
        issues.append("❌ SHOPIFY_OAUTH_REDIRECT_URI is missing")
    elif not redirect_uri.startswith(('http://', 'https://')):
        issues.append("❌ SHOPIFY_OAUTH_REDIRECT_URI must start with http:// or https://")
    else:
        print("✅ Redirect URI is configured")
    
    if api_version != "2023-10":
        issues.append(f"⚠️  API version is {api_version}, recommended: 2023-10")
    else:
        print("✅ API version is correct")
    
    if not webhook_secret:
        issues.append("⚠️  Webhook secret not set (will be auto-generated)")
    else:
        print("✅ Webhook secret is configured")
    
    print("\n🔧 PARTNER DASHBOARD CONFIGURATION:")
    if redirect_uri:
        base_url = redirect_uri.replace('/api/v1/shopify/oauth/callback', '')
        print(f"   App URL: {base_url}")
        print(f"   Allowed redirection URLs: {redirect_uri}")
        print(f"   Webhook endpoint: {base_url}/api/v1/shopify/webhooks")
    
    print("\n📝 REQUIRED SCOPES IN PARTNER DASHBOARD:")
    if scopes:
        scope_list = scopes.split(',')
        for scope in scope_list:
            print(f"   ✓ {scope.strip()}")
    
    print("\n🧪 TEST URLS (after deployment):")
    if redirect_uri:
        base_url = redirect_uri.replace('/api/v1/shopify/oauth/callback', '')
        print(f"   Health Check: {base_url}/api/v1/shopify/health")
        print(f"   OAuth Flow Start: {base_url}/api/v1/shopify/oauth/init")
        print(f"   API Status: {base_url}/api/v1/status")
    
    print("\n📊 VALIDATION RESULTS:")
    print("=" * 30)
    
    if not issues:
        print("🎉 ALL CHECKS PASSED!")
        print("Your Shopify integration is properly configured.")
        print("\n🚀 NEXT STEPS:")
        print("1. Configure the URLs above in your Shopify Partner Dashboard")
        print("2. Create a development store (or use existing)")
        print("3. Deploy the application: ./deploy.sh development")
        print("4. Test OAuth flow: visit the OAuth Flow Start URL")
        
    else:
        print("⚠️  ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
        
        if all("⚠️" in issue for issue in issues):
            print("\n✅ No critical issues - integration should work with warnings")
        else:
            print("\n❌ Critical issues found - please fix before proceeding")
    
    print("\n" + "=" * 50)
    
    return len([i for i in issues if "❌" in i]) == 0

if __name__ == "__main__":
    test_shopify_credentials()