from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# Request Models

class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    shop_name: str = Field(..., min_length=2, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field("UTC", max_length=50)
    language: Optional[str] = Field("en", max_length=10)
    is_active: Optional[bool] = True
    role_names: Optional[List[str]] = Field(default_factory=lambda: ["user"])
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdateRequest(BaseModel):
    shop_name: Optional[str] = Field(None, min_length=2, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    is_active: Optional[bool] = None

class UserProfileUpdateRequest(BaseModel):
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    bio: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[datetime] = None
    social_links: Optional[Dict[str, str]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[Dict[str, Any]] = None
    marketing_consent: Optional[bool] = None
    analytics_consent: Optional[bool] = None

class UserRoleAssignmentRequest(BaseModel):
    user_id: UUID
    role_names: List[str]
    expires_at: Optional[datetime] = None

class UserSearchRequest(BaseModel):
    query: Optional[str] = None
    email: Optional[str] = None
    shop_name: Optional[str] = None
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None
    has_role: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = Field(1, ge=1)
    per_page: int = Field(10, ge=1, le=100)
    sort_by: Optional[str] = Field("created_at", pattern="^(created_at|last_login|email|shop_name)$")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")

class BulkUserActionRequest(BaseModel):
    user_ids: List[UUID] = Field(..., min_items=1, max_items=100)
    action: str = Field(..., pattern="^(activate|deactivate|delete|assign_role|remove_role)$")
    parameters: Optional[Dict[str, Any]] = None

# Response Models

class UserResponse(BaseModel):
    id: UUID
    email: str
    shop_name: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    display_name: str
    is_active: bool
    email_verified: bool
    email_verified_at: Optional[datetime]
    phone_verified: bool
    two_factor_enabled: bool
    timezone: str
    language: str
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    avatar_url: Optional[str]
    
    class Config:
        from_attributes = True

class UserDetailResponse(UserResponse):
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_password_change: Optional[datetime]
    roles: List[str]
    permissions: List[str]

class UserProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    phone: Optional[str]
    company: Optional[str]
    website: Optional[str]
    bio: Optional[str]
    location: Optional[str]
    date_of_birth: Optional[datetime]
    social_links: Dict[str, str]
    notification_preferences: Dict[str, Any]
    privacy_settings: Dict[str, Any]
    marketing_consent: bool
    analytics_consent: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class UserWithProfileResponse(UserDetailResponse):
    profile: Optional[UserProfileResponse] = None

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total_count: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class UserStatsResponse(BaseModel):
    total_users: int
    active_users: int
    verified_users: int
    recent_registrations: int
    locked_accounts: int
    users_with_2fa: int

class UserAuditResponse(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    performed_by: Optional[str]  # email or user ID

class UserAuditListResponse(BaseModel):
    audit_logs: List[UserAuditResponse]
    total_count: int
    page: int
    per_page: int

class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    permissions: List[str]
    is_system_role: bool
    user_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class RoleListResponse(BaseModel):
    roles: List[RoleResponse]
    total_count: int

class BulkActionResponse(BaseModel):
    success: bool
    message: str
    processed_count: int
    failed_count: int
    errors: List[Dict[str, Any]]

class UserManagementResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None