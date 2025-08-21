"""Create enhanced user management tables

Revision ID: 004
Revises: 003
Create Date: 2024-08-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '004'
down_revision = '003'

def upgrade():
    """Create enhanced user management tables"""
    
    # Add new columns to existing users table
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('phone_verified', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('two_factor_enabled', sa.Boolean(), default=False))
    op.add_column('users', sa.Column('two_factor_secret', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), default=0))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('last_password_change', sa.DateTime(timezone=True), nullable=True))
    
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', sa.JSON(), default={}),
        
        sa.Column('name', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), default=[]),
        sa.Column('is_system_role', sa.Boolean(), default=False),
        
        sa.UniqueConstraint('name', name='uq_user_roles_name')
    )
    
    # Create user_role_assignments table
    op.create_table('user_role_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', sa.JSON(), default={}),
        
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_roles.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create user_email_verifications table
    op.create_table('user_email_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', sa.JSON(), default={}),
        
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, index=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('attempts', sa.Integer(), default=0),
        
        sa.UniqueConstraint('token', name='uq_user_email_verifications_token')
    )
    
    # Create user_password_resets table
    op.create_table('user_password_resets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', sa.JSON(), default={}),
        
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('token', sa.String(255), nullable=False, index=True),
        sa.Column('is_used', sa.Boolean(), default=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        
        sa.UniqueConstraint('token', name='uq_user_password_resets_token')
    )
    
    # Create user_login_attempts table
    op.create_table('user_login_attempts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', sa.JSON(), default={}),
        
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True, index=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, index=True),
        sa.Column('failure_reason', sa.String(100), nullable=True),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False, index=True),
    )
    
    # Create user_profiles table
    op.create_table('user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        sa.Column('tenant_id', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', sa.JSON(), default={}),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', postgresql.UUID(as_uuid=True), nullable=True),
        
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('company', sa.String(255), nullable=True),
        sa.Column('website', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('date_of_birth', sa.DateTime(timezone=True), nullable=True),
        sa.Column('social_links', sa.JSON(), default={}),
        sa.Column('notification_preferences', sa.JSON(), default={}),
        sa.Column('privacy_settings', sa.JSON(), default={}),
        sa.Column('marketing_consent', sa.Boolean(), default=False),
        sa.Column('analytics_consent', sa.Boolean(), default=True),
    )
    
    # Create indexes for better performance
    op.create_index('idx_user_roles_permissions', 'user_roles', ['permissions'], postgresql_using='gin')
    op.create_index('idx_user_login_attempts_email_time', 'user_login_attempts', ['email', 'attempted_at'])
    op.create_index('idx_user_login_attempts_ip_time', 'user_login_attempts', ['ip_address', 'attempted_at'])
    op.create_index('idx_user_email_verifications_expires', 'user_email_verifications', ['expires_at'])
    op.create_index('idx_user_password_resets_expires', 'user_password_resets', ['expires_at'])
    
    # Insert default roles
    op.execute("""
        INSERT INTO user_roles (name, description, permissions, is_system_role, tenant_id, created_at)
        VALUES 
        ('admin', 'Administrator with full access', 
         '["user.create", "user.read", "user.update", "user.delete", "role.manage", "tenant.manage", "system.admin"]'::json, 
         true, 'system', CURRENT_TIMESTAMP),
        ('user', 'Regular user with basic access', 
         '["user.read_own", "user.update_own", "order.read_own", "order.create", "template.read_own", "template.create"]'::json, 
         true, 'system', CURRENT_TIMESTAMP),
        ('shop_owner', 'Shop owner with shop management access', 
         '["user.read_own", "user.update_own", "order.read_own", "order.create", "order.manage_own", "template.read_own", "template.create", "template.manage_own", "integration.manage"]'::json, 
         true, 'system', CURRENT_TIMESTAMP)
    """)

def downgrade():
    """Drop enhanced user management tables"""
    
    # Drop indexes
    op.drop_index('idx_user_password_resets_expires')
    op.drop_index('idx_user_email_verifications_expires')
    op.drop_index('idx_user_login_attempts_ip_time')
    op.drop_index('idx_user_login_attempts_email_time')
    op.drop_index('idx_user_roles_permissions')
    
    # Drop tables
    op.drop_table('user_profiles')
    op.drop_table('user_login_attempts')
    op.drop_table('user_password_resets')
    op.drop_table('user_email_verifications')
    op.drop_table('user_role_assignments')
    op.drop_table('user_roles')
    
    # Drop columns from users table
    op.drop_column('users', 'last_password_change')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'two_factor_secret')
    op.drop_column('users', 'two_factor_enabled')
    op.drop_column('users', 'phone_verified')
    op.drop_column('users', 'email_verified_at')
    op.drop_column('users', 'email_verified')