from sqlalchemy import Column, String, Boolean, DECIMAL, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import CoreBase, TimestampMixin
import uuid

class Tenant(CoreBase):
    """Core tenant entity for multi-tenant architecture"""
    __tablename__ = 'tenants'
    __table_args__ = {'schema': 'core'}
    
    subdomain = Column(String(63), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    subscription_tier = Column(String(50), default='basic')
    database_schema = Column(String(63), nullable=False)
    custom_domain = Column(String(255), nullable=True)
    settings = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    users = relationship('TenantUser', back_populates='tenant', cascade='all, delete-orphan')
    api_keys = relationship('TenantApiKey', back_populates='tenant', cascade='all, delete-orphan')
    subscriptions = relationship('TenantSubscription', back_populates='tenant', cascade='all, delete-orphan')
    usage_metrics = relationship('TenantUsage', back_populates='tenant', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Tenant(id='{self.id}', subdomain='{self.subdomain}', company='{self.company_name}')>"

class TenantUser(CoreBase):
    """Core tenant user entity - users that can access the tenant admin"""
    __tablename__ = 'tenant_users'
    __table_args__ = {'schema': 'core'}
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(String(50), default='user')
    permissions = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign key reference
    from sqlalchemy import ForeignKey
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('core.tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='users')
    
    __table_args__ = (
        {'schema': 'core'},
    )
    
    @property
    def full_name(self):
        """Get full name of the user"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if self.role == 'admin':
            return True
        return permission in self.permissions.get('allowed', [])
    
    def __repr__(self):
        return f"<TenantUser(id='{self.id}', email='{self.email}', tenant_id='{self.tenant_id}')>"

class TenantApiKey(CoreBase):
    """API keys for tenant service communication"""
    __tablename__ = 'tenant_api_keys'
    __table_args__ = {'schema': 'core'}
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    key_name = Column(String(100), nullable=False)
    api_key_hash = Column(String(255), nullable=False)
    permissions = Column(JSON, default=dict)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Foreign key reference
    from sqlalchemy import ForeignKey
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('core.tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='api_keys')
    
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if not self.expires_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.expires_at
    
    def __repr__(self):
        return f"<TenantApiKey(id='{self.id}', name='{self.key_name}', tenant_id='{self.tenant_id}')>"

class TenantSubscription(CoreBase):
    """Tenant subscription and billing information"""
    __tablename__ = 'tenant_subscriptions'
    __table_args__ = {'schema': 'core'}
    
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    plan_name = Column(String(50), nullable=False)
    status = Column(String(20), default='active', index=True)
    billing_cycle = Column(String(20), default='monthly')
    price_per_cycle = Column(DECIMAL(10, 2), nullable=False)
    features = Column(JSON, default=dict)
    limits = Column(JSON, default=dict)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign key reference
    from sqlalchemy import ForeignKey
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('core.tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='subscriptions')
    
    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        if not self.trial_ends_at:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) < self.trial_ends_at
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == 'active' and not self.cancelled_at
    
    def has_feature(self, feature_name: str) -> bool:
        """Check if subscription includes specific feature"""
        return self.features.get(feature_name, False)
    
    def get_limit(self, limit_name: str) -> int:
        """Get subscription limit value"""
        return self.limits.get(limit_name, 0)
    
    def __repr__(self):
        return f"<TenantSubscription(id='{self.id}', plan='{self.plan_name}', status='{self.status}')>"

class TenantUsage(CoreBase):
    """Tenant usage metrics for billing and monitoring"""
    __tablename__ = 'tenant_usage'
    __table_args__ = {'schema': 'core'}
    
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('core.tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Integer, default=0)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    usage_metadata = Column(JSON, default=dict)
    
    # Relationships
    tenant = relationship('Tenant', back_populates='usage_metrics')
    
    def increment(self, amount: int = 1):
        """Increment the metric value"""
        self.metric_value += amount
    
    def reset(self):
        """Reset the metric value to 0"""
        self.metric_value = 0
    
    def __repr__(self):
        return f"<TenantUsage(metric='{self.metric_name}', value={self.metric_value}, tenant_id='{self.tenant_id}')>"

class TenantRegistrationSession(CoreBase):
    """Temporary session for multi-step tenant registration"""
    __tablename__ = 'tenant_registration_sessions'
    __table_args__ = {'schema': 'core'}
    
    registration_token = Column(String(255), nullable=False, unique=True, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey('core.tenants.id', ondelete='CASCADE'), nullable=False)
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey('core.tenant_users.id', ondelete='CASCADE'), nullable=False)
    selected_integrations = Column(JSON, nullable=False)  # List of selected platforms
    connected_integrations = Column(JSON, default=list)  # List of successfully connected platforms
    oauth_states = Column(JSON, default=dict)  # Maps platform to OAuth state
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_completed = Column(Boolean, default=False)
    
    # Relationships
    tenant = relationship('Tenant')
    admin_user = relationship('TenantUser')
    
    def is_expired(self) -> bool:
        """Check if registration session is expired"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) >= self.expires_at
    
    def add_connected_integration(self, platform: str, shop_data: dict = None):
        """Add a connected integration"""
        if self.connected_integrations is None:
            self.connected_integrations = []
        
        integration_data = {"platform": platform}
        if shop_data:
            integration_data.update(shop_data)
            
        if platform not in [item["platform"] for item in self.connected_integrations]:
            self.connected_integrations.append(integration_data)
    
    def get_remaining_integrations(self) -> list:
        """Get list of integrations still needing connection"""
        connected_platforms = [item["platform"] for item in (self.connected_integrations or [])]
        return [platform for platform in self.selected_integrations if platform not in connected_platforms]
    
    def is_ready_to_complete(self) -> bool:
        """Check if all required integrations are connected"""
        return len(self.get_remaining_integrations()) == 0
    
    def __repr__(self):
        return f"<TenantRegistrationSession(token='{self.registration_token[:8]}...', tenant_id='{self.tenant_id}')>"