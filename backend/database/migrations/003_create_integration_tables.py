#!/usr/bin/env python3
"""
Create integration tables for Etsy and Shopify services

This migration creates all necessary tables for:
- Etsy product templates and synchronization
- Shopify product templates and synchronization  
- Third-party OAuth tokens
- Webhook tracking
- Batch operations
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)

# Migration metadata
down_revision = '002'
depends_on = ['001', '002']

def upgrade():
    """Apply the migration"""
    
    # Get connection from current transaction context
    import threading
    conn = getattr(threading.current_thread(), '_migration_connection', None)
    if not conn:
        raise RuntimeError("No database connection available in migration context")
    
    with conn.cursor() as cur:
        logger.info("Creating integration tables...")
        
        # Create extensions if needed
        cur.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
        
        # Third-party OAuth tokens table (used by both Etsy and Shopify)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS core.third_party_oauth_tokens (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
                platform VARCHAR(50) NOT NULL,
                
                -- OAuth data
                access_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMP WITH TIME ZONE,
                scopes TEXT,
                token_type VARCHAR(50) DEFAULT 'bearer',
                
                -- Platform-specific data
                shop_domain VARCHAR(255),
                shop_id VARCHAR(100),
                oauth_state VARCHAR(255), -- For CSRF protection during OAuth flow
                code_verifier VARCHAR(255), -- For PKCE flow
                code_challenge VARCHAR(255), -- For PKCE flow
                
                -- Sync metadata
                last_sync_at TIMESTAMP WITH TIME ZONE,
                sync_status VARCHAR(50) DEFAULT 'active',
                
                -- Metadata
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                
                -- Constraints
                UNIQUE(user_id, platform, shop_domain),
                CHECK (platform IN ('etsy', 'shopify'))
            );
            
            CREATE INDEX idx_oauth_tokens_user_platform ON core.third_party_oauth_tokens(user_id, platform);
            CREATE INDEX idx_oauth_tokens_active ON core.third_party_oauth_tokens(is_active) WHERE is_active = true;
        """)
        
        # Function to create tenant-specific integration tables
        cur.execute("""
            CREATE OR REPLACE FUNCTION create_tenant_integration_tables(schema_name TEXT)
            RETURNS VOID AS $$
            BEGIN
                -- Etsy Product Templates
                EXECUTE format('
                    CREATE TABLE %I.etsy_product_templates (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
                        tenant_id VARCHAR(50) NOT NULL,
                        
                        -- Template metadata
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        category VARCHAR(100),
                        tags TEXT, -- Comma-separated tags
                        
                        -- Template data (JSON structure matching Etsy API)
                        template_data JSONB NOT NULL,
                        
                        -- Etsy-specific fields
                        listing_template_id VARCHAR(100), -- External template ID if synced
                        taxonomy_id INTEGER,
                        materials TEXT[], -- Array of materials
                        style_tags TEXT[], -- Array of style tags
                        
                        -- Usage tracking
                        usage_count INTEGER DEFAULT 0,
                        last_used_at TIMESTAMP WITH TIME ZONE,
                        
                        -- Status
                        is_active BOOLEAN DEFAULT true,
                        is_deleted BOOLEAN DEFAULT false,
                        priority INTEGER DEFAULT 0,
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        deleted_at TIMESTAMP WITH TIME ZONE
                    );
                    
                    CREATE INDEX idx_etsy_templates_user ON %I.etsy_product_templates(user_id) WHERE is_deleted = false;
                    CREATE INDEX idx_etsy_templates_active ON %I.etsy_product_templates(is_active) WHERE is_active = true AND is_deleted = false;
                    CREATE INDEX idx_etsy_templates_category ON %I.etsy_product_templates(category) WHERE is_deleted = false;
                ', schema_name, schema_name, schema_name, schema_name);
                
                -- Shopify Product Templates
                EXECUTE format('
                    CREATE TABLE %I.shopify_product_templates (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
                        tenant_id VARCHAR(50) NOT NULL,
                        
                        -- Template metadata
                        name VARCHAR(255) NOT NULL,
                        description TEXT,
                        category VARCHAR(100),
                        tags TEXT, -- Comma-separated tags
                        
                        -- Template data (JSON structure matching Shopify API)
                        template_data JSONB NOT NULL,
                        
                        -- Shopify-specific fields
                        product_type VARCHAR(255),
                        vendor VARCHAR(255),
                        handle VARCHAR(255), -- URL handle
                        seo_title VARCHAR(70),
                        seo_description VARCHAR(320),
                        
                        -- Usage tracking
                        usage_count INTEGER DEFAULT 0,
                        last_used_at TIMESTAMP WITH TIME ZONE,
                        
                        -- Status
                        is_active BOOLEAN DEFAULT true,
                        is_deleted BOOLEAN DEFAULT false,
                        priority INTEGER DEFAULT 0,
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        deleted_at TIMESTAMP WITH TIME ZONE
                    );
                    
                    CREATE INDEX idx_shopify_templates_user ON %I.shopify_product_templates(user_id) WHERE is_deleted = false;
                    CREATE INDEX idx_shopify_templates_active ON %I.shopify_product_templates(is_active) WHERE is_active = true AND is_deleted = false;
                    CREATE INDEX idx_shopify_templates_category ON %I.shopify_product_templates(category) WHERE is_deleted = false;
                ', schema_name, schema_name, schema_name, schema_name);
                
                -- Etsy Product Sync tracking
                EXECUTE format('
                    CREATE TABLE %I.etsy_product_sync (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
                        tenant_id VARCHAR(50) NOT NULL,
                        
                        -- Etsy data
                        etsy_listing_id VARCHAR(50) NOT NULL,
                        internal_template_id UUID REFERENCES %I.etsy_product_templates(id) ON DELETE SET NULL,
                        
                        -- Sync status
                        sync_status VARCHAR(50) DEFAULT ''pending'',
                        last_sync_at TIMESTAMP WITH TIME ZONE,
                        sync_error_message TEXT,
                        
                        -- Data snapshots
                        etsy_data JSONB, -- Last known Etsy data
                        local_modifications JSONB, -- Local changes not yet synced
                        
                        -- Sync configuration
                        sync_direction VARCHAR(20) DEFAULT ''bidirectional'', -- to_etsy, from_etsy, bidirectional
                        auto_sync_enabled BOOLEAN DEFAULT true,
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Constraints
                        UNIQUE(user_id, etsy_listing_id),
                        CHECK (sync_status IN (''pending'', ''synced'', ''error'', ''manual'')),
                        CHECK (sync_direction IN (''to_etsy'', ''from_etsy'', ''bidirectional''))
                    );
                    
                    CREATE INDEX idx_etsy_sync_user ON %I.etsy_product_sync(user_id);
                    CREATE INDEX idx_etsy_sync_status ON %I.etsy_product_sync(sync_status);
                    CREATE INDEX idx_etsy_sync_listing ON %I.etsy_product_sync(etsy_listing_id);
                ', schema_name, schema_name, schema_name, schema_name, schema_name);
                
                -- Shopify Product Sync tracking  
                EXECUTE format('
                    CREATE TABLE %I.shopify_product_sync (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
                        tenant_id VARCHAR(50) NOT NULL,
                        
                        -- Shopify data
                        shopify_product_id VARCHAR(50) NOT NULL,
                        internal_template_id UUID REFERENCES %I.shopify_product_templates(id) ON DELETE SET NULL,
                        
                        -- Sync status
                        sync_status VARCHAR(50) DEFAULT ''pending'',
                        last_sync_at TIMESTAMP WITH TIME ZONE,
                        sync_error_message TEXT,
                        
                        -- Data snapshots
                        shopify_data JSONB, -- Last known Shopify data
                        local_modifications JSONB, -- Local changes not yet synced
                        
                        -- Sync configuration
                        sync_direction VARCHAR(20) DEFAULT ''bidirectional'',
                        auto_sync_enabled BOOLEAN DEFAULT true,
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Constraints
                        UNIQUE(user_id, shopify_product_id),
                        CHECK (sync_status IN (''pending'', ''synced'', ''error'', ''manual'')),
                        CHECK (sync_direction IN (''to_shopify'', ''from_shopify'', ''bidirectional''))
                    );
                    
                    CREATE INDEX idx_shopify_sync_user ON %I.shopify_product_sync(user_id);
                    CREATE INDEX idx_shopify_sync_status ON %I.shopify_product_sync(sync_status);
                    CREATE INDEX idx_shopify_sync_product ON %I.shopify_product_sync(shopify_product_id);
                ', schema_name, schema_name, schema_name, schema_name, schema_name);
                
                -- Etsy Order Sync tracking
                EXECUTE format('
                    CREATE TABLE %I.etsy_order_sync (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
                        tenant_id VARCHAR(50) NOT NULL,
                        
                        -- Etsy data
                        etsy_receipt_id VARCHAR(50) NOT NULL,
                        internal_order_id UUID REFERENCES %I.orders(id) ON DELETE SET NULL,
                        
                        -- Sync status
                        sync_status VARCHAR(50) DEFAULT ''pending'',
                        last_sync_at TIMESTAMP WITH TIME ZONE,
                        sync_error_message TEXT,
                        
                        -- Order data
                        etsy_order_data JSONB, -- Complete Etsy receipt data
                        receipt_id VARCHAR(50),
                        
                        -- Processing metadata
                        webhook_processed BOOLEAN DEFAULT false,
                        requires_manual_review BOOLEAN DEFAULT false,
                        review_notes TEXT,
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Constraints
                        UNIQUE(user_id, etsy_receipt_id)
                    );
                    
                    CREATE INDEX idx_etsy_order_sync_user ON %I.etsy_order_sync(user_id);
                    CREATE INDEX idx_etsy_order_sync_status ON %I.etsy_order_sync(sync_status);
                    CREATE INDEX idx_etsy_order_sync_receipt ON %I.etsy_order_sync(etsy_receipt_id);
                ', schema_name, schema_name, schema_name, schema_name, schema_name);
                
                -- Shopify Order Sync tracking
                EXECUTE format('
                    CREATE TABLE %I.shopify_order_sync (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
                        tenant_id VARCHAR(50) NOT NULL,
                        
                        -- Shopify data
                        shopify_order_id VARCHAR(50) NOT NULL,
                        internal_order_id UUID REFERENCES %I.orders(id) ON DELETE SET NULL,
                        
                        -- Sync status
                        sync_status VARCHAR(50) DEFAULT ''pending'',
                        last_sync_at TIMESTAMP WITH TIME ZONE,
                        sync_error_message TEXT,
                        
                        -- Order data
                        shopify_order_data JSONB, -- Complete Shopify order data
                        order_number VARCHAR(50), -- Shopify order number
                        financial_status VARCHAR(50),
                        fulfillment_status VARCHAR(50),
                        
                        -- Processing metadata
                        webhook_processed BOOLEAN DEFAULT false,
                        requires_manual_review BOOLEAN DEFAULT false,
                        review_notes TEXT,
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Constraints
                        UNIQUE(user_id, shopify_order_id)
                    );
                    
                    CREATE INDEX idx_shopify_order_sync_user ON %I.shopify_order_sync(user_id);
                    CREATE INDEX idx_shopify_order_sync_status ON %I.shopify_order_sync(sync_status);
                    CREATE INDEX idx_shopify_order_sync_order ON %I.shopify_order_sync(shopify_order_id);
                ', schema_name, schema_name, schema_name, schema_name, schema_name);
                
                -- Webhook tracking (for both platforms)
                EXECUTE format('
                    CREATE TABLE %I.platform_webhooks (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        tenant_id VARCHAR(50) NOT NULL,
                        
                        -- Platform and webhook data
                        platform VARCHAR(50) NOT NULL, -- etsy, shopify
                        webhook_id VARCHAR(50), -- Platform webhook ID
                        topic VARCHAR(100) NOT NULL, -- e.g., orders/create, products/update
                        
                        -- Event data
                        shop_domain VARCHAR(255),
                        event_data JSONB NOT NULL,
                        headers JSONB,
                        
                        -- Processing status
                        processing_status VARCHAR(50) DEFAULT ''pending'',
                        processed_at TIMESTAMP WITH TIME ZONE,
                        processing_error TEXT,
                        retry_count INTEGER DEFAULT 0,
                        
                        -- Verification
                        hmac_verified BOOLEAN DEFAULT false,
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Constraints
                        CHECK (platform IN (''etsy'', ''shopify'')),
                        CHECK (processing_status IN (''pending'', ''processed'', ''failed'', ''ignored''))
                    );
                    
                    CREATE INDEX idx_webhooks_platform ON %I.platform_webhooks(platform);
                    CREATE INDEX idx_webhooks_status ON %I.platform_webhooks(processing_status);
                    CREATE INDEX idx_webhooks_topic ON %I.platform_webhooks(topic);
                    CREATE INDEX idx_webhooks_created ON %I.platform_webhooks(created_at);
                ', schema_name, schema_name, schema_name, schema_name, schema_name);
                
                -- Batch operations tracking
                EXECUTE format('
                    CREATE TABLE %I.platform_batch_operations (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
                        tenant_id VARCHAR(50) NOT NULL,
                        
                        -- Operation details
                        platform VARCHAR(50) NOT NULL, -- etsy, shopify
                        operation_type VARCHAR(50) NOT NULL, -- bulk_update, bulk_delete, bulk_publish, etc.
                        target_entity VARCHAR(50) NOT NULL, -- products, collections, orders
                        
                        -- Progress tracking
                        total_items INTEGER DEFAULT 0,
                        processed_items INTEGER DEFAULT 0,
                        successful_items INTEGER DEFAULT 0,
                        failed_items INTEGER DEFAULT 0,
                        
                        -- Status
                        status VARCHAR(50) DEFAULT ''pending'',
                        started_at TIMESTAMP WITH TIME ZONE,
                        completed_at TIMESTAMP WITH TIME ZONE,
                        
                        -- Operation data
                        operation_data JSONB, -- Parameters for the operation
                        results JSONB, -- Results and errors
                        
                        -- Progress tracking
                        progress_percentage DECIMAL(5,2) DEFAULT 0.0,
                        estimated_completion TIMESTAMP WITH TIME ZONE,
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Constraints
                        CHECK (platform IN (''etsy'', ''shopify'')),
                        CHECK (status IN (''pending'', ''running'', ''completed'', ''failed'', ''cancelled''))
                    );
                    
                    CREATE INDEX idx_batch_ops_user ON %I.platform_batch_operations(user_id);
                    CREATE INDEX idx_batch_ops_platform ON %I.platform_batch_operations(platform);
                    CREATE INDEX idx_batch_ops_status ON %I.platform_batch_operations(status);
                    CREATE INDEX idx_batch_ops_created ON %I.platform_batch_operations(created_at);
                ', schema_name, schema_name, schema_name, schema_name, schema_name);
                
                -- Collection sync (Shopify specific)
                EXECUTE format('
                    CREATE TABLE %I.shopify_collection_sync (
                        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                        user_id UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
                        tenant_id VARCHAR(50) NOT NULL,
                        
                        -- Collection data
                        shopify_collection_id VARCHAR(50) NOT NULL,
                        collection_type VARCHAR(20) NOT NULL, -- smart, custom
                        collection_data JSONB NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        handle VARCHAR(255),
                        
                        -- Sync metadata
                        sync_status VARCHAR(50) DEFAULT ''synced'',
                        last_sync_at TIMESTAMP WITH TIME ZONE,
                        is_managed_locally BOOLEAN DEFAULT false, -- Whether we manage this collection
                        
                        -- Timestamps
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        
                        -- Constraints
                        UNIQUE(user_id, shopify_collection_id),
                        CHECK (collection_type IN (''smart'', ''custom''))
                    );
                    
                    CREATE INDEX idx_shopify_collections_user ON %I.shopify_collection_sync(user_id);
                    CREATE INDEX idx_shopify_collections_type ON %I.shopify_collection_sync(collection_type);
                ', schema_name, schema_name);
                
                -- Template tags association tables
                EXECUTE format('
                    CREATE TABLE %I.etsy_template_tags (
                        template_id UUID REFERENCES %I.etsy_product_templates(id) ON DELETE CASCADE,
                        tag VARCHAR(100),
                        tenant_id VARCHAR(50) NOT NULL,
                        PRIMARY KEY (template_id, tag)
                    );
                    
                    CREATE TABLE %I.shopify_template_tags (
                        template_id UUID REFERENCES %I.shopify_product_templates(id) ON DELETE CASCADE,
                        tag VARCHAR(100),
                        tenant_id VARCHAR(50) NOT NULL,
                        PRIMARY KEY (template_id, tag)
                    );
                ', schema_name, schema_name, schema_name, schema_name);
                
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Create triggers for updated_at timestamps
        cur.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            
            -- Add trigger to OAuth tokens table
            DROP TRIGGER IF EXISTS update_oauth_tokens_updated_at ON core.third_party_oauth_tokens;
            CREATE TRIGGER update_oauth_tokens_updated_at
                BEFORE UPDATE ON core.third_party_oauth_tokens
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)
        
        # Create function to update existing tenant schemas
        cur.execute("""
            CREATE OR REPLACE FUNCTION add_integration_tables_to_existing_tenants()
            RETURNS VOID AS $$
            DECLARE
                tenant_record RECORD;
            BEGIN
                FOR tenant_record IN SELECT tenant_id, schema_name FROM core.tenants WHERE is_active = true
                LOOP
                    RAISE NOTICE 'Adding integration tables to tenant schema: %', tenant_record.schema_name;
                    PERFORM create_tenant_integration_tables(tenant_record.schema_name);
                END LOOP;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        # Apply to existing tenants
        cur.execute("SELECT add_integration_tables_to_existing_tenants();")
        
        # Update the create_tenant_schema function to include integration tables
        cur.execute("""
            CREATE OR REPLACE FUNCTION create_tenant_schema(tenant_id_param TEXT, schema_name_param TEXT)
            RETURNS VOID AS $$
            BEGIN
                -- Create the schema
                EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name_param);
                
                -- Create tenant record
                INSERT INTO core.tenants (tenant_id, schema_name, is_active)
                VALUES (tenant_id_param, schema_name_param, true)
                ON CONFLICT (tenant_id) DO UPDATE SET
                    schema_name = EXCLUDED.schema_name,
                    is_active = true,
                    updated_at = CURRENT_TIMESTAMP;
                
                -- Create base tables (from previous migrations)
                PERFORM create_tenant_tables(schema_name_param);
                
                -- Create integration tables
                PERFORM create_tenant_integration_tables(schema_name_param);
                
                RAISE NOTICE 'Tenant schema % created successfully for tenant %', schema_name_param, tenant_id_param;
            END;
            $$ LANGUAGE plpgsql;
        """)
        
        logger.info("Integration tables created successfully")

def downgrade():
    """Rollback the migration"""
    
    import threading
    conn = getattr(threading.current_thread(), '_migration_connection', None)
    if not conn:
        raise RuntimeError("No database connection available in migration context")
    
    with conn.cursor() as cur:
        logger.info("Rolling back integration tables...")
        
        # Drop the integration table creation function
        cur.execute("DROP FUNCTION IF EXISTS create_tenant_integration_tables(TEXT);")
        cur.execute("DROP FUNCTION IF EXISTS add_integration_tables_to_existing_tenants();")
        
        # Drop tables from all tenant schemas
        cur.execute("""
            DO $$
            DECLARE
                tenant_record RECORD;
            BEGIN
                FOR tenant_record IN SELECT schema_name FROM core.tenants WHERE is_active = true
                LOOP
                    EXECUTE format('DROP TABLE IF EXISTS %I.etsy_template_tags CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.shopify_template_tags CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.shopify_collection_sync CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.platform_batch_operations CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.platform_webhooks CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.shopify_order_sync CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.etsy_order_sync CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.shopify_product_sync CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.etsy_product_sync CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.shopify_product_templates CASCADE', tenant_record.schema_name);
                    EXECUTE format('DROP TABLE IF EXISTS %I.etsy_product_templates CASCADE', tenant_record.schema_name);
                END LOOP;
            END;
            $$;
        """)
        
        # Drop core tables
        cur.execute("DROP TABLE IF EXISTS core.third_party_oauth_tokens CASCADE;")
        
        # Drop trigger function
        cur.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;")
        
        logger.info("Integration tables rolled back successfully")