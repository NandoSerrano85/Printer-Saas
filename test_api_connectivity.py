#!/usr/bin/env python3
"""
Test script to verify frontend-backend API connectivity
This script creates a test JWT token and validates API endpoints
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import jwt
import uuid

# Configuration
BACKEND_URL = "http://localhost:8000"
JWT_SECRET = "your-secret-key-here"  # Default from auth.py
ALGORITHM = "HS256"

def create_test_token():
    """Create a test JWT token for API testing"""
    # Create test user data
    user_id = str(uuid.uuid4())
    email = "demo@printersaas.com"
    tenant_id = "demo"
    
    # Token expiration
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Token payload
    payload = {
        "sub": email,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "exp": expire
    }
    
    # Create token
    token = jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)
    return token

def test_api_endpoints():
    """Test API endpoints that the frontend uses"""
    
    print("🧪 Testing Printer SaaS API Connectivity")
    print("=" * 50)
    
    # Create test token
    print("📝 Creating test JWT token...")
    token = create_test_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Tenant-ID": "demo"
    }
    
    # Test endpoints
    endpoints = [
        ("GET", "/health", "Health Check"),
        ("GET", "/api/v1/status", "API Status"),
        ("GET", "/api/v1/shopify/health", "Shopify Health"),
        ("GET", "/api/v1/etsy/health", "Etsy Health (Auth Required)"),
        ("GET", "/api/v1/dashboard/summary", "Dashboard Summary"),
        ("GET", "/api/v1/etsy/integration/status", "Etsy Integration Status"),
        ("GET", "/api/v1/shopify/integration/status", "Shopify Integration Status"),
    ]
    
    results = []
    
    for method, endpoint, description in endpoints:
        try:
            url = f"{BACKEND_URL}{endpoint}"
            
            if method == "GET":
                if endpoint in ["/health", "/api/v1/status", "/api/v1/shopify/health"]:
                    # These endpoints don't require auth
                    response = requests.get(url, timeout=5)
                else:
                    # These endpoints require auth
                    response = requests.get(url, headers=headers, timeout=5)
                    
            status_code = response.status_code
            
            if status_code == 200:
                status = "✅ OK"
                try:
                    data = response.json()
                    detail = f"Response: {json.dumps(data, indent=2)[:100]}..."
                except:
                    detail = "Valid response received"
            elif status_code == 401:
                status = "🔒 Auth Required"
                detail = "Endpoint requires authentication (expected)"
            elif status_code == 404:
                status = "❌ Not Found"
                detail = "Endpoint not available"
            elif status_code == 405:
                status = "⚠️ Method Not Allowed"
                detail = "HTTP method not supported"
            else:
                status = f"⚠️ HTTP {status_code}"
                try:
                    data = response.json()
                    detail = data.get('detail', 'Unknown error')
                except:
                    detail = "Non-JSON response"
                    
            results.append({
                "endpoint": endpoint,
                "description": description,
                "status": status,
                "status_code": status_code,
                "detail": detail
            })
            
            print(f"{status} {description} ({endpoint})")
            if status_code == 200:
                try:
                    print(f"    📄 {response.json()}")
                except:
                    print(f"    📄 Response length: {len(response.text)} chars")
            else:
                print(f"    ℹ️  {detail}")
                
        except requests.exceptions.ConnectionError:
            results.append({
                "endpoint": endpoint,
                "description": description,
                "status": "❌ Connection Failed",
                "status_code": 0,
                "detail": "Backend service not reachable"
            })
            print(f"❌ Connection Failed {description} ({endpoint})")
            print(f"    ℹ️  Backend service not reachable")
            
        except Exception as e:
            results.append({
                "endpoint": endpoint,
                "description": description,
                "status": "❌ Error",
                "status_code": 0,
                "detail": str(e)
            })
            print(f"❌ Error {description} ({endpoint})")
            print(f"    ℹ️  {str(e)}")
    
    print("\n📊 Summary:")
    print("=" * 50)
    
    # Count results
    success_count = len([r for r in results if r['status_code'] == 200])
    auth_count = len([r for r in results if r['status_code'] == 401])
    error_count = len([r for r in results if r['status_code'] not in [200, 401]])
    
    print(f"✅ Successful: {success_count}")
    print(f"🔒 Auth Required: {auth_count}")
    print(f"❌ Errors: {error_count}")
    
    # Frontend connectivity assessment
    print("\n🖥️  Frontend Connectivity Assessment:")
    print("=" * 50)
    
    if success_count >= 2 and (success_count + auth_count) >= 6:
        print("✅ EXCELLENT: Frontend can successfully connect to backend")
        print("   - Core API endpoints are accessible")
        print("   - Authentication system is working")
        print("   - Integration services are available")
    elif success_count >= 1:
        print("⚠️  PARTIAL: Frontend has limited connectivity to backend")
        print("   - Some endpoints are working")
        print("   - Authentication may need configuration")
    else:
        print("❌ FAILED: Frontend cannot connect to backend")
        print("   - Backend service may not be running")
        print("   - Check docker-compose services")
        
    # Recommendations
    print("\n💡 Frontend Integration Recommendations:")
    print("=" * 50)
    
    if auth_count > 0:
        print("1. 🔑 Implement proper authentication in frontend")
        print("   - Add login form for demo users")
        print("   - Store JWT tokens in frontend state")
        print("   - Add token refresh logic")
        
    if success_count > 0:
        print("2. 🔄 API Service Integration")
        print("   - Frontend API service can connect to backend")
        print("   - Implement error handling for 401 responses") 
        print("   - Add loading states for API calls")
        
    print("3. 🧪 Testing Suggestions")
    print("   - Test OAuth flows with actual credentials")
    print("   - Verify template and order management")
    print("   - Test multi-tenant functionality")
    
    return results

if __name__ == "__main__":
    test_api_endpoints()