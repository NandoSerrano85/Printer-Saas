from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum

# Shopify API Configuration
class ShopifyAPIConfig(BaseModel):
    """Shopify API configuration constants"""
    base_url: str = "https://{shop}.myshopify.com"
    admin_api_path: str = "/admin/api/2023-10"
    oauth_url: str = "https://{shop}.myshopify.com/admin/oauth/authorize"
    token_url: str = "https://{shop}.myshopify.com/admin/oauth/access_token"
    scopes: str = "read_products,write_products,read_orders,write_orders,read_customers,write_customers,read_inventory,write_inventory,read_files"
    redirect_uri_param: str = "redirect_uri"

# OAuth Models
class ShopifyOAuthInitRequest(BaseModel):
    """Request to initiate Shopify OAuth flow"""
    shop_domain: str = Field(..., description="Shopify shop domain (e.g., mystore.myshopify.com)")
    redirect_uri: str = Field(..., description="OAuth callback URI")

class ShopifyOAuthInitResponse(BaseModel):
    """Response with OAuth flow data"""
    oauth_url: str
    shop_domain: str
    client_id: str
    redirect_uri: str
    scopes: str
    state: str
    
class ShopifyOAuthCallbackRequest(BaseModel):
    """OAuth callback data from Shopify"""
    code: str = Field(..., description="Authorization code from Shopify")
    shop: str = Field(..., description="Shop domain")
    state: str = Field(..., description="State parameter for CSRF protection")
    hmac: Optional[str] = Field(None, description="HMAC signature for verification")

class ShopifyTokenResponse(BaseModel):
    """Shopify token response"""
    access_token: str
    scope: str
    expires_at: Optional[datetime] = None  # Shopify tokens don't expire
    shop_domain: str

# Shop Models
class ShopifyShop(BaseModel):
    """Shopify shop information"""
    id: int
    name: str
    domain: str
    myshopify_domain: str
    email: str
    customer_email: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    currency: str = "USD"
    timezone: str = "(GMT-05:00) Eastern Time (US & Canada)"
    iana_timezone: Optional[str] = None
    phone: Optional[str] = None
    province: Optional[str] = None
    province_code: Optional[str] = None
    zip: Optional[str] = None
    money_format: str = "${{amount}}"
    money_with_currency_format: str = "${{amount}} USD"
    weight_unit: str = "lb"
    plan_name: Optional[str] = None
    plan_display_name: Optional[str] = None
    shop_owner: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    primary_locale: str = "en"
    primary_location_id: Optional[int] = None
    multi_location_enabled: bool = False
    setup_required: bool = False
    enabled_presentment_currencies: List[str] = Field(default_factory=list)

# Product Models
class ShopifyProductStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"

class ShopifyProductType(str, Enum):
    SIMPLE = "simple"
    GIFT_CARD = "gift_card"

class ShopifyInventoryPolicy(str, Enum):
    DENY = "deny"
    CONTINUE = "continue"

class ShopifyWeightUnit(str, Enum):
    G = "g"
    KG = "kg"
    OZ = "oz"
    LB = "lb"

class ShopifyOption(BaseModel):
    """Product option (Color, Size, etc.)"""
    id: Optional[int] = None
    product_id: Optional[int] = None
    name: str = Field(..., max_length=255)
    position: int = 1
    values: List[str] = Field(..., min_items=1, max_items=100)

class ShopifyVariant(BaseModel):
    """Product variant"""
    id: Optional[int] = None
    product_id: Optional[int] = None
    title: str
    price: Decimal = Field(..., ge=0)
    sku: Optional[str] = Field(None, max_length=255)
    position: int = 1
    inventory_policy: ShopifyInventoryPolicy = ShopifyInventoryPolicy.DENY
    compare_at_price: Optional[Decimal] = Field(None, ge=0)
    fulfillment_service: str = "manual"
    inventory_management: Optional[str] = "shopify"
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    taxable: bool = True
    barcode: Optional[str] = None
    grams: Optional[int] = Field(None, ge=0)
    image_id: Optional[int] = None
    weight: Optional[float] = Field(None, ge=0)
    weight_unit: ShopifyWeightUnit = ShopifyWeightUnit.LB
    inventory_item_id: Optional[int] = None
    inventory_quantity: int = 0
    old_inventory_quantity: Optional[int] = None
    requires_shipping: bool = True

class ShopifyImage(BaseModel):
    """Product image"""
    id: Optional[int] = None
    product_id: Optional[int] = None
    position: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    src: str
    variant_ids: List[int] = Field(default_factory=list)

class ShopifyProductCreate(BaseModel):
    """Create Shopify product request"""
    title: str = Field(..., min_length=1, max_length=255)
    body_html: Optional[str] = Field(None, description="Product description in HTML")
    vendor: Optional[str] = Field(None, max_length=255)
    product_type: Optional[str] = Field(None, max_length=255)
    handle: Optional[str] = Field(None, max_length=255, description="URL handle")
    status: ShopifyProductStatus = ShopifyProductStatus.DRAFT
    published_scope: str = "web"
    tags: Optional[str] = Field(None, description="Comma-separated tags")
    images: List[ShopifyImage] = Field(default_factory=list)
    options: List[ShopifyOption] = Field(default_factory=list)
    variants: List[ShopifyVariant] = Field(default_factory=list, min_items=1)
    metafields: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    seo_title: Optional[str] = Field(None, max_length=70)
    seo_description: Optional[str] = Field(None, max_length=320)
    
    @validator('variants')
    def validate_variants(cls, v):
        if not v:
            # Create default variant if none provided
            return [ShopifyVariant(title="Default Title", price=Decimal('0.00'))]
        return v

class ShopifyProduct(BaseModel):
    """Shopify product response"""
    id: int
    title: str
    body_html: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    created_at: datetime
    handle: str
    updated_at: datetime
    published_at: Optional[datetime] = None
    template_suffix: Optional[str] = None
    status: ShopifyProductStatus
    published_scope: str
    tags: str = ""
    admin_graphql_api_id: Optional[str] = None
    variants: List[ShopifyVariant] = Field(default_factory=list)
    options: List[ShopifyOption] = Field(default_factory=list)
    images: List[ShopifyImage] = Field(default_factory=list)
    image: Optional[ShopifyImage] = None

class ShopifyProductUpdate(BaseModel):
    """Update Shopify product request"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    body_html: Optional[str] = None
    vendor: Optional[str] = Field(None, max_length=255)
    product_type: Optional[str] = Field(None, max_length=255)
    handle: Optional[str] = Field(None, max_length=255)
    status: Optional[ShopifyProductStatus] = None
    published_scope: Optional[str] = None
    tags: Optional[str] = None
    seo_title: Optional[str] = Field(None, max_length=70)
    seo_description: Optional[str] = Field(None, max_length=320)

# Collection Models
class ShopifyCollectionType(str, Enum):
    SMART = "smart"
    CUSTOM = "custom"

class ShopifyCollectionRule(BaseModel):
    """Smart collection rule"""
    column: str = Field(..., description="Product attribute to filter on")
    relation: str = Field(..., description="Comparison operator")
    condition: str = Field(..., description="Value to compare against")

class ShopifyCollection(BaseModel):
    """Shopify collection"""
    id: int
    handle: str
    title: str
    updated_at: datetime
    body_html: Optional[str] = None
    published_at: Optional[datetime] = None
    sort_order: str = "best-selling"
    template_suffix: Optional[str] = None
    published_scope: str = "web"
    admin_graphql_api_id: Optional[str] = None
    image: Optional[Dict[str, Any]] = None

class ShopifySmartCollection(ShopifyCollection):
    """Smart collection with rules"""
    rules: List[ShopifyCollectionRule] = Field(default_factory=list)
    disjunctive: bool = False

class ShopifyCustomCollection(ShopifyCollection):
    """Custom collection"""
    products_count: int = 0

class ShopifyCollectionCreate(BaseModel):
    """Create collection request"""
    title: str = Field(..., min_length=1, max_length=255)
    body_html: Optional[str] = None
    handle: Optional[str] = Field(None, max_length=255)
    image: Optional[Dict[str, Any]] = None
    published: bool = True
    published_scope: str = "web"
    sort_order: str = "best-selling"
    template_suffix: Optional[str] = None
    # Smart collection specific
    rules: Optional[List[ShopifyCollectionRule]] = None
    disjunctive: Optional[bool] = False

# Order Models
class ShopifyOrderStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class ShopifyFulfillmentStatus(str, Enum):
    FULFILLED = "fulfilled"
    PARTIAL = "partial"
    RESTOCKED = "restocked"
    NULL = "null"

class ShopifyFinancialStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    REFUNDED = "refunded"
    VOIDED = "voided"

class ShopifyAddress(BaseModel):
    """Address model"""
    first_name: Optional[str] = None
    address1: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    last_name: Optional[str] = None
    address2: Optional[str] = None
    company: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    name: Optional[str] = None
    country_code: Optional[str] = None
    province_code: Optional[str] = None

class ShopifyCustomer(BaseModel):
    """Customer information"""
    id: int
    email: str
    accepts_marketing: bool = False
    created_at: datetime
    updated_at: datetime
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    orders_count: int = 0
    state: str = "disabled"
    total_spent: Decimal = Decimal('0')
    last_order_id: Optional[int] = None
    note: Optional[str] = None
    verified_email: bool = False
    multipass_identifier: Optional[str] = None
    tax_exempt: bool = False
    phone: Optional[str] = None
    tags: str = ""
    currency: str = "USD"
    addresses: List[ShopifyAddress] = Field(default_factory=list)
    default_address: Optional[ShopifyAddress] = None

class ShopifyLineItem(BaseModel):
    """Order line item"""
    id: int
    variant_id: Optional[int] = None
    title: str
    quantity: int
    sku: Optional[str] = None
    variant_title: Optional[str] = None
    vendor: Optional[str] = None
    fulfillment_service: str = "manual"
    product_id: Optional[int] = None
    requires_shipping: bool = True
    taxable: bool = True
    gift_card: bool = False
    name: str
    variant_inventory_management: Optional[str] = None
    properties: List[Dict[str, str]] = Field(default_factory=list)
    product_exists: bool = True
    fulfillable_quantity: int = 0
    grams: int = 0
    price: Decimal
    total_discount: Decimal = Decimal('0')
    fulfillment_status: Optional[str] = None
    price_set: Optional[Dict[str, Any]] = None
    total_discount_set: Optional[Dict[str, Any]] = None
    discount_allocations: List[Dict[str, Any]] = Field(default_factory=list)
    duties: List[Dict[str, Any]] = Field(default_factory=list)
    admin_graphql_api_id: Optional[str] = None
    tax_lines: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Custom fields for upload links and previews
    upload_url: Optional[str] = None
    preview_image_url: Optional[str] = None
    custom_design_data: Optional[Dict[str, Any]] = None

class ShopifyOrder(BaseModel):
    """Shopify order"""
    id: int
    admin_graphql_api_id: Optional[str] = None
    app_id: Optional[int] = None
    browser_ip: Optional[str] = None
    buyer_accepts_marketing: bool = False
    cancel_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cart_token: Optional[str] = None
    checkout_id: Optional[int] = None
    checkout_token: Optional[str] = None
    client_details: Optional[Dict[str, Any]] = None
    closed_at: Optional[datetime] = None
    confirmed: bool = True
    contact_email: Optional[str] = None
    created_at: datetime
    currency: str = "USD"
    current_subtotal_price: Decimal
    current_subtotal_price_set: Optional[Dict[str, Any]] = None
    current_total_discounts: Decimal = Decimal('0')
    current_total_discounts_set: Optional[Dict[str, Any]] = None
    current_total_duties_set: Optional[Dict[str, Any]] = None
    current_total_price: Decimal
    current_total_price_set: Optional[Dict[str, Any]] = None
    current_total_tax: Decimal = Decimal('0')
    current_total_tax_set: Optional[Dict[str, Any]] = None
    customer_locale: Optional[str] = None
    device_id: Optional[str] = None
    discount_codes: List[Dict[str, Any]] = Field(default_factory=list)
    email: str
    estimated_taxes: bool = False
    financial_status: ShopifyFinancialStatus = ShopifyFinancialStatus.PENDING
    fulfillment_status: Optional[ShopifyFulfillmentStatus] = None
    gateway: Optional[str] = None
    landing_site: Optional[str] = None
    landing_site_ref: Optional[str] = None
    location_id: Optional[int] = None
    name: str
    note: Optional[str] = None
    note_attributes: List[Dict[str, str]] = Field(default_factory=list)
    number: int
    order_number: int
    order_status_url: Optional[str] = None
    original_total_duties_set: Optional[Dict[str, Any]] = None
    payment_gateway_names: List[str] = Field(default_factory=list)
    phone: Optional[str] = None
    presentment_currency: str = "USD"
    processed_at: Optional[datetime] = None
    processing_method: Optional[str] = None
    reference: Optional[str] = None
    referring_site: Optional[str] = None
    source_identifier: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    subtotal_price: Decimal
    subtotal_price_set: Optional[Dict[str, Any]] = None
    tags: str = ""
    tax_lines: List[Dict[str, Any]] = Field(default_factory=list)
    taxes_included: bool = False
    test: bool = False
    token: str
    total_discounts: Decimal = Decimal('0')
    total_discounts_set: Optional[Dict[str, Any]] = None
    total_line_items_price: Decimal
    total_line_items_price_set: Optional[Dict[str, Any]] = None
    total_outstanding: Decimal = Decimal('0')
    total_price: Decimal
    total_price_set: Optional[Dict[str, Any]] = None
    total_price_usd: Optional[Decimal] = None
    total_shipping_price_set: Optional[Dict[str, Any]] = None
    total_tax: Decimal = Decimal('0')
    total_tax_set: Optional[Dict[str, Any]] = None
    total_tip_received: Decimal = Decimal('0')
    total_weight: int = 0
    updated_at: datetime
    user_id: Optional[int] = None
    billing_address: Optional[ShopifyAddress] = None
    customer: Optional[ShopifyCustomer] = None
    discount_applications: List[Dict[str, Any]] = Field(default_factory=list)
    fulfillments: List[Dict[str, Any]] = Field(default_factory=list)
    line_items: List[ShopifyLineItem] = Field(default_factory=list)
    payment_terms: Optional[Dict[str, Any]] = None
    refunds: List[Dict[str, Any]] = Field(default_factory=list)
    shipping_address: Optional[ShopifyAddress] = None
    shipping_lines: List[Dict[str, Any]] = Field(default_factory=list)

# Batch Operations
class ShopifyBatchOperation(BaseModel):
    """Batch operation request"""
    operation: str = Field(..., description="Operation: update, delete, publish, unpublish")
    product_ids: List[int] = Field(..., min_items=1, description="Product IDs to operate on")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Update data")

class ShopifyBatchResult(BaseModel):
    """Batch operation result"""
    successful: List[int] = Field(default_factory=list)
    failed: List[Dict[str, Any]] = Field(default_factory=list)
    total_requested: int = 0
    total_successful: int = 0
    total_failed: int = 0

# Dashboard Models
class ShopifyShopStats(BaseModel):
    """Shopify shop statistics"""
    total_products: int = 0
    published_products: int = 0
    draft_products: int = 0
    total_orders: int = 0
    total_customers: int = 0
    total_revenue: Decimal = Decimal('0')
    orders_this_month: int = 0
    revenue_this_month: Decimal = Decimal('0')
    average_order_value: Decimal = Decimal('0')
    total_collections: int = 0
    pending_orders: int = 0

class ShopifyDashboardData(BaseModel):
    """Complete dashboard data from Shopify"""
    shop_info: ShopifyShop
    shop_stats: ShopifyShopStats
    recent_orders: List[ShopifyOrder] = Field(default_factory=list)
    recent_products: List[ShopifyProduct] = Field(default_factory=list)
    pending_orders: List[ShopifyOrder] = Field(default_factory=list)
    low_stock_products: List[ShopifyProduct] = Field(default_factory=list)
    collections: List[ShopifyCollection] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

# Integration Models
class ShopifyIntegrationStatus(BaseModel):
    """Status of Shopify integration for a user"""
    user_id: UUID
    tenant_id: str
    is_connected: bool = False
    shop_domain: Optional[str] = None
    shop_name: Optional[str] = None
    last_sync: Optional[datetime] = None
    sync_status: str = "never_synced"
    error_message: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

class ShopifySyncRequest(BaseModel):
    """Request to sync data from Shopify"""
    sync_type: str = Field(..., description="Type of sync: orders, products, collections, customers, all")
    force_full_sync: bool = Field(False, description="Force full sync instead of incremental")
    date_range_start: Optional[datetime] = Field(None, description="Start date for sync")
    date_range_end: Optional[datetime] = Field(None, description="End date for sync")

class ShopifySyncResponse(BaseModel):
    """Response from sync operation"""
    sync_id: str
    status: str  # started, completed, error
    sync_type: str
    records_processed: int = 0
    records_updated: int = 0
    records_created: int = 0
    errors: List[str] = Field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None
    message: Optional[str] = None

# Order Preview Models
class OrderPreviewItem(BaseModel):
    """Order item with preview data"""
    line_item_id: int
    product_title: str
    variant_title: Optional[str] = None
    quantity: int
    upload_url: Optional[str] = None
    preview_image_url: Optional[str] = None
    custom_design_data: Optional[Dict[str, Any]] = None
    mockup_urls: List[str] = Field(default_factory=list)
    processing_status: str = "pending"  # pending, processing, completed, error

class OrderPreview(BaseModel):
    """Complete order preview with all items"""
    order_id: int
    order_name: str
    customer_email: str
    created_at: datetime
    items: List[OrderPreviewItem] = Field(default_factory=list)
    has_uploads: bool = False
    preview_ready: bool = False
    total_items_with_uploads: int = 0

# API Response Models
class ShopifyApiResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None

# Model configuration
for model_class in [ShopifyShop, ShopifyProduct, ShopifyOrder, ShopifyCustomer]:
    model_class.model_config = ConfigDict(from_attributes=True)