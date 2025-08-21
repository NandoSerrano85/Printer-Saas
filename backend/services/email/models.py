from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum

class EmailTemplate(str, Enum):
    """Email template types"""
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"
    WELCOME = "welcome"
    ACCOUNT_LOCKED = "account_locked"
    PASSWORD_CHANGED = "password_changed"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    TWO_FACTOR_DISABLED = "two_factor_disabled"
    LOGIN_ALERT = "login_alert"

class EmailPriority(str, Enum):
    """Email priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailRequest(BaseModel):
    """Email send request"""
    to_email: EmailStr
    to_name: Optional[str] = None
    template: EmailTemplate
    template_data: Dict[str, Any] = {}
    priority: EmailPriority = EmailPriority.NORMAL
    send_at: Optional[datetime] = None
    tenant_id: str
    user_id: Optional[UUID] = None

class EmailVerificationRequest(BaseModel):
    """Email verification specific request"""
    user_id: UUID
    email: EmailStr
    verification_token: str
    verification_url: str
    expires_at: datetime

class PasswordResetRequest(BaseModel):
    """Password reset specific request"""
    user_id: UUID
    email: EmailStr
    reset_token: str
    reset_url: str
    expires_at: datetime

class EmailResponse(BaseModel):
    """Email send response"""
    success: bool
    message: str
    email_id: Optional[str] = None
    error: Optional[str] = None

class EmailStatus(str, Enum):
    """Email status tracking"""
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    COMPLAINED = "complained"

class EmailLog(BaseModel):
    """Email log entry"""
    id: UUID
    tenant_id: str
    user_id: Optional[UUID]
    to_email: str
    from_email: str
    subject: str
    template: EmailTemplate
    status: EmailStatus
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    error_message: Optional[str]
    provider_message_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class EmailStatsResponse(BaseModel):
    """Email statistics response"""
    total_sent: int
    total_delivered: int
    total_failed: int
    total_bounced: int
    delivery_rate: float
    bounce_rate: float
    complaint_rate: float