from sqlalchemy import Column, String, Boolean, DateTime, func, Index
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from ..core import Base

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

class TenantMixin:
    """Mixin for multi-tenant support"""
    
    @declared_attr
    def tenant_id(cls):
        return Column(String, nullable=False, index=True)
    
    @declared_attr
    def __table_args__(cls):
        # Create index on tenant_id for all tenant tables
        return (
            Index(f'idx_{cls.__tablename__}_tenant_id', 'tenant_id'),
        )

class MultiTenantBase(Base, TimestampMixin, TenantMixin):
    """Base class for all multi-tenant entities"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class CoreBase(Base, TimestampMixin):
    """Base class for core (non-tenant specific) entities"""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False, index=True)
    
    def soft_delete(self, deleted_by=None):
        """Mark entity as deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """Restore soft-deleted entity"""
        self.is_deleted = False
        self.deleted_at = None

class AuditMixin:
    """Mixin for audit trail functionality"""
    
    @declared_attr
    def created_by(cls):
        return Column(UUID(as_uuid=True), nullable=True)
    
    @declared_attr
    def updated_by(cls):
        return Column(UUID(as_uuid=True), nullable=True)
    
    @declared_attr
    def version(cls):
        return Column(String, default=1, nullable=False)

class UserScopedMixin:
    """Mixin for entities that belong to a specific user"""
    
    @declared_attr
    def user_id(cls):
        return Column(UUID(as_uuid=True), nullable=False, index=True)
    
    @declared_attr
    def __table_args__(cls):
        base_args = getattr(super(), '__table_args__', ())
        if isinstance(base_args, dict):
            base_args = ()
        return base_args + (
            Index(f'idx_{cls.__tablename__}_user_id', 'user_id'),
        )