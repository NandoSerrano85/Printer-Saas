from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from typing import List, Optional, Dict, Any, Union
from uuid import UUID
from datetime import datetime

from .models import (
    ShopifyOAuthInitRequest, ShopifyOAuthInitResponse, ShopifyOAuthCallbackRequest,
    ShopifyTokenResponse, ShopifyShop, ShopifyProduct, ShopifyProductCreate,
    ShopifyProductUpdate, ShopifyOrder, ShopifyCustomer, ShopifyCollection,
    ShopifyCollectionCreate, ShopifyBatchOperation, ShopifyBatchResult,
    OrderPreview, ShopifyDashboardData, ShopifyIntegrationStatus,
    ShopifySyncRequest, ShopifySyncResponse
)
from .service import ShopifyService
from common.auth import UserOrAdminDep
from common.database import get_database_manager, DatabaseManager
from common.exceptions import (
    UserNotFound, ShopifyAPIError, ShopifyAuthenticationError,
    ShopifyRateLimitError, ValidationError
)

router = APIRouter(
    prefix="/api/v1/shopify",
    tags=["Shopify Integration"]
)

def get_shopify_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> ShopifyService:
    """Dependency to get Shopify service"""
    return ShopifyService(db_manager)

# OAuth Endpoints

@router.post("/oauth/init", response_model=ShopifyOAuthInitResponse)
async def initiate_oauth_flow(
    oauth_request: ShopifyOAuthInitRequest,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Initiate Shopify OAuth flow"""
    try:
        return shopify_service.initiate_oauth_flow(oauth_request, current_user.get_uuid())
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/oauth/callback", response_model=ShopifyTokenResponse)
async def handle_oauth_callback(
    callback_data: ShopifyOAuthCallbackRequest,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Handle Shopify OAuth callback"""
    try:
        return shopify_service.handle_oauth_callback(callback_data, current_user.get_uuid())
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/oauth/disconnect")
async def disconnect_shopify(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Disconnect Shopify integration"""
    try:
        success = shopify_service.disconnect_shopify(current_user.get_uuid())
        return {"success": success, "message": "Shopify disconnected successfully" if success else "Failed to disconnect"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/integration/status", response_model=ShopifyIntegrationStatus)
async def get_integration_status(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Get Shopify integration status"""
    return shopify_service.get_integration_status(current_user.get_uuid())

@router.get("/test-connection")
async def test_connection(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Test Shopify connection"""
    try:
        is_connected = shopify_service.test_connection(current_user.get_uuid())
        return {
            "connected": is_connected,
            "message": "Connection successful" if is_connected else "Connection failed"
        }
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Shop Endpoints

@router.get("/shop", response_model=ShopifyShop)
async def get_shop_info(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Get shop information"""
    try:
        return shopify_service.get_shop_info(current_user.get_uuid())
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Product Endpoints

@router.get("/products", response_model=Dict[str, Any])
async def get_products(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service),
    limit: int = Query(50, ge=1, le=250, description="Number of products to retrieve"),
    page_info: Optional[str] = Query(None, description="Pagination cursor"),
    status: Optional[str] = Query(None, description="Product status filter"),
    product_type: Optional[str] = Query(None, description="Product type filter"),
    vendor: Optional[str] = Query(None, description="Vendor filter")
):
    """Get products with pagination and filtering"""
    try:
        return shopify_service.get_products(
            user_id=current_user.get_uuid(),
            limit=limit,
            page_info=page_info,
            status=status,
            product_type=product_type,
            vendor=vendor
        )
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{product_id}", response_model=ShopifyProduct)
async def get_product(
    product_id: int,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Get a specific product"""
    try:
        return shopify_service.get_product(current_user.get_uuid(), product_id)
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e))

@router.post("/products", response_model=ShopifyProduct)
async def create_product(
    product_data: ShopifyProductCreate,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Create a new product"""
    try:
        return shopify_service.create_product(current_user.get_uuid(), product_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/products/{product_id}", response_model=ShopifyProduct)
async def update_product(
    product_id: int,
    product_data: ShopifyProductUpdate,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Update an existing product"""
    try:
        return shopify_service.update_product(current_user.get_uuid(), product_id, product_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e))

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Delete a product"""
    try:
        success = shopify_service.delete_product(current_user.get_uuid(), product_id)
        return {"success": success, "message": "Product deleted successfully" if success else "Failed to delete product"}
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e))

@router.post("/products/batch", response_model=ShopifyBatchResult)
async def batch_update_products(
    batch_operation: ShopifyBatchOperation,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Perform batch operations on products"""
    try:
        return shopify_service.batch_update_products(current_user.get_uuid(), batch_operation)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyRateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Order Endpoints

@router.get("/orders", response_model=Dict[str, Any])
async def get_orders(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service),
    limit: int = Query(50, ge=1, le=250, description="Number of orders to retrieve"),
    page_info: Optional[str] = Query(None, description="Pagination cursor"),
    status: Optional[str] = Query(None, description="Order status filter"),
    financial_status: Optional[str] = Query(None, description="Financial status filter"),
    fulfillment_status: Optional[str] = Query(None, description="Fulfillment status filter"),
    created_at_min: Optional[datetime] = Query(None, description="Minimum creation date"),
    created_at_max: Optional[datetime] = Query(None, description="Maximum creation date")
):
    """Get orders with pagination and filtering"""
    try:
        return shopify_service.get_orders(
            user_id=current_user.get_uuid(),
            limit=limit,
            page_info=page_info,
            status=status,
            financial_status=financial_status,
            fulfillment_status=fulfillment_status,
            created_at_min=created_at_min,
            created_at_max=created_at_max
        )
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/orders/{order_id}", response_model=ShopifyOrder)
async def get_order(
    order_id: int,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Get a specific order"""
    try:
        return shopify_service.get_order(current_user.get_uuid(), order_id)
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e))

@router.get("/orders/{order_id}/preview", response_model=OrderPreview)
async def get_order_preview(
    order_id: int,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Get order preview with upload links and custom design data"""
    try:
        return shopify_service.get_order_preview(current_user.get_uuid(), order_id)
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e))

# Collection Endpoints

@router.get("/collections", response_model=List[ShopifyCollection])
async def get_collections(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service),
    collection_type: str = Query("all", description="Collection type: all, smart, custom")
):
    """Get collections"""
    try:
        return shopify_service.get_collections(current_user.get_uuid(), collection_type)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/collections", response_model=ShopifyCollection)
async def create_collection(
    collection_data: ShopifyCollectionCreate,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Create a new collection"""
    try:
        return shopify_service.create_collection(current_user.get_uuid(), collection_data)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Customer Endpoints

@router.get("/customers", response_model=Dict[str, Any])
async def get_customers(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service),
    limit: int = Query(50, ge=1, le=250, description="Number of customers to retrieve"),
    page_info: Optional[str] = Query(None, description="Pagination cursor")
):
    """Get customers with pagination"""
    try:
        return shopify_service.get_customers(current_user.get_uuid(), limit, page_info)
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/customers/{customer_id}", response_model=ShopifyCustomer)
async def get_customer(
    customer_id: int,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Get a specific customer"""
    try:
        return shopify_service.get_customer(current_user.get_uuid(), customer_id)
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=404 if "not found" in str(e).lower() else 500, detail=str(e))

# Sync Endpoints

@router.post("/sync", response_model=ShopifySyncResponse)
async def sync_data(
    sync_request: ShopifySyncRequest,
    background_tasks: BackgroundTasks,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Sync data from Shopify"""
    try:
        # For large syncs, run in background
        if sync_request.sync_type == 'all' or sync_request.force_full_sync:
            background_tasks.add_task(
                shopify_service.sync_data,
                current_user.get_uuid(),
                sync_request
            )
            return ShopifySyncResponse(
                sync_id="background",
                status="started",
                sync_type=sync_request.sync_type,
                started_at=datetime.now(),
                message="Large sync started in background"
            )
        else:
            return shopify_service.sync_data(current_user.get_uuid(), sync_request)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard Endpoints

@router.get("/dashboard", response_model=ShopifyDashboardData)
async def get_dashboard_data(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service)
):
    """Get dashboard data from Shopify"""
    try:
        return shopify_service.get_dashboard_data(current_user.get_uuid())
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Template Endpoints

@router.post("/templates/{template_id}/create-listing", response_model=ShopifyProduct)
async def create_listing_from_template(
    template_id: UUID,
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service),
    customizations: Optional[Dict[str, Any]] = None
):
    """Create Shopify product from template"""
    try:
        return shopify_service.create_listing_from_template(
            current_user.get_uuid(),
            template_id,
            customizations
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints

@router.get("/analytics/summary")
async def get_analytics_summary(
    current_user: UserOrAdminDep,
    shopify_service: ShopifyService = Depends(get_shopify_service),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get analytics summary"""
    try:
        dashboard_data = shopify_service.get_dashboard_data(current_user.get_uuid())
        
        return {
            "summary": {
                "total_products": dashboard_data.shop_stats.total_products,
                "total_orders": dashboard_data.shop_stats.total_orders,
                "total_revenue": float(dashboard_data.shop_stats.total_revenue),
                "pending_orders": dashboard_data.shop_stats.pending_orders,
                "average_order_value": float(dashboard_data.shop_stats.average_order_value)
            },
            "shop_info": {
                "name": dashboard_data.shop_info.name,
                "domain": dashboard_data.shop_info.domain,
                "currency": dashboard_data.shop_info.currency,
                "timezone": dashboard_data.shop_info.timezone
            },
            "alerts": {
                "low_stock_products": len(dashboard_data.low_stock_products),
                "pending_orders": len(dashboard_data.pending_orders)
            },
            "last_updated": dashboard_data.last_updated.isoformat()
        }
    except ShopifyAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except ShopifyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health Check

@router.get("/health")
async def shopify_health_check():
    """Shopify service health check"""
    return {
        "service": "shopify",
        "status": "healthy",
        "version": "1.0.0",
        "features": [
            "oauth_authentication",
            "product_management",
            "order_management",
            "collection_management",
            "customer_management",
            "batch_operations",
            "order_preview",
            "dashboard_integration",
            "template_integration",
            "data_synchronization"
        ]
    }