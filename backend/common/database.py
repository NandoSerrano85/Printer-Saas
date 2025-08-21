from sqlalchemy.orm import Session
from fastapi import Depends, Request
from typing import Generator
import logging

from database.core import get_db as _get_db, get_tenant_db as _get_tenant_db
from .auth import get_tenant_context

logger = logging.getLogger(__name__)

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    db = next(_get_db())
    try:
        yield db
    finally:
        db.close()

def get_tenant_database(
    request: Request,
    tenant_id: str = Depends(get_tenant_context)
) -> Generator[Session, None, None]:
    """Get tenant-scoped database session"""
    db = next(_get_tenant_db(tenant_id))
    try:
        # With SQLAlchemy ORM, we filter by tenant_id instead of setting schema path
        # This is more compatible and easier to debug
        yield db
    finally:
        db.close()

def set_tenant_context(db: Session, tenant_id: str):
    """Set tenant context for database session - Using ORM filtering instead"""
    # With SQLAlchemy ORM, we filter by tenant_id in queries instead of schema switching
    # This is more compatible with SQLAlchemy ORM and easier to debug
    logger.debug(f"Using tenant_id filtering for tenant: {tenant_id}")
    pass

class DatabaseManager:
    """Database manager for handling tenant-specific operations"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self._set_context()
    
    def _set_context(self):
        """Set the tenant context for this session"""
        # Using ORM filtering by tenant_id instead of schema switching
        set_tenant_context(self.db, self.tenant_id)
    
    def commit(self):
        """Commit the session"""
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Database commit failed: {e}")
            raise
    
    def rollback(self):
        """Rollback the session"""
        self.db.rollback()
    
    def refresh(self, instance):
        """Refresh an instance from the database"""
        self.db.refresh(instance)
    
    def add(self, instance):
        """Add instance to session"""
        self.db.add(instance)
    
    def delete(self, instance):
        """Delete instance from session"""
        self.db.delete(instance)
    
    def query(self, model):
        """Create a query for the model"""
        return self.db.query(model)
    
    def get(self, model, id):
        """Get model by ID"""
        return self.db.query(model).filter(model.id == id).first()
    
    def close(self):
        """Close the database session"""
        self.db.close()

def get_database_manager(
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db)
) -> DatabaseManager:
    """Get database manager with tenant context"""
    return DatabaseManager(db, tenant_id)