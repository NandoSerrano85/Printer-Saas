import os
from sqlalchemy import create_engine, MetaData, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
import logging

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/etsy_saas")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = scoped_session(SessionLocal)

# Base class for all models
Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_tenant_db(tenant_id: str):
    """Get database session with tenant context"""
    db = SessionLocal()
    try:
        # For ORM queries, we'll filter by tenant_id instead of setting schema path
        # This is more compatible with SQLAlchemy and easier to debug
        yield db
    finally:
        db.close()

def create_core_tables():
    """Create core multi-tenant tables and ORM entities"""
    # Import all entities explicitly to register them with Base metadata
    from database.entities.user import (
        User, ThirdPartyOAuthToken, UserSession, UserAuditLog,
        UserRole, UserRoleAssignment, UserEmailVerification, 
        UserPasswordReset, UserLoginAttempt, UserProfile
    )
    from database.entities.tenant import Tenant, TenantUser, TenantApiKey, TenantSubscription, TenantUsage
    from database.entities.order import Order, OrderItem, OrderFulfillment, OrderNote, OrderStatusHistory
    from database.entities.template import EtsyProductTemplate, TemplateCategory, TemplateVersion, TemplateTag
    from database.entities.design import DesignImage, DesignVariant, DesignCollection, DesignCollectionItem, DesignAnalytics
    from database.entities.mockup import Mockup, MockupImage, MockupMaskData, MockupDesignAssociation, MockupTemplate, MockupBatch
    from database.entities.canvas import CanvasConfig, SizeConfig, CanvasPreset, CanvasMaterial
    from database.entities.shopify import ShopifyProductTemplate, ShopifyProductSync, ShopifyOrderSync, ShopifyWebhook, ShopifyCollectionSync, ShopifyBatchOperation
    
    # Debug: Print what tables are registered
    print(f"Tables registered in metadata: {list(Base.metadata.tables.keys())}")
    
    # Create all ORM tables defined in our entities
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    print("Tables created, running verification...")
    
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE SCHEMA IF NOT EXISTS core;
            
            -- Core tenant management table
            CREATE TABLE IF NOT EXISTS core.tenants (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                subdomain VARCHAR(63) UNIQUE NOT NULL,
                company_name VARCHAR(255) NOT NULL,
                subscription_tier VARCHAR(50) DEFAULT 'basic',
                database_schema VARCHAR(63) NOT NULL,
                custom_domain VARCHAR(255),
                settings JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Core tenant users table  
            CREATE TABLE IF NOT EXISTS core.tenant_users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID REFERENCES core.tenants(id) ON DELETE CASCADE,
                email VARCHAR(255) NOT NULL,
                hashed_password VARCHAR(255) NOT NULL,
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                role VARCHAR(50) DEFAULT 'user',
                permissions JSONB DEFAULT '{}',
                is_active BOOLEAN DEFAULT TRUE,
                last_login TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tenant_id, email)
            );
            
            -- Tenant API keys for service communication
            CREATE TABLE IF NOT EXISTS core.tenant_api_keys (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID REFERENCES core.tenants(id) ON DELETE CASCADE,
                key_name VARCHAR(100) NOT NULL,
                api_key_hash VARCHAR(255) NOT NULL,
                permissions JSONB DEFAULT '{}',
                expires_at TIMESTAMP WITH TIME ZONE,
                last_used TIMESTAMP WITH TIME ZONE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tenant subscription and billing
            CREATE TABLE IF NOT EXISTS core.tenant_subscriptions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID REFERENCES core.tenants(id) ON DELETE CASCADE,
                plan_name VARCHAR(50) NOT NULL,
                status VARCHAR(20) DEFAULT 'active',
                billing_cycle VARCHAR(20) DEFAULT 'monthly',
                price_per_cycle DECIMAL(10,2) NOT NULL,
                features JSONB DEFAULT '{}',
                limits JSONB DEFAULT '{}',
                trial_ends_at TIMESTAMP WITH TIME ZONE,
                current_period_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                current_period_end TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP + INTERVAL '1 month',
                cancelled_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Tenant usage metrics
            CREATE TABLE IF NOT EXISTS core.tenant_usage (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                tenant_id UUID REFERENCES core.tenants(id) ON DELETE CASCADE,
                metric_name VARCHAR(100) NOT NULL,
                metric_value BIGINT DEFAULT 0,
                period_start TIMESTAMP WITH TIME ZONE NOT NULL,
                period_end TIMESTAMP WITH TIME ZONE NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tenant_id, metric_name, period_start)
            );
            
            -- Index creation
            CREATE INDEX IF NOT EXISTS idx_tenant_users_tenant_id ON core.tenant_users(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_tenant_users_email ON core.tenant_users(email);
            CREATE INDEX IF NOT EXISTS idx_tenant_api_keys_tenant_id ON core.tenant_api_keys(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_tenant_id ON core.tenant_subscriptions(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_id ON core.tenant_usage(tenant_id);
            CREATE INDEX IF NOT EXISTS idx_tenant_usage_metric ON core.tenant_usage(metric_name, period_start);
        """))
        conn.commit()

def create_tenant_schema(tenant_id: str, schema_name: str):
    """Create tenant-specific schema - simplified for single-schema multi-tenancy"""
    # With SQLAlchemy ORM and tenant_id filtering, we don't need separate schemas
    # All tables are created by Base.metadata.create_all() in create_core_tables()
    # This function is kept for backward compatibility but does nothing
    pass

# Event listeners for automatic timestamp updates
@event.listens_for(Base, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """Update the updated_at timestamp before any update"""
    if hasattr(target, 'updated_at'):
        from datetime import datetime
        target.updated_at = datetime.utcnow()

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO if os.getenv("SQL_ECHO", "false").lower() == "true" else logging.WARNING)