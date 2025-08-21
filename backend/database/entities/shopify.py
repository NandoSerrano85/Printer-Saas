from sqlalchemy import Column, String, Integer, Boolean, JSON, Text, DECIMAL, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime, timezone
from .base import MultiTenantBase, TimestampMixin, SoftDeleteMixin, UserScopedMixin

class ShopifyProductTemplate(MultiTenantBase, TimestampMixin, SoftDeleteMixin, UserScopedMixin):
    """Shopify product template for consistent product creation"""
    __tablename__ = 'shopify_product_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    
    # Template data structure (JSON)
    template_data = Column(JSON, nullable=False)  # Shopify product structure
    
    # Template metadata
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    tags = Column(Text)  # Comma-separated tags
    
    # Shopify-specific fields
    product_type = Column(String(255))
    vendor = Column(String(255))
    handle = Column(String(255))  # URL handle
    seo_title = Column(String(70))
    seo_description = Column(String(320))
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<ShopifyProductTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"


class ShopifyProductSync(MultiTenantBase, TimestampMixin, UserScopedMixin):
    """Track Shopify product synchronization status"""
    __tablename__ = 'shopify_product_sync'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    shopify_product_id = Column(String(50), nullable=False)  # Shopify product ID
    internal_product_id = Column(UUID(as_uuid=True), ForeignKey('shopify_product_templates.id'))
    
    # Sync status
    sync_status = Column(String(50), default='pending')  # pending, synced, error, manual
    last_sync_at = Column(DateTime(timezone=True))
    sync_error_message = Column(Text)
    
    # Product data snapshot
    shopify_data = Column(JSON)  # Last known Shopify data
    local_modifications = Column(JSON)  # Local changes not yet synced
    
    # Sync metadata
    sync_direction = Column(String(20), default='bidirectional')  # to_shopify, from_shopify, bidirectional
    auto_sync_enabled = Column(Boolean, default=True)
    
    # Relationships
    template = relationship("ShopifyProductTemplate", backref="sync_records")
    
    def __repr__(self):
        return f"<ShopifyProductSync(shopify_id={self.shopify_product_id}, status='{self.sync_status}')>"


class ShopifyOrderSync(MultiTenantBase, TimestampMixin, UserScopedMixin):
    """Track Shopify order synchronization"""
    __tablename__ = 'shopify_order_sync'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    shopify_order_id = Column(String(50), nullable=False)  # Shopify order ID
    internal_order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id'))
    
    # Sync status
    sync_status = Column(String(50), default='pending')
    last_sync_at = Column(DateTime(timezone=True))
    sync_error_message = Column(Text)
    
    # Order data
    shopify_order_data = Column(JSON)  # Complete Shopify order data
    order_number = Column(String(50))  # Shopify order number
    financial_status = Column(String(50))
    fulfillment_status = Column(String(50))
    
    # Processing metadata
    webhook_processed = Column(Boolean, default=False)
    requires_manual_review = Column(Boolean, default=False)
    review_notes = Column(Text)
    
    def __repr__(self):
        return f"<ShopifyOrderSync(shopify_order_id={self.shopify_order_id}, order_number='{self.order_number}')>"


class ShopifyWebhook(MultiTenantBase, TimestampMixin):
    """Track Shopify webhook events"""
    __tablename__ = 'shopify_webhooks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    webhook_id = Column(String(50))  # Shopify webhook ID
    topic = Column(String(100), nullable=False)  # e.g., 'orders/create', 'products/update'
    
    # Event data
    shopify_shop_domain = Column(String(255), nullable=False)
    event_data = Column(JSON, nullable=False)
    headers = Column(JSON)
    
    # Processing status
    processing_status = Column(String(50), default='pending')  # pending, processed, failed, ignored
    processed_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)
    retry_count = Column(Integer, default=0)
    
    # Verification
    hmac_verified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<ShopifyWebhook(topic='{self.topic}', shop='{self.shopify_shop_domain}', status='{self.processing_status}')>"


class ShopifyCollectionSync(MultiTenantBase, TimestampMixin, UserScopedMixin):
    """Track Shopify collection synchronization"""
    __tablename__ = 'shopify_collection_sync'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    shopify_collection_id = Column(String(50), nullable=False)
    collection_type = Column(String(20), nullable=False)  # smart, custom
    
    # Collection data
    collection_data = Column(JSON, nullable=False)
    title = Column(String(255), nullable=False)
    handle = Column(String(255))
    
    # Sync metadata
    sync_status = Column(String(50), default='synced')
    last_sync_at = Column(DateTime(timezone=True))
    is_managed_locally = Column(Boolean, default=False)  # Whether we manage this collection
    
    def __repr__(self):
        return f"<ShopifyCollectionSync(collection_id={self.shopify_collection_id}, title='{self.title}')>"


class ShopifyBatchOperation(MultiTenantBase, TimestampMixin, UserScopedMixin):
    """Track batch operations on Shopify"""
    __tablename__ = 'shopify_batch_operations'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    operation_type = Column(String(50), nullable=False)  # bulk_update, bulk_delete, bulk_publish, etc.
    
    # Operation details
    target_entity = Column(String(50), nullable=False)  # products, collections, orders
    total_items = Column(Integer, default=0)
    processed_items = Column(Integer, default=0)
    successful_items = Column(Integer, default=0)
    failed_items = Column(Integer, default=0)
    
    # Status tracking
    status = Column(String(50), default='pending')  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # Operation data
    operation_data = Column(JSON)  # Parameters for the operation
    results = Column(JSON)  # Results and errors
    
    # Progress tracking
    progress_percentage = Column(DECIMAL(5, 2), default=0.0)
    estimated_completion = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<ShopifyBatchOperation(type='{self.operation_type}', status='{self.status}', progress={self.progress_percentage}%)>"


# Association table for product template tags
shopify_template_tags = Table(
    'shopify_template_tags',
    MultiTenantBase.metadata,
    Column('template_id', UUID(as_uuid=True), ForeignKey('shopify_product_templates.id'), primary_key=True),
    Column('tag', String(100), primary_key=True),
    Column('tenant_id', String(50), nullable=False)
)