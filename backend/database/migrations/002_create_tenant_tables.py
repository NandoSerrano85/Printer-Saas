"""
Migration 002: Create tenant-specific table templates
This migration creates the template for all tenant-specific tables that will be created
dynamically for each tenant schema.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    """Update the create_tenant_schema function to create all tenant tables"""
    
    # Drop the existing function and recreate with full table creation logic
    op.execute("DROP FUNCTION IF EXISTS create_tenant_schema(UUID, VARCHAR);")
    
    op.execute("""
        CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_id UUID, schema_name VARCHAR)
        RETURNS VOID AS $$
        BEGIN
            -- Create the tenant schema
            EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name);
            
            -- Set search path to include the new schema
            EXECUTE format('SET search_path TO %I, core, public', schema_name);
            
            -- Create users table
            EXECUTE format('
                CREATE TABLE IF NOT EXISTS %I.users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR NOT NULL DEFAULT %L,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    shop_name VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    root_folder VARCHAR(500),
                    avatar_url VARCHAR(500),
                    timezone VARCHAR(50) DEFAULT ''UTC'',
                    language VARCHAR(10) DEFAULT ''en'',
                    preferences JSONB DEFAULT ''{}'',
                    last_login TIMESTAMP WITH TIME ZONE,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )', schema_name, tenant_id);
            
            -- Create indexes for users table
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_users_tenant_id ON %I.users(tenant_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_users_email ON %I.users(email)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_users_is_active ON %I.users(is_active)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_users_is_deleted ON %I.users(is_deleted)', schema_name, schema_name);
            
            -- Create third_party_oauth_tokens table
            EXECUTE format('
                CREATE TABLE IF NOT EXISTS %I.third_party_oauth_tokens (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR NOT NULL DEFAULT %L,
                    user_id UUID REFERENCES %I.users(id) ON DELETE CASCADE,
                    provider VARCHAR(50) NOT NULL,
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    scope TEXT,
                    token_type VARCHAR(20) DEFAULT ''Bearer'',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )', schema_name, tenant_id, schema_name);
            
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_oauth_tokens_tenant_id ON %I.third_party_oauth_tokens(tenant_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_oauth_tokens_user_id ON %I.third_party_oauth_tokens(user_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_oauth_tokens_provider ON %I.third_party_oauth_tokens(provider)', schema_name, schema_name);
            
            -- Create etsy_product_templates table
            EXECUTE format('
                CREATE TABLE IF NOT EXISTS %I.etsy_product_templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR NOT NULL DEFAULT %L,
                    user_id UUID REFERENCES %I.users(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    template_title VARCHAR(255),
                    title VARCHAR(255),
                    description TEXT,
                    who_made VARCHAR(50),
                    when_made VARCHAR(50),
                    taxonomy_id INTEGER,
                    price DECIMAL(10,2),
                    materials TEXT,
                    shop_section_id INTEGER,
                    quantity INTEGER,
                    tags TEXT,
                    item_weight DECIMAL(8,2),
                    item_weight_unit VARCHAR(10),
                    item_length DECIMAL(8,2),
                    item_width DECIMAL(8,2),
                    item_height DECIMAL(8,2),
                    item_dimensions_unit VARCHAR(10),
                    is_taxable BOOLEAN,
                    type VARCHAR(50),
                    processing_min INTEGER,
                    processing_max INTEGER,
                    return_policy_id INTEGER,
                    is_active BOOLEAN DEFAULT TRUE,
                    category VARCHAR(100),
                    priority INTEGER DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at TIMESTAMP WITH TIME ZONE,
                    created_by UUID,
                    updated_by UUID,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name)
                )', schema_name, tenant_id, schema_name);
            
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_templates_tenant_id ON %I.etsy_product_templates(tenant_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_templates_user_id ON %I.etsy_product_templates(user_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_templates_name ON %I.etsy_product_templates(name)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_templates_is_active ON %I.etsy_product_templates(is_active)', schema_name, schema_name);
            
            -- Create canvas_configs table
            EXECUTE format('
                CREATE TABLE IF NOT EXISTS %I.canvas_configs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR NOT NULL DEFAULT %L,
                    user_id UUID REFERENCES %I.users(id) ON DELETE CASCADE,
                    product_template_id UUID REFERENCES %I.etsy_product_templates(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    category VARCHAR(100),
                    width_inches DECIMAL(8,2) NOT NULL,
                    height_inches DECIMAL(8,2) NOT NULL,
                    max_width_inches DECIMAL(8,2),
                    max_height_inches DECIMAL(8,2),
                    min_width_inches DECIMAL(8,2),
                    min_height_inches DECIMAL(8,2),
                    is_active BOOLEAN DEFAULT TRUE,
                    is_stretch BOOLEAN DEFAULT TRUE,
                    maintain_aspect_ratio BOOLEAN DEFAULT TRUE,
                    allow_rotation BOOLEAN DEFAULT TRUE,
                    default_dpi INTEGER DEFAULT 300,
                    min_dpi INTEGER DEFAULT 150,
                    max_dpi INTEGER DEFAULT 600,
                    color_profile VARCHAR(50) DEFAULT ''sRGB'',
                    background_color VARCHAR(7) DEFAULT ''#FFFFFF'',
                    supports_transparency BOOLEAN DEFAULT TRUE,
                    default_file_format VARCHAR(10) DEFAULT ''png'',
                    default_alignment VARCHAR(20) DEFAULT ''center'',
                    padding_inches DECIMAL(8,2) DEFAULT 0.0,
                    safe_area_inches DECIMAL(8,2) DEFAULT 0.0,
                    bleed_inches DECIMAL(8,2) DEFAULT 0.0,
                    cut_line_color VARCHAR(7),
                    registration_marks BOOLEAN DEFAULT FALSE,
                    sort_order INTEGER DEFAULT 0,
                    tags JSONB DEFAULT ''[]'',
                    metadata JSONB DEFAULT ''{}'',
                    usage_count INTEGER DEFAULT 0,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at TIMESTAMP WITH TIME ZONE,
                    created_by UUID,
                    updated_by UUID,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )', schema_name, tenant_id, schema_name, schema_name);
                
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_canvas_tenant_id ON %I.canvas_configs(tenant_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_canvas_user_id ON %I.canvas_configs(user_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_canvas_template_id ON %I.canvas_configs(product_template_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_canvas_is_active ON %I.canvas_configs(is_active)', schema_name, schema_name);
            
            -- Create size_configs table
            EXECUTE format('
                CREATE TABLE IF NOT EXISTS %I.size_configs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    tenant_id VARCHAR NOT NULL DEFAULT %L,
                    user_id UUID REFERENCES %I.users(id) ON DELETE CASCADE,
                    product_template_id UUID REFERENCES %I.etsy_product_templates(id) ON DELETE CASCADE,
                    canvas_config_id UUID REFERENCES %I.canvas_configs(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    display_name VARCHAR(255),
                    description TEXT,
                    size_category VARCHAR(50),
                    width_inches DECIMAL(8,2) NOT NULL,
                    height_inches DECIMAL(8,2) NOT NULL,
                    position_x_percent DECIMAL(5,2) DEFAULT 50.0,
                    position_y_percent DECIMAL(5,2) DEFAULT 50.0,
                    scale_factor DECIMAL(8,4) DEFAULT 1.0,
                    rotation_degrees DECIMAL(8,2) DEFAULT 0.0,
                    is_active BOOLEAN DEFAULT TRUE,
                    is_default BOOLEAN DEFAULT FALSE,
                    priority INTEGER DEFAULT 0,
                    price_modifier DECIMAL(8,2) DEFAULT 0.0,
                    price_modifier_type VARCHAR(20) DEFAULT ''fixed'',
                    production_time_modifier DECIMAL(8,4) DEFAULT 1.0,
                    material_usage_modifier DECIMAL(8,4) DEFAULT 1.0,
                    recommended_dpi INTEGER,
                    min_design_quality VARCHAR(20) DEFAULT ''medium'',
                    tags JSONB DEFAULT ''[]'',
                    metadata JSONB DEFAULT ''{}'',
                    usage_count INTEGER DEFAULT 0,
                    last_used TIMESTAMP WITH TIME ZONE,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    deleted_at TIMESTAMP WITH TIME ZONE,
                    created_by UUID,
                    updated_by UUID,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )', schema_name, tenant_id, schema_name, schema_name, schema_name);
            
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_size_tenant_id ON %I.size_configs(tenant_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_size_user_id ON %I.size_configs(user_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_size_template_id ON %I.size_configs(product_template_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_size_canvas_id ON %I.size_configs(canvas_config_id)', schema_name, schema_name);
            EXECUTE format('CREATE INDEX IF NOT EXISTS idx_%I_size_is_active ON %I.size_configs(is_active)', schema_name, schema_name);
            
            -- Reset search path
            SET search_path TO core, public;
        END;
        $$ LANGUAGE plpgsql;
    """)

def downgrade():
    """Revert the create_tenant_schema function to the basic version"""
    
    op.execute("DROP FUNCTION IF EXISTS create_tenant_schema(UUID, VARCHAR);")
    
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