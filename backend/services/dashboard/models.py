from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class DashboardOverview(BaseModel):
    """Dashboard overview data"""
    # User info
    user_id: UUID
    tenant_id: str
    shop_name: Optional[str] = None
    
    # Summary stats
    total_orders: int = 0
    pending_orders: int = 0
    processing_orders: int = 0
    completed_orders: int = 0
    total_revenue: Decimal = Decimal('0')
    this_month_revenue: Decimal = Decimal('0')
    
    # Templates and listings
    total_templates: int = 0
    active_templates: int = 0
    total_listings: int = 0
    active_listings: int = 0
    
    # Recent activity
    recent_orders_count: int = 0
    recent_templates_count: int = 0
    
    # Etsy integration status
    etsy_connected: bool = False
    etsy_shop_name: Optional[str] = None
    etsy_last_sync: Optional[datetime] = None
    
    # Shopify integration status
    shopify_connected: bool = False
    shopify_shop_name: Optional[str] = None
    shopify_last_sync: Optional[datetime] = None
    
    # System status
    last_updated: datetime = Field(default_factory=datetime.now)

class DashboardMetrics(BaseModel):
    """Detailed dashboard metrics"""
    # Time period
    period_start: datetime
    period_end: datetime
    
    # Order metrics
    orders_by_status: Dict[str, int] = Field(default_factory=dict)
    orders_by_platform: Dict[str, int] = Field(default_factory=dict)
    revenue_by_month: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Template metrics
    templates_by_category: Dict[str, int] = Field(default_factory=dict)
    most_used_templates: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Etsy metrics (if connected)
    etsy_metrics: Optional[Dict[str, Any]] = None
    
    # Shopify metrics (if connected)
    shopify_metrics: Optional[Dict[str, Any]] = None
    
    # Performance metrics
    conversion_rate: float = 0.0
    average_order_value: Decimal = Decimal('0')
    customer_satisfaction: Optional[float] = None

class DashboardAlert(BaseModel):
    """Dashboard alert/notification"""
    id: str
    type: str = Field(..., description="alert, warning, info, success")
    title: str
    message: str
    action_url: Optional[str] = None
    action_text: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    is_read: bool = False
    priority: str = "normal"  # low, normal, high, urgent

class DashboardQuickAction(BaseModel):
    """Quick action button for dashboard"""
    id: str
    title: str
    description: str
    icon: str
    action_url: str
    category: str = "general"
    is_enabled: bool = True

class DashboardWidget(BaseModel):
    """Dashboard widget configuration"""
    id: str
    title: str
    type: str = Field(..., description="chart, table, metric, list")
    position: Dict[str, int] = Field(default_factory=dict)  # x, y, width, height
    config: Dict[str, Any] = Field(default_factory=dict)
    is_visible: bool = True
    refresh_interval: Optional[int] = None  # seconds

class CompleteDashboard(BaseModel):
    """Complete dashboard data"""
    overview: DashboardOverview
    metrics: DashboardMetrics
    alerts: List[DashboardAlert] = Field(default_factory=list)
    quick_actions: List[DashboardQuickAction] = Field(default_factory=list)
    widgets: List[DashboardWidget] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)