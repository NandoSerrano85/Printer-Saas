"""
Migration 001: Create core multi-tenant schema and tables
This migration creates the foundational core schema and tables for multi-tenant support.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """Create core schema and foundational tables"""
    
    # Create core schema
    op.execute("CREATE SCHEMA IF NOT EXISTS core")
    
    # Create core.tenants table
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('subdomain', sa.String(63), nullable=False, unique=True),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('subscription_tier', sa.String(50), server_default='basic'),
        sa.Column('database_schema', sa.String(63), nullable=False),
        sa.Column('custom_domain', sa.String(255), nullable=True),
        sa.Column('settings', postgresql.JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema='core'
    )
    
    # Create indexes for tenants table
    op.create_index('idx_core_tenants_subdomain', 'tenants', ['subdomain'], schema='core')
    op.create_index('idx_core_tenants_is_active', 'tenants', ['is_active'], schema='core')
    
    # Create core.tenant_users table
    op.create_table(
        'tenant_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('role', sa.String(50), server_default='user'),
        sa.Column('permissions', postgresql.JSONB, server_default='{}'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['core.tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_tenant_users_tenant_email'),
        schema='core'
    )
    
    # Create indexes for tenant_users table
    op.create_index('idx_core_tenant_users_tenant_id', 'tenant_users', ['tenant_id'], schema='core')
    op.create_index('idx_core_tenant_users_email', 'tenant_users', ['email'], schema='core')
    op.create_index('idx_core_tenant_users_is_active', 'tenant_users', ['is_active'], schema='core')
    
    # Create core.tenant_api_keys table
    op.create_table(
        'tenant_api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('key_name', sa.String(100), nullable=False),
        sa.Column('api_key_hash', sa.String(255), nullable=False),
        sa.Column('permissions', postgresql.JSONB, server_default='{}'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['core.tenants.id'], ondelete='CASCADE'),
        schema='core'
    )
    
    # Create indexes for tenant_api_keys table
    op.create_index('idx_core_tenant_api_keys_tenant_id', 'tenant_api_keys', ['tenant_id'], schema='core')
    op.create_index('idx_core_tenant_api_keys_is_active', 'tenant_api_keys', ['is_active'], schema='core')
    
    # Create core.tenant_subscriptions table
    op.create_table(
        'tenant_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_name', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('billing_cycle', sa.String(20), server_default='monthly'),
        sa.Column('price_per_cycle', sa.DECIMAL(10, 2), nullable=False),
        sa.Column('features', postgresql.JSONB, server_default='{}'),
        sa.Column('limits', postgresql.JSONB, server_default='{}'),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('current_period_start', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('current_period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['core.tenants.id'], ondelete='CASCADE'),
        schema='core'
    )
    
    # Create indexes for tenant_subscriptions table
    op.create_index('idx_core_tenant_subscriptions_tenant_id', 'tenant_subscriptions', ['tenant_id'], schema='core')
    op.create_index('idx_core_tenant_subscriptions_status', 'tenant_subscriptions', ['status'], schema='core')
    
    # Create core.tenant_usage table
    op.create_table(
        'tenant_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.BigInteger, server_default='0'),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['tenant_id'], ['core.tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('tenant_id', 'metric_name', 'period_start', name='uq_tenant_usage_metric_period'),
        schema='core'
    )
    
    # Create indexes for tenant_usage table
    op.create_index('idx_core_tenant_usage_tenant_id', 'tenant_usage', ['tenant_id'], schema='core')
    op.create_index('idx_core_tenant_usage_metric_name', 'tenant_usage', ['metric_name'], schema='core')
    op.create_index('idx_core_tenant_usage_period_start', 'tenant_usage', ['period_start'], schema='core')
    
    # Create function for tenant schema creation
    op.execute("""
        CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_id UUID, schema_name VARCHAR)
        RETURNS VOID AS $$
        BEGIN
            -- Create the tenant schema
            EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name);
            
            -- Set search path to include the new schema
            EXECUTE format('SET search_path TO %I, core, public', schema_name);
            
            -- This function will be extended in subsequent migrations
            -- to create all tenant-specific tables
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create function for automatic updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers for updated_at columns
    tables_with_updated_at = ['tenants', 'tenant_users', 'tenant_api_keys', 'tenant_subscriptions', 'tenant_usage']
    for table in tables_with_updated_at:
        op.execute(f"""
            CREATE TRIGGER trigger_update_updated_at_{table}
            BEFORE UPDATE ON core.{table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)

def downgrade():
    """Drop core schema and all related objects"""
    
    # Drop triggers
    tables_with_updated_at = ['tenants', 'tenant_users', 'tenant_api_keys', 'tenant_subscriptions', 'tenant_usage']
    for table in tables_with_updated_at:
        op.execute(f"DROP TRIGGER IF EXISTS trigger_update_updated_at_{table} ON core.{table};")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    op.execute("DROP FUNCTION IF EXISTS create_tenant_schema(UUID, VARCHAR);")
    
    # Drop tables (in reverse dependency order)
    op.drop_table('tenant_usage', schema='core')
    op.drop_table('tenant_subscriptions', schema='core')
    op.drop_table('tenant_api_keys', schema='core')
    op.drop_table('tenant_users', schema='core')
    op.drop_table('tenants', schema='core')
    
    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS core CASCADE")