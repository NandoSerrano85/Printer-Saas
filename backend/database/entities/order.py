from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey, JSON, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin

class Order(MultiTenantBase, SoftDeleteMixin, AuditMixin):
    """Orders from various sources (Etsy, Shopify, etc.)"""
    __tablename__ = 'orders'
    
    # User relationship (nullable for external orders)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    
    # External platform information
    etsy_receipt_id = Column(Integer, nullable=True, index=True)  # Etsy receipt ID
    etsy_order_id = Column(Integer, nullable=True, index=True)   # Etsy order ID
    shopify_order_id = Column(Integer, nullable=True, index=True) # Shopify order ID
    platform = Column(String(50), nullable=False, index=True)    # etsy, shopify, manual, etc.
    
    # Order identification
    order_number = Column(String(100), nullable=True, index=True)  # Platform order number
    internal_order_number = Column(String(100), nullable=True, index=True)  # Our internal numbering
    
    # Order status and workflow
    status = Column(String(50), default='pending', index=True)  # pending, processing, shipped, completed, cancelled
    fulfillment_status = Column(String(50), default='unfulfilled', index=True)  # unfulfilled, partial, fulfilled
    payment_status = Column(String(50), default='pending', index=True)  # pending, paid, refunded, disputed
    
    # Financial information
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(10, 2), nullable=True)
    tax_amount = Column(DECIMAL(10, 2), default=0)
    shipping_amount = Column(DECIMAL(10, 2), default=0)
    discount_amount = Column(DECIMAL(10, 2), default=0)
    currency = Column(String(3), default='USD')
    
    # Customer information
    customer_email = Column(String(255), nullable=True, index=True)
    customer_name = Column(String(255), nullable=True)
    customer_phone = Column(String(50), nullable=True)
    customer_id = Column(String(100), nullable=True, index=True)  # External customer ID
    
    # Addresses
    billing_address = Column(JSON, default=dict)
    shipping_address = Column(JSON, default=dict)
    
    # Order details
    items_count = Column(Integer, default=0)
    total_quantity = Column(Integer, default=0)
    special_instructions = Column(Text, nullable=True)
    gift_message = Column(Text, nullable=True)
    
    # Dates and timing
    order_date = Column(DateTime(timezone=True), nullable=True, index=True)
    promised_date = Column(DateTime(timezone=True), nullable=True)
    shipped_date = Column(DateTime(timezone=True), nullable=True)
    delivered_date = Column(DateTime(timezone=True), nullable=True)
    
    # Processing information
    processing_priority = Column(Integer, default=0)  # Higher numbers = higher priority
    processing_notes = Column(Text, nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Metadata and tracking
    order_metadata = Column(JSON, default=dict)  # Flexible metadata storage
    tracking_numbers = Column(JSON, default=list)  # Array of tracking numbers
    tags = Column(JSON, default=list)  # Array of tags for organization
    
    # Analytics
    profit_margin = Column(DECIMAL(10, 2), nullable=True)
    cost_of_goods = Column(DECIMAL(10, 2), nullable=True)
    processing_time_hours = Column(Float, nullable=True)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id], back_populates='orders')
    assigned_user = relationship('User', foreign_keys=[assigned_to])
    order_items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    order_fulfillments = relationship('OrderFulfillment', back_populates='order', cascade='all, delete-orphan')
    order_notes = relationship('OrderNote', back_populates='order', cascade='all, delete-orphan')
    
    @property
    def is_rush_order(self):
        """Check if order is a rush order based on processing time"""
        if not self.promised_date or not self.order_date:
            return False
        days_to_fulfill = (self.promised_date - self.order_date).days
        return days_to_fulfill <= 2
    
    @property
    def days_since_order(self):
        """Get days since order was placed"""
        if not self.order_date:
            return 0
        from datetime import datetime, timezone
        return (datetime.now(timezone.utc) - self.order_date).days
    
    @property
    def is_overdue(self):
        """Check if order is past promised date"""
        if not self.promised_date:
            return False
        from datetime import datetime, timezone
        return datetime.now(timezone.utc) > self.promised_date and self.status not in ['shipped', 'completed']
    
    def get_customer_address(self, address_type='shipping'):
        """Get formatted customer address"""
        address = self.shipping_address if address_type == 'shipping' else self.billing_address
        if not address:
            return None
        return {
            'name': address.get('name', self.customer_name),
            'line1': address.get('line1', ''),
            'line2': address.get('line2', ''),
            'city': address.get('city', ''),
            'state': address.get('state', ''),
            'zip': address.get('zip', ''),
            'country': address.get('country', '')
        }
    
    def calculate_totals(self):
        """Recalculate order totals from items"""
        if not self.order_items:
            return
        
        subtotal = sum(item.total_price for item in self.order_items)
        self.subtotal = subtotal
        self.total_amount = subtotal + self.tax_amount + self.shipping_amount - self.discount_amount
        self.items_count = len(self.order_items)
        self.total_quantity = sum(item.quantity for item in self.order_items)
    
    def __repr__(self):
        return f"<Order(id='{self.id}', number='{self.order_number}', status='{self.status}', total=${self.total_amount})>"

class OrderItem(MultiTenantBase, UserScopedMixin):
    """Individual items within an order"""
    __tablename__ = 'order_items'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Product references
    product_template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id'), nullable=True, index=True)
    design_id = Column(UUID(as_uuid=True), ForeignKey('design_images.id'), nullable=True, index=True)
    mockup_id = Column(UUID(as_uuid=True), ForeignKey('mockups.id'), nullable=True, index=True)
    
    # External product information
    etsy_listing_id = Column(Integer, nullable=True, index=True)
    etsy_product_id = Column(Integer, nullable=True)
    shopify_product_id = Column(Integer, nullable=True, index=True)
    shopify_variant_id = Column(Integer, nullable=True)
    
    # Item details
    product_name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=True, index=True)
    variant_name = Column(String(255), nullable=True)  # Size, color, etc.
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    
    # Customization
    customization_text = Column(Text, nullable=True)
    customization_options = Column(JSON, default=dict)  # Size, color, personalization, etc.
    custom_design_uploaded = Column(Boolean, default=False)
    
    # Production information
    production_status = Column(String(50), default='pending', index=True)  # pending, designing, printing, quality_check, completed
    production_notes = Column(Text, nullable=True)
    estimated_production_time = Column(Integer, nullable=True)  # Hours
    actual_production_time = Column(Integer, nullable=True)    # Hours
    
    # Quality and fulfillment
    quality_check_status = Column(String(50), default='pending')  # pending, passed, failed, rework
    quality_notes = Column(Text, nullable=True)
    fulfillment_status = Column(String(50), default='pending')  # pending, printed, packaged, shipped
    
    # Costs and margins
    cost_of_materials = Column(DECIMAL(8, 2), nullable=True)
    cost_of_labor = Column(DECIMAL(8, 2), nullable=True)
    cost_of_shipping = Column(DECIMAL(8, 2), nullable=True)
    profit_margin = Column(DECIMAL(8, 2), nullable=True)
    
    # Relationships
    user = relationship('User')
    order = relationship('Order', back_populates='order_items')
    product_template = relationship('EtsyProductTemplate', back_populates='order_items')
    design = relationship('DesignImage')
    mockup = relationship('Mockup', back_populates='order_items')
    
    @property
    def is_custom_order(self):
        """Check if this is a custom/personalized order"""
        return bool(self.customization_text or self.customization_options or self.custom_design_uploaded)
    
    @property
    def is_ready_for_production(self):
        """Check if item is ready for production"""
        return self.production_status == 'pending' and (
            not self.is_custom_order or 
            (self.customization_text or self.customization_options)
        )
    
    def calculate_profit(self):
        """Calculate profit margin for this item"""
        total_cost = (self.cost_of_materials or 0) + (self.cost_of_labor or 0) + (self.cost_of_shipping or 0)
        self.profit_margin = self.total_price - total_cost
        return self.profit_margin
    
    def __repr__(self):
        return f"<OrderItem(id='{self.id}', product='{self.product_name}', qty={self.quantity}, price=${self.total_price})>"

class OrderFulfillment(MultiTenantBase, UserScopedMixin):
    """Fulfillment/shipping records for orders"""
    __tablename__ = 'order_fulfillments'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Fulfillment details
    tracking_number = Column(String(100), nullable=True, index=True)
    carrier = Column(String(50), nullable=True)  # USPS, FedEx, UPS, etc.
    service_level = Column(String(50), nullable=True)  # Priority, Ground, Express, etc.
    
    # Addresses
    ship_from_address = Column(JSON, default=dict)
    ship_to_address = Column(JSON, default=dict)
    
    # Status and dates
    status = Column(String(50), default='pending', index=True)  # pending, shipped, in_transit, delivered, failed
    shipped_date = Column(DateTime(timezone=True), nullable=True)
    expected_delivery_date = Column(DateTime(timezone=True), nullable=True)
    actual_delivery_date = Column(DateTime(timezone=True), nullable=True)
    
    # Costs and details
    shipping_cost = Column(DECIMAL(8, 2), nullable=True)
    insurance_cost = Column(DECIMAL(8, 2), nullable=True)
    weight_oz = Column(Float, nullable=True)
    dimensions = Column(JSON, default=dict)  # length, width, height
    
    # Items included in this fulfillment
    fulfilled_items = Column(JSON, default=list)  # Array of order item IDs
    
    # Notes and metadata
    fulfillment_notes = Column(Text, nullable=True)
    item_metadata = Column(JSON, default=dict)
    
    # Relationships
    user = relationship('User')
    order = relationship('Order', back_populates='order_fulfillments')
    
    @property
    def is_delivered(self):
        """Check if fulfillment is delivered"""
        return self.status == 'delivered'
    
    @property
    def days_in_transit(self):
        """Calculate days in transit"""
        if not self.shipped_date:
            return 0
        end_date = self.actual_delivery_date or datetime.now(timezone.utc)
        return (end_date - self.shipped_date).days
    
    def __repr__(self):
        return f"<OrderFulfillment(id='{self.id}', tracking='{self.tracking_number}', status='{self.status}')>"

class OrderNote(MultiTenantBase, UserScopedMixin):
    """Notes and comments on orders"""
    __tablename__ = 'order_notes'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)
    
    # Note content
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(String(50), default='general', index=True)  # general, production, customer, internal
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    
    # Visibility and status
    is_customer_visible = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False, index=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    attachments = Column(JSON, default=list)  # Array of file attachments
    tags = Column(JSON, default=list)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id])
    order = relationship('Order', back_populates='order_notes')
    author = relationship('User', foreign_keys=[author_id])
    resolved_by_user = relationship('User', foreign_keys=[resolved_by])
    
    def mark_resolved(self, resolved_by_user_id: str = None):
        """Mark note as resolved"""
        from datetime import datetime, timezone
        self.is_resolved = True
        self.resolved_at = datetime.now(timezone.utc)
        if resolved_by_user_id:
            self.resolved_by = resolved_by_user_id
    
    def __repr__(self):
        return f"<OrderNote(id='{self.id}', type='{self.note_type}', resolved={self.is_resolved})>"

class OrderStatusHistory(MultiTenantBase, UserScopedMixin):
    """History of order status changes"""
    __tablename__ = 'order_status_history'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    changed_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Status change details
    old_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=False, index=True)
    change_reason = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Automatic vs manual change
    is_automatic = Column(Boolean, default=False)
    trigger_source = Column(String(50), nullable=True)  # system, user, webhook, etc.
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id])
    order = relationship('Order')
    changed_by_user = relationship('User', foreign_keys=[changed_by])
    
    def __repr__(self):
        return f"<OrderStatusHistory(order_id='{self.order_id}', {self.old_status} -> {self.new_status})>"