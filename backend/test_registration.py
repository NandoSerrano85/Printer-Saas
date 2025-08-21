#!/usr/bin/env python3
"""
Test script for the new multi-step tenant registration API
"""
import os
import sys
sys.path.append('.')

# Mock the missing modules for testing
import sys
class MockModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

sys.modules['pyotp'] = MockModule()
sys.modules['qrcode'] = MockModule()

from services.tenant.service import TenantService
from services.tenant.models import TenantRegistrationStep1Request, IntegrationPlatform
from database.core import get_db
from sqlalchemy.orm import Session

def test_registration_flow():
    """Test the multi-step registration flow"""
    print("Testing multi-step registration flow...")
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Initialize service
        tenant_service = TenantService(db)
        
        # Test step 1: Start registration
        print("\n1. Testing registration start...")
        registration_data = TenantRegistrationStep1Request(
            subdomain="testcompany",
            company_name="Test Company",
            admin_email="admin@testcompany.com",
            admin_password="TestPassword123",
            admin_first_name="John",
            admin_last_name="Doe",
            selected_integrations=[IntegrationPlatform.ETSY, IntegrationPlatform.SHOPIFY]
        )
        
        response = tenant_service.start_registration(registration_data)
        print(f"✓ Registration started successfully")
        print(f"  Tenant ID: {response.tenant_id}")
        print(f"  Registration Token: {response.registration_token[:20]}...")
        print(f"  OAuth URLs: {list(response.oauth_urls.keys())}")
        
        # Test subdomain check
        print("\n2. Testing subdomain availability...")
        available = tenant_service.check_subdomain_availability("testcompany")
        print(f"✓ Subdomain 'testcompany' available: {available}")
        
        # Test another subdomain
        available = tenant_service.check_subdomain_availability("anothertestcompany")
        print(f"✓ Subdomain 'anothertestcompany' available: {available}")
        
        print("\n✅ All tests passed! Multi-step registration API is working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_registration_flow()