from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID
from enum import Enum

if TYPE_CHECKING:
    from typing import ForwardRef

class IntegrationPlatform(str, Enum):
    """Supported integration platforms"""
    ETSY = "etsy"
    SHOPIFY = "shopify"

class TenantResponse(BaseModel):
    """Response model for tenant information"""
    id: UUID
    subdomain: str
    company_name: str
    subscription_tier: str
    is_active: bool
    created_at: datetime
    custom_domain: Optional[str] = None
    
    class Config:
        from_attributes = True

class TenantUserResponse(BaseModel):
    """Response model for tenant admin user"""
    id: UUID
    tenant_id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class TenantTokenResponse(BaseModel):
    """Token response for tenant authentication"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    tenant_id: UUID
    user_id: UUID
    email: str

class TenantRegistrationRequest(BaseModel):
    """Request model for tenant registration"""
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    subdomain: str = Field(..., min_length=3, max_length=63, description="Unique subdomain")
    admin_email: EmailStr = Field(..., description="Admin user email")
    admin_password: str = Field(..., min_length=8, max_length=128, description="Admin password")
    admin_first_name: str = Field(..., min_length=1, max_length=100, description="Admin first name")
    admin_last_name: str = Field(..., min_length=1, max_length=100, description="Admin last name")
    subscription_plan: str = Field(default="basic", description="Initial subscription plan")
    selected_integrations: List[IntegrationPlatform] = Field(..., min_items=1, description="Required integrations to set up")
    
    @field_validator('subdomain')
    @classmethod
    def validate_subdomain(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Subdomain must contain only letters, numbers, hyphens, and underscores')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Subdomain cannot start or end with a hyphen')
        return v.lower()
    
    @field_validator('admin_password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class TenantRegistrationStep1Request(BaseModel):
    """Step 1: Company and admin details"""
    company_name: str = Field(..., min_length=2, max_length=255, description="Company name")
    subdomain: str = Field(..., min_length=3, max_length=63, description="Unique subdomain")
    admin_email: EmailStr = Field(..., description="Admin user email")
    admin_password: str = Field(..., min_length=8, max_length=128, description="Admin password")
    admin_first_name: str = Field(..., min_length=1, max_length=100, description="Admin first name")
    admin_last_name: str = Field(..., min_length=1, max_length=100, description="Admin last name")
    subscription_plan: str = Field(default="basic", description="Initial subscription plan")
    selected_integrations: List[IntegrationPlatform] = Field(..., min_items=1, description="Required integrations to set up")
    
    @field_validator('subdomain')
    @classmethod
    def validate_subdomain(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Subdomain must contain only letters, numbers, hyphens, and underscores')
        if v.startswith('-') or v.endswith('-'):
            raise ValueError('Subdomain cannot start or end with a hyphen')
        return v.lower()
    
    @field_validator('admin_password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class TenantRegistrationStep1Response(BaseModel):
    """Response for step 1 - includes OAuth URLs for selected integrations"""
    success: bool
    message: str
    tenant_id: UUID
    registration_token: str  # Temporary token for completing registration
    oauth_urls: Dict[str, str]  # Maps platform to OAuth URL
    expires_in: int = 300  # 5 minutes to complete OAuth flow

class IntegrationConnectRequest(BaseModel):
    """Request to connect an integration during registration"""
    registration_token: str
    platform: IntegrationPlatform
    oauth_code: str
    oauth_state: str

class IntegrationConnectResponse(BaseModel):
    """Response for integration connection"""
    success: bool
    message: str
    platform: str
    shop_name: Optional[str] = None
    remaining_integrations: List[IntegrationPlatform]

class CompleteRegistrationRequest(BaseModel):
    """Request to complete the registration process"""
    registration_token: str

class CompleteRegistrationResponse(BaseModel):
    """Final registration response with login tokens"""
    success: bool
    message: str
    tenant: TenantResponse
    user: TenantUserResponse
    tokens: Dict[str, Any]
    connected_integrations: List[str]

class TenantLoginRequest(BaseModel):
    """Request model for tenant admin login"""
    email: EmailStr = Field(..., description="Admin email")
    password: str = Field(..., description="Admin password")
    subdomain: Optional[str] = Field(None, description="Tenant subdomain (optional if in URL)")

class TenantRegistrationResponse(BaseModel):
    """Response model for tenant registration"""
    success: bool
    message: str
    tenant: TenantResponse
    admin_user: TenantUserResponse
    tokens: Optional[Dict[str, Any]] = None

class TenantLoginResponse(BaseModel):
    """Response model for tenant login"""
    success: bool
    message: str
    tenant: TenantResponse
    user: TenantUserResponse
    tokens: Dict[str, Any]