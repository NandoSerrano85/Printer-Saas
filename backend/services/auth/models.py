from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# Request Models

class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    shop_name: str = Field(..., min_length=2, max_length=255)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field("UTC", max_length=50)
    language: Optional[str] = Field("en", max_length=10)
    marketing_consent: Optional[bool] = False
    terms_accepted: bool = Field(..., description="Must accept terms and conditions")
    
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
    
    @validator('terms_accepted')
    def validate_terms(cls, v):
        if not v:
            raise ValueError('Terms and conditions must be accepted')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False
    device_info: Optional[Dict[str, Any]] = None

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
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

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('new_password')
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

class EmailVerificationRequest(BaseModel):
    email: Optional[EmailStr] = None  # If None, uses current user's email

class EmailVerificationConfirm(BaseModel):
    token: str

class TwoFactorSetupRequest(BaseModel):
    password: str  # Confirm password to enable 2FA

class TwoFactorConfirmRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

class TwoFactorLoginRequest(BaseModel):
    email: EmailStr
    password: str
    two_factor_code: str = Field(..., min_length=6, max_length=6)

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Response Models

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user_id: UUID
    email: str
    tenant_id: str

class UserProfileResponse(BaseModel):
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
    avatar_url: Optional[str]
    
    class Config:
        from_attributes = True

class AuthenticationResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserProfileResponse] = None
    tokens: Optional[TokenResponse] = None
    requires_2fa: Optional[bool] = False
    requires_email_verification: Optional[bool] = False

class RegistrationResponse(BaseModel):
    success: bool
    message: str
    user: UserProfileResponse
    verification_email_sent: bool = False

class TwoFactorSetupResponse(BaseModel):
    success: bool
    secret: str
    qr_code_url: str
    backup_codes: List[str]

class SessionInfo(BaseModel):
    id: UUID
    device_info: Dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    is_active: bool
    last_activity: datetime
    expires_at: datetime
    is_current: bool = False
    
    class Config:
        from_attributes = True

class UserSessionsResponse(BaseModel):
    sessions: List[SessionInfo]
    total_count: int

class SecurityEventResponse(BaseModel):
    event_type: str
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Dict[str, Any]
    success: bool

class UserSecurityResponse(BaseModel):
    recent_events: List[SecurityEventResponse]
    failed_login_attempts: int
    account_locked: bool
    locked_until: Optional[datetime]
    two_factor_enabled: bool
    email_verified: bool
    last_password_change: Optional[datetime]

class PermissionResponse(BaseModel):
    permission: str
    granted: bool
    source: str  # role name or direct grant

class UserPermissionsResponse(BaseModel):
    permissions: List[PermissionResponse]
    roles: List[str]

class AuthResponse(BaseModel):
    """Generic auth response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None