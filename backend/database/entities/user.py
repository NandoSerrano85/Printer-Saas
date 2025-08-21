from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from ..core import Base  # Direct import to avoid any mixin issues
from .base import MultiTenantBase, SoftDeleteMixin, AuditMixin
import uuid

class User(Base):
    """Tenant-scoped user entity for application users"""
    __tablename__ = 'users'
    
    # Primary key and timestamps manually defined
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    
    # Multi-tenant support
    tenant_id = Column(String, nullable=False, index=True)
    
    # Soft delete columns 
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)
    
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    shop_name = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    root_folder = Column(String(500), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    preferences = Column(JSON, default=dict)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Add additional fields for enhanced user management
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    phone_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    last_password_change = Column(DateTime(timezone=True), nullable=True)
    
    # Audit fields
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    third_party_tokens = relationship('ThirdPartyOAuthToken', back_populates='user', cascade='all, delete-orphan')
    etsy_product_templates = relationship('EtsyProductTemplate', back_populates='user', cascade='all, delete-orphan')
    mockups = relationship('Mockup', back_populates='user', cascade='all, delete-orphan')
    design_images = relationship('DesignImage', back_populates='user', cascade='all, delete-orphan')
    orders = relationship('Order', foreign_keys='Order.user_id', back_populates='user', cascade='all, delete-orphan')
    
    # New relationships
    sessions = relationship('UserSession', back_populates='user', cascade='all, delete-orphan')
    audit_logs = relationship('UserAuditLog', back_populates='user', cascade='all, delete-orphan')
    role_assignments = relationship('UserRoleAssignment', foreign_keys='UserRoleAssignment.user_id', back_populates='user', cascade='all, delete-orphan')
    email_verifications = relationship('UserEmailVerification', back_populates='user', cascade='all, delete-orphan')
    password_resets = relationship('UserPasswordReset', back_populates='user', cascade='all, delete-orphan')
    profile = relationship('UserProfile', uselist=False, back_populates='user', cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        """Get full name of the user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    @property
    def display_name(self):
        """Get display name (full name or shop name)"""
        return self.full_name if (self.first_name or self.last_name) else self.shop_name
    
    def get_preference(self, key: str, default=None):
        """Get user preference value"""
        return self.preferences.get(key, default)
    
    def set_preference(self, key: str, value):
        """Set user preference value"""
        if self.preferences is None:
            self.preferences = {}
        self.preferences[key] = value
    
    def is_locked(self) -> bool:
        """Check if user account is locked"""
        if not self.locked_until:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) < self.locked_until
    
    def lock_account(self, minutes: int = 30):
        """Lock user account for specified minutes"""
        from datetime import datetime, timezone, timedelta
        self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    
    def unlock_account(self):
        """Unlock user account"""
        self.locked_until = None
        self.failed_login_attempts = 0
    
    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account(30)  # Lock for 30 minutes
    
    def reset_failed_login(self):
        """Reset failed login attempts"""
        self.failed_login_attempts = 0
    
    def update_last_login(self):
        """Update last login timestamp"""
        from datetime import datetime, timezone
        self.last_login = datetime.now(timezone.utc)
    
    def mark_email_verified(self):
        """Mark email as verified"""
        from datetime import datetime, timezone
        self.email_verified = True
        self.email_verified_at = datetime.now(timezone.utc)
    
    def get_roles(self) -> list:
        """Get user's active roles"""
        from datetime import datetime, timezone
        active_assignments = [
            assignment for assignment in self.role_assignments
            if not assignment.is_expired()
        ]
        return [assignment.role for assignment in active_assignments]
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.get_roles())
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return any(role.has_permission(permission) for role in self.get_roles())
    
    def __repr__(self):
        return f"<User(id='{self.id}', email='{self.email}', shop='{self.shop_name}')>"

class ThirdPartyOAuthToken(MultiTenantBase):
    """OAuth tokens for third-party integrations like Etsy"""
    __tablename__ = 'third_party_oauth_tokens'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    provider = Column(String(50), nullable=False, index=True)  # 'etsy', 'shopify', etc.
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    scope = Column(Text, nullable=True)
    token_type = Column(String(20), default='Bearer')
    
    # Relationships
    user = relationship('User', back_populates='third_party_tokens')
    
    def is_expired(self) -> bool:
        """Check if token is expired"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.expires_at
    
    def is_expiring_soon(self, minutes: int = 30) -> bool:
        """Check if token is expiring within specified minutes"""
        from datetime import datetime, timezone, timedelta
        expiry_threshold = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        return self.expires_at <= expiry_threshold
    
    def __repr__(self):
        return f"<ThirdPartyOAuthToken(provider='{self.provider}', user_id='{self.user_id}')>"

class UserSession(MultiTenantBase):
    """User session tracking for security and monitoring"""
    __tablename__ = 'user_sessions'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    session_token = Column(String(255), nullable=False, unique=True, index=True)
    device_info = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    last_activity = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='sessions')
    
    def is_expired(self) -> bool:
        """Check if session is expired"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.expires_at
    
    def extend_session(self, hours: int = 24):
        """Extend session expiry time"""
        from datetime import datetime, timezone, timedelta
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)
        self.last_activity = datetime.now(timezone.utc)
    
    def __repr__(self):
        return f"<UserSession(id='{self.id}', user_id='{self.user_id}', active='{self.is_active}')>"

class UserAuditLog(MultiTenantBase):
    """Audit log for user actions"""
    __tablename__ = 'user_audit_logs'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='audit_logs')
    
    @classmethod
    def log_action(cls, user_id: uuid.UUID, action: str, resource_type: str = None, 
                   resource_id: uuid.UUID = None, details: dict = None, 
                   ip_address: str = None, user_agent: str = None, tenant_id: str = None):
        """Create audit log entry"""
        return cls(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            tenant_id=tenant_id
        )
    
    def __repr__(self):
        return f"<UserAuditLog(action='{self.action}', user_id='{self.user_id}', resource='{self.resource_type}')>"

class UserRole(MultiTenantBase):
    """User roles for permission management"""
    __tablename__ = 'user_roles'
    
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(JSON, default=list)  # List of permission strings
    is_system_role = Column(Boolean, default=False)  # True for built-in roles
    
    # Relationships
    users = relationship('UserRoleAssignment', back_populates='role')
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission"""
        return permission in (self.permissions or [])
    
    def add_permission(self, permission: str):
        """Add permission to role"""
        if self.permissions is None:
            self.permissions = []
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: str):
        """Remove permission from role"""
        if self.permissions and permission in self.permissions:
            self.permissions.remove(permission)
    
    def __repr__(self):
        return f"<UserRole(name='{self.name}', permissions={len(self.permissions or [])})>"

class UserRoleAssignment(MultiTenantBase):
    """Assignment of roles to users"""
    __tablename__ = 'user_role_assignments'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey('user_roles.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional role expiry
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], back_populates='role_assignments')
    role = relationship('UserRole', back_populates='users')
    assigner = relationship('User', foreign_keys=[assigned_by])
    
    def is_expired(self) -> bool:
        """Check if role assignment is expired"""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.expires_at
    
    def __repr__(self):
        return f"<UserRoleAssignment(user_id='{self.user_id}', role_id='{self.role_id}')>"

class UserEmailVerification(MultiTenantBase):
    """Email verification tokens"""
    __tablename__ = 'user_email_verifications'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    attempts = Column(Integer, default=0)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='email_verifications')
    
    def is_expired(self) -> bool:
        """Check if verification token is expired"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.expires_at
    
    def mark_verified(self):
        """Mark email as verified"""
        from datetime import datetime, timezone
        self.is_verified = True
        self.verified_at = datetime.now(timezone.utc)
    
    def increment_attempts(self):
        """Increment verification attempts"""
        self.attempts += 1
    
    def __repr__(self):
        return f"<UserEmailVerification(email='{self.email}', verified='{self.is_verified}')>"

class UserPasswordReset(MultiTenantBase):
    """Password reset tokens"""
    __tablename__ = 'user_password_resets'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User', back_populates='password_resets')
    
    def is_expired(self) -> bool:
        """Check if reset token is expired"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.expires_at
    
    def mark_used(self):
        """Mark token as used"""
        from datetime import datetime, timezone
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)
    
    def is_valid(self) -> bool:
        """Check if token is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()
    
    def __repr__(self):
        return f"<UserPasswordReset(user_id='{self.user_id}', used='{self.is_used}')>"

class UserLoginAttempt(MultiTenantBase):
    """Track login attempts for security"""
    __tablename__ = 'user_login_attempts'
    
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, index=True)
    failure_reason = Column(String(100), nullable=True)
    attempted_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    @classmethod
    def log_attempt(cls, email: str, success: bool, ip_address: str = None, 
                   user_agent: str = None, failure_reason: str = None, tenant_id: str = None):
        """Log a login attempt"""
        from datetime import datetime, timezone
        return cls(
            email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
            attempted_at=datetime.now(timezone.utc),
            tenant_id=tenant_id
        )
    
    def __repr__(self):
        return f"<UserLoginAttempt(email='{self.email}', success='{self.success}')>"

class UserProfile(MultiTenantBase, SoftDeleteMixin):
    """Extended user profile information"""
    __tablename__ = 'user_profiles'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    company = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    social_links = Column(JSON, default=dict)  # Social media links
    notification_preferences = Column(JSON, default=dict)
    privacy_settings = Column(JSON, default=dict)
    marketing_consent = Column(Boolean, default=False)
    analytics_consent = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    user = relationship('User', uselist=False, back_populates='profile')
    
    def get_social_link(self, platform: str) -> str:
        """Get social media link for platform"""
        return (self.social_links or {}).get(platform)
    
    def set_social_link(self, platform: str, url: str):
        """Set social media link"""
        if self.social_links is None:
            self.social_links = {}
        self.social_links[platform] = url
    
    def get_notification_preference(self, key: str, default: bool = True) -> bool:
        """Get notification preference"""
        return (self.notification_preferences or {}).get(key, default)
    
    def set_notification_preference(self, key: str, value: bool):
        """Set notification preference"""
        if self.notification_preferences is None:
            self.notification_preferences = {}
        self.notification_preferences[key] = value
    
    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}', company='{self.company}')>"