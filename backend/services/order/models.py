from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class FulfillmentStatus(str, Enum):
    UNFULFILLED = "unfulfilled"
    PARTIAL = "partial"
    FULFILLED = "fulfilled"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    FAILED = "failed"

class OrderPlatform(str, Enum):
    ETSY = "etsy"
    SHOPIFY = "shopify"
    MANUAL = "manual"
    API = "api"

class AddressModel(BaseModel):
    name: Optional[str] = None
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    zip: str
    country: str
    phone: Optional[str] = None

class OrderItemBase(BaseModel):
    product_template_id: Optional[UUID] = None
    design_id: Optional[UUID] = None
    mockup_id: Optional[UUID] = None
    product_name: str = Field(..., min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    variant_name: Optional[str] = Field(None, max_length=255)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    total_price: Decimal = Field(..., ge=0)
    
    # External platform references
    etsy_listing_id: Optional[int] = None
    etsy_product_id: Optional[int] = None
    shopify_product_id: Optional[int] = None
    shopify_variant_id: Optional[int] = None
    
    # Customization
    customization_text: Optional[str] = None
    customization_options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    custom_design_uploaded: bool = False
    
    # Production
    production_notes: Optional[str] = None
    estimated_production_time: Optional[int] = None  # hours
    
    @validator('total_price')
    def validate_total_price(cls, v, values):
        quantity = values.get('quantity', 1)
        unit_price = values.get('unit_price', 0)
        expected_total = quantity * unit_price
        if abs(float(v) - float(expected_total)) > 0.01:  # Allow for small rounding differences
            raise ValueError(f'Total price {v} does not match quantity × unit_price ({expected_total})')
        return v

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemUpdate(BaseModel):
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, max_length=100)
    variant_name: Optional[str] = Field(None, max_length=255)
    quantity: Optional[int] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)
    total_price: Optional[Decimal] = Field(None, ge=0)
    customization_text: Optional[str] = None
    customization_options: Optional[Dict[str, Any]] = None
    production_notes: Optional[str] = None
    estimated_production_time: Optional[int] = None

class OrderItemResponse(OrderItemBase):
    id: UUID
    order_id: UUID
    user_id: UUID
    tenant_id: str
    
    # Production status
    production_status: str = "pending"
    quality_check_status: str = "pending"
    fulfillment_status: str = "pending"
    actual_production_time: Optional[int] = None
    
    # Costs
    cost_of_materials: Optional[Decimal] = None
    cost_of_labor: Optional[Decimal] = None
    profit_margin: Optional[Decimal] = None
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    # External platform information
    etsy_receipt_id: Optional[int] = None
    etsy_order_id: Optional[int] = None
    shopify_order_id: Optional[int] = None
    platform: OrderPlatform = OrderPlatform.MANUAL
    order_number: Optional[str] = Field(None, max_length=100)
    
    # Financial information
    total_amount: Decimal = Field(..., ge=0)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Decimal = Field(0, ge=0)
    shipping_amount: Decimal = Field(0, ge=0)
    discount_amount: Decimal = Field(0, ge=0)
    currency: str = Field("USD", max_length=3)
    
    # Customer information
    customer_email: Optional[str] = Field(None, max_length=255)
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=50)
    customer_id: Optional[str] = Field(None, max_length=100)
    
    # Addresses
    billing_address: Optional[AddressModel] = None
    shipping_address: Optional[AddressModel] = None
    
    # Order details
    special_instructions: Optional[str] = None
    gift_message: Optional[str] = None
    
    # Dates
    order_date: Optional[datetime] = None
    promised_date: Optional[datetime] = None
    
    # Processing
    processing_priority: int = Field(0, description="Higher numbers = higher priority")
    processing_notes: Optional[str] = None
    
    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        subtotal = values.get('subtotal', v)
        tax_amount = values.get('tax_amount', 0)
        shipping_amount = values.get('shipping_amount', 0)
        discount_amount = values.get('discount_amount', 0)
        
        expected_total = subtotal + tax_amount + shipping_amount - discount_amount
        if abs(float(v) - float(expected_total)) > 0.01:
            raise ValueError(f'Total amount {v} does not match calculated total ({expected_total})')
        return v

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_items=1)

class OrderUpdate(BaseModel):
    etsy_receipt_id: Optional[int] = None
    etsy_order_id: Optional[int] = None
    shopify_order_id: Optional[int] = None
    platform: Optional[OrderPlatform] = None
    order_number: Optional[str] = Field(None, max_length=100)
    
    # Status updates
    status: Optional[OrderStatus] = None
    fulfillment_status: Optional[FulfillmentStatus] = None
    payment_status: Optional[PaymentStatus] = None
    
    # Financial information
    total_amount: Optional[Decimal] = Field(None, ge=0)
    subtotal: Optional[Decimal] = Field(None, ge=0)
    tax_amount: Optional[Decimal] = Field(None, ge=0)
    shipping_amount: Optional[Decimal] = Field(None, ge=0)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Customer information
    customer_email: Optional[str] = Field(None, max_length=255)
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=50)
    
    # Addresses
    billing_address: Optional[AddressModel] = None
    shipping_address: Optional[AddressModel] = None
    
    # Order details
    special_instructions: Optional[str] = None
    gift_message: Optional[str] = None
    
    # Dates
    promised_date: Optional[datetime] = None
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    
    # Processing
    processing_priority: Optional[int] = None
    processing_notes: Optional[str] = None
    assigned_to: Optional[UUID] = None

class OrderResponse(OrderBase):
    id: UUID
    user_id: UUID
    tenant_id: str
    internal_order_number: Optional[str] = None
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.UNFULFILLED
    payment_status: PaymentStatus = PaymentStatus.PENDING
    
    # Computed fields
    items_count: int = 0
    total_quantity: int = 0
    
    # Dates
    shipped_date: Optional[datetime] = None
    delivered_date: Optional[datetime] = None
    
    # Processing
    assigned_to: Optional[UUID] = None
    
    # Analytics
    profit_margin: Optional[Decimal] = None
    cost_of_goods: Optional[Decimal] = None
    processing_time_hours: Optional[float] = None
    
    # Tracking
    tracking_numbers: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Relationships
    items: List[OrderItemResponse] = Field(default_factory=list)
    
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

class OrderStatsResponse(BaseModel):
    total_orders: int
    pending_orders: int
    processing_orders: int
    completed_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    orders_by_status: Dict[str, int]
    orders_by_platform: Dict[str, int]
    recent_orders: List[OrderResponse]

class OrderNoteCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=1)
    note_type: str = Field("general", description="Note type: general, production, customer, internal")
    priority: str = Field("normal", description="Priority: low, normal, high, urgent")
    is_customer_visible: bool = Field(False)
    tags: List[str] = Field(default_factory=list)

class OrderNoteResponse(OrderNoteCreate):
    id: UUID
    order_id: UUID
    author_id: UUID
    user_id: UUID
    tenant_id: str
    is_resolved: bool = False
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    attachments: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class OrderFulfillmentCreate(BaseModel):
    tracking_number: Optional[str] = Field(None, max_length=100)
    carrier: Optional[str] = Field(None, max_length=50)
    service_level: Optional[str] = Field(None, max_length=50)
    shipping_cost: Optional[Decimal] = Field(None, ge=0)
    insurance_cost: Optional[Decimal] = Field(None, ge=0)
    weight_oz: Optional[float] = Field(None, ge=0)
    dimensions: Optional[Dict[str, float]] = None
    fulfilled_items: List[UUID] = Field(default_factory=list, description="Order item IDs fulfilled")
    fulfillment_notes: Optional[str] = None

class OrderFulfillmentResponse(OrderFulfillmentCreate):
    id: UUID
    order_id: UUID
    user_id: UUID
    tenant_id: str
    status: str = "pending"  # pending, shipped, in_transit, delivered, failed
    ship_from_address: Optional[Dict[str, str]] = None
    ship_to_address: Optional[Dict[str, str]] = None
    shipped_date: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class OrderStatusUpdateRequest(BaseModel):
    status: OrderStatus
    notes: Optional[str] = None
    notify_customer: bool = False

class OrderBulkOperationRequest(BaseModel):
    order_ids: List[UUID] = Field(..., min_items=1)
    operation: str = Field(..., description="Operation: update_status, assign, add_tags, export")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['update_status', 'assign', 'add_tags', 'remove_tags', 'export']
        if v not in allowed_operations:
            raise ValueError(f'Operation must be one of: {", ".join(allowed_operations)}')
        return v

class OrderBulkOperationResponse(BaseModel):
    successful: List[UUID]
    failed: List[Dict[str, Any]]  # [{"id": UUID, "error": str}]
    total_requested: int
    total_successful: int
    total_failed: int