from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from enum import Enum

# Etsy API Configuration
class EtsyAPIConfig(BaseModel):
    """Etsy API configuration constants"""
    base_url: str = "https://openapi.etsy.com/v3"
    ping_url: str = "https://api.etsy.com/v3/application/openapi-ping"
    token_url: str = "https://api.etsy.com/v3/public/oauth/token"
    oauth_connect_url: str = "https://www.etsy.com/oauth/connect"
    scopes: str = "listings_w listings_r shops_r shops_w transactions_r"
    code_challenge_method: str = "S256"
    response_type: str = "code"

# OAuth Models
class EtsyOAuthInitRequest(BaseModel):
    """Request to initiate Etsy OAuth flow"""
    redirect_uri: str = Field(..., description="OAuth callback URI")

class EtsyOAuthInitResponse(BaseModel):
    """Response with OAuth flow data"""
    oauth_connect_url: str
    client_id: str
    redirect_uri: str
    scopes: str
    state: str
    code_challenge: str
    code_challenge_method: str
    response_type: str

class EtsyOAuthCallbackRequest(BaseModel):
    """OAuth callback data from Etsy"""
    code: str = Field(..., description="Authorization code from Etsy")
    state: str = Field(..., description="State parameter for CSRF protection")
    code_verifier: str = Field(..., description="PKCE code verifier")

class EtsyTokenResponse(BaseModel):
    """Etsy token response"""
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: int
    token_type: str = "Bearer"
    expires_at: datetime

# Etsy Shop Models
class EtsyShop(BaseModel):
    """Etsy shop information"""
    shop_id: int
    shop_name: str
    title: Optional[str] = None
    announcement: Optional[str] = None
    currency_code: str = "USD"
    is_vacation: bool = False
    vacation_message: Optional[str] = None
    sale_message: Optional[str] = None
    digital_sale_message: Optional[str] = None
    listing_active_count: int = 0
    digital_listing_count: int = 0
    login_name: str
    accepts_custom_requests: bool = False
    policy_welcome: Optional[str] = None
    policy_payment: Optional[str] = None
    policy_shipping: Optional[str] = None
    policy_refunds: Optional[str] = None
    policy_additional: Optional[str] = None
    policy_seller_info: Optional[str] = None
    policy_updated_tsz: Optional[datetime] = None
    vacation_autoreply: Optional[str] = None
    url: Optional[str] = None
    image_url_760x100: Optional[str] = None
    num_favorers: int = 0
    languages: List[str] = Field(default_factory=list)
    upcoming_local_event_id: Optional[int] = None
    icon_url_fullxfull: Optional[str] = None
    is_using_structured_policies: bool = False
    has_onboarded_structured_policies: bool = False
    include_dispute_form_link: bool = False
    is_direct_checkout_onboarded: bool = False
    is_calculated_eligible: bool = False
    is_opted_in_to_buyer_promise: bool = False
    is_shop_us_based: bool = False
    transaction_sold_count: int = 0
    shipping_from_country_iso: Optional[str] = None
    shop_location_country_iso: Optional[str] = None
    review_count: int = 0
    review_average: Optional[float] = None

class EtsyUser(BaseModel):
    """Etsy user information"""
    user_id: int
    primary_email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    gender: Optional[str] = None
    birth_month: Optional[str] = None
    birth_day: Optional[str] = None
    birth_year: Optional[str] = None
    join_tsz: Optional[datetime] = None
    materials: List[str] = Field(default_factory=list)
    country_id: Optional[int] = None
    region: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    avatar_id: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    transaction_buy_count: int = 0
    transaction_sold_count: int = 0
    is_seller: bool = False
    image_url_75x75: Optional[str] = None
    first_name_real: Optional[str] = None
    last_name_real: Optional[str] = None

# Taxonomy Models
class EtsyTaxonomy(BaseModel):
    """Etsy taxonomy node"""
    id: int
    level: int
    name: str
    parent_id: Optional[int] = None
    children: List["EtsyTaxonomy"] = Field(default_factory=list)
    full_path_taxonomy_ids: List[int] = Field(default_factory=list)

class EtsyTaxonomyFlat(BaseModel):
    """Flattened taxonomy for easier use"""
    id: int
    name: str
    level: int
    full_path: str
    parent_id: Optional[int] = None

# Shipping Models
class EtsyShippingProfile(BaseModel):
    """Etsy shipping profile"""
    shipping_profile_id: int
    title: str
    user_id: int
    min_processing_days: int
    max_processing_days: int
    processing_days_display_label: str
    origin_country_iso: str
    is_deleted: bool = False
    shipping_profile_destinations: List[Dict[str, Any]] = Field(default_factory=list)
    shipping_profile_upgrades: List[Dict[str, Any]] = Field(default_factory=list)
    origin_postal_code: Optional[str] = None
    profile_type: str = "manual"
    domestic_handling_fee: Optional[Decimal] = None
    international_handling_fee: Optional[Decimal] = None

class EtsyShopSection(BaseModel):
    """Etsy shop section"""
    shop_section_id: int
    title: str
    rank: int
    user_id: int
    active_listing_count: int = 0

# Listing Models
class EtsyListingState(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SOLD_OUT = "sold_out"
    DRAFT = "draft"
    EXPIRED = "expired"

class EtsyWhoMade(str, Enum):
    I_DID = "i_did"
    SOMEONE_ELSE = "someone_else"
    COLLECTIVE = "collective"

class EtsyWhenMade(str, Enum):
    MADE_TO_ORDER = "made_to_order"
    YEAR_2020_2023 = "2020_2023"
    YEAR_2010_2019 = "2010_2019"
    YEAR_2004_2009 = "2004_2009"
    BEFORE_2004 = "before_2004"
    YEAR_2000_2003 = "2000_2003"
    YEAR_1990_1999 = "1990_1999"
    YEAR_1980_1989 = "1980_1989"
    YEAR_1970_1979 = "1970_1979"
    YEAR_1960_1969 = "1960_1969"
    YEAR_1950_1959 = "1950_1959"
    YEAR_1940_1949 = "1940_1949"
    VINTAGE = "vintage"

class EtsyListingType(str, Enum):
    PHYSICAL = "physical"
    DOWNLOAD = "download"
    BOTH = "both"

class EtsyListingCreate(BaseModel):
    """Create Etsy listing request"""
    quantity: int = Field(..., ge=1, description="Quantity available")
    title: str = Field(..., min_length=1, max_length=140, description="Listing title")
    description: str = Field(..., min_length=1, description="Listing description")
    price: Decimal = Field(..., gt=0, description="Listing price")
    who_made: EtsyWhoMade = Field(..., description="Who made this item")
    when_made: EtsyWhenMade = Field(..., description="When was this item made")
    taxonomy_id: int = Field(..., description="Etsy taxonomy category ID")
    shipping_profile_id: Optional[int] = Field(None, description="Shipping profile ID")
    return_policy_id: Optional[int] = Field(None, description="Return policy ID")
    materials: Optional[List[str]] = Field(None, max_items=13, description="Materials used")
    shop_section_id: Optional[int] = Field(None, description="Shop section ID")
    processing_min: Optional[int] = Field(None, ge=1, le=30, description="Min processing time")
    processing_max: Optional[int] = Field(None, ge=1, le=30, description="Max processing time")
    tags: Optional[List[str]] = Field(None, max_items=13, description="Listing tags")
    styles: Optional[List[str]] = Field(None, max_items=2, description="Style tags")
    item_weight: Optional[float] = Field(None, ge=0, description="Item weight")
    item_length: Optional[float] = Field(None, ge=0, description="Item length")
    item_width: Optional[float] = Field(None, ge=0, description="Item width")
    item_height: Optional[float] = Field(None, ge=0, description="Item height")
    item_dimensions_unit: Optional[str] = Field(None, description="Dimensions unit")
    is_personalizable: bool = Field(False, description="Is item personalizable")
    personalization_is_required: bool = Field(False, description="Is personalization required")
    personalization_char_count_max: Optional[int] = Field(None, description="Max personalization chars")
    personalization_instructions: Optional[str] = Field(None, description="Personalization instructions")
    production_partner_ids: Optional[List[int]] = Field(None, description="Production partner IDs")
    image_ids: Optional[List[int]] = Field(None, max_items=10, description="Image IDs")
    is_supply: bool = Field(False, description="Is this a supply/tool")
    is_customizable: bool = Field(False, description="Is item customizable")
    should_auto_renew: bool = Field(False, description="Auto-renew when sold out")
    is_taxable: bool = Field(True, description="Is item taxable")
    type: EtsyListingType = Field(EtsyListingType.PHYSICAL, description="Listing type")

class EtsyListing(BaseModel):
    """Etsy listing response"""
    listing_id: int
    user_id: int
    shop_id: int
    title: str
    description: str
    state: EtsyListingState
    creation_timestamp: datetime
    created_timestamp: datetime
    ending_timestamp: datetime
    original_creation_timestamp: datetime
    last_modified_timestamp: datetime
    updated_timestamp: datetime
    state_timestamp: datetime
    quantity: int
    shop_section_id: Optional[int] = None
    featured_rank: Optional[int] = None
    url: str
    num_favorers: int = 0
    non_taxable: bool = False
    is_taxable: bool = True
    is_customizable: bool = False
    is_personalizable: bool = False
    personalization_is_required: bool = False
    personalization_char_count_max: Optional[int] = None
    personalization_instructions: Optional[str] = None
    listing_type: str = "physical"
    tags: List[str] = Field(default_factory=list)
    materials: List[str] = Field(default_factory=list)
    shop_section_id: Optional[int] = None
    processing_min: Optional[int] = None
    processing_max: Optional[int] = None
    who_made: Optional[str] = None
    when_made: Optional[str] = None
    is_supply: bool = False
    item_weight: Optional[float] = None
    item_weight_unit: Optional[str] = None
    item_length: Optional[float] = None
    item_width: Optional[float] = None
    item_height: Optional[float] = None
    item_dimensions_unit: Optional[str] = None
    is_private: bool = False
    style: List[str] = Field(default_factory=list)
    file_data: str = ""
    has_variations: bool = False
    should_auto_renew: bool = False
    language: Optional[str] = None
    price: Optional[Dict[str, Any]] = None
    taxonomy_id: Optional[int] = None
    shipping_profile_id: Optional[int] = None
    return_policy_id: Optional[int] = None
    production_partner_ids: List[int] = Field(default_factory=list)
    skus: List[str] = Field(default_factory=list)

# Order Models
class EtsyOrderStatus(str, Enum):
    PAID = "paid"
    COMPLETED = "completed"
    OPEN = "open"
    PAYMENT_PROCESSING = "payment processing"
    CANCELED = "canceled"

class EtsyReceipt(BaseModel):
    """Etsy receipt (order) information"""
    receipt_id: int
    receipt_type: int
    order_id: int
    seller_user_id: int
    buyer_user_id: int
    creation_timestamp: datetime
    can_refund: bool
    last_modified_timestamp: datetime
    name: str
    first_line: str
    second_line: Optional[str] = None
    city: str
    state: Optional[str] = None
    zip: str
    formatted_address: str
    country_iso: str
    payment_method: str
    payment_email: str
    message_from_seller: Optional[str] = None
    message_from_buyer: Optional[str] = None
    message_from_payment: Optional[str] = None
    is_paid: bool
    is_shipped: bool
    is_gift: bool
    needs_gift_wrap: bool
    gift_message: Optional[str] = None
    gift_wrap_price: Optional[Dict[str, Any]] = None
    discount_amt: Optional[Dict[str, Any]] = None
    subtotal: Optional[Dict[str, Any]] = None
    total_price: Optional[Dict[str, Any]] = None
    total_shipping_cost: Optional[Dict[str, Any]] = None
    total_tax_cost: Optional[Dict[str, Any]] = None
    total_vat_cost: Optional[Dict[str, Any]] = None
    grandtotal: Optional[Dict[str, Any]] = None
    adjusted_grandtotal: Optional[Dict[str, Any]] = None
    buyer_adjusted_grandtotal: Optional[Dict[str, Any]] = None
    shipments: List[Dict[str, Any]] = Field(default_factory=list)
    transactions: List[Dict[str, Any]] = Field(default_factory=list)

class EtsyTransaction(BaseModel):
    """Etsy transaction (order item)"""
    transaction_id: int
    title: str
    description: str
    seller_user_id: int
    buyer_user_id: int
    creation_timestamp: datetime
    paid_timestamp: Optional[datetime] = None
    shipped_timestamp: Optional[datetime] = None
    price: Optional[Dict[str, Any]] = None
    currency_code: str = "USD"
    quantity: int
    tags: List[str] = Field(default_factory=list)
    materials: List[str] = Field(default_factory=list)
    image_listing_id: Optional[int] = None
    receipt_id: int
    shipping_cost: Optional[Dict[str, Any]] = None
    variations: List[Dict[str, Any]] = Field(default_factory=list)
    product_data: List[Dict[str, Any]] = Field(default_factory=list)
    digital_download_url: Optional[str] = None
    listing_id: int
    sku: Optional[str] = None
    product_id: Optional[int] = None
    personalization: Optional[str] = None

# Dashboard Models
class EtsyShopStats(BaseModel):
    """Etsy shop statistics for dashboard"""
    total_listings: int = 0
    active_listings: int = 0
    sold_listings: int = 0
    draft_listings: int = 0
    total_views: int = 0
    total_favorites: int = 0
    total_orders: int = 0
    total_revenue: Decimal = Decimal('0')
    orders_this_month: int = 0
    revenue_this_month: Decimal = Decimal('0')
    average_order_value: Decimal = Decimal('0')
    conversion_rate: float = 0.0
    shop_rating: Optional[float] = None
    total_reviews: int = 0

class EtsyDashboardData(BaseModel):
    """Complete dashboard data from Etsy"""
    shop_info: EtsyShop
    user_info: EtsyUser
    shop_stats: EtsyShopStats
    recent_orders: List[EtsyReceipt] = Field(default_factory=list)
    recent_listings: List[EtsyListing] = Field(default_factory=list)
    pending_orders: List[EtsyReceipt] = Field(default_factory=list)
    low_stock_listings: List[EtsyListing] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)

# API Response Models
class EtsyListResponse(BaseModel):
    """Generic list response from Etsy API"""
    count: int
    results: List[Dict[str, Any]]
    pagination: Optional[Dict[str, Any]] = None

class EtsyApiResponse(BaseModel):
    """Generic API response wrapper"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    message: Optional[str] = None

# Integration Models
class EtsyIntegrationStatus(BaseModel):
    """Status of Etsy integration for a user"""
    user_id: UUID
    tenant_id: str
    is_connected: bool = False
    shop_id: Optional[int] = None
    shop_name: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    sync_status: str = "never_synced"  # never_synced, syncing, completed, error
    error_message: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

class EtsySyncRequest(BaseModel):
    """Request to sync data from Etsy"""
    sync_type: str = Field(..., description="Type of sync: orders, listings, shop, all")
    force_full_sync: bool = Field(False, description="Force full sync instead of incremental")
    date_range_start: Optional[datetime] = Field(None, description="Start date for sync")
    date_range_end: Optional[datetime] = Field(None, description="End date for sync")

class EtsySyncResponse(BaseModel):
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

# Error Models
class EtsyErrorResponse(BaseModel):
    """Etsy API error response"""
    error: str
    error_msg: str
    http_status: int

# Validation
EtsyTaxonomy.model_rebuild()

# Model configuration
for model_class in [EtsyShop, EtsyUser, EtsyListing, EtsyReceipt, EtsyTransaction]:
    model_class.model_config = ConfigDict(from_attributes=True)