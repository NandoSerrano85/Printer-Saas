from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from .models import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderListResponse,
    OrderStatsResponse,
    OrderStatus,
    FulfillmentStatus,
    PaymentStatus,
    OrderPlatform,
    OrderStatusUpdateRequest,
    OrderBulkOperationRequest,
    OrderBulkOperationResponse,
    OrderNoteCreate,
    OrderNoteResponse,
    OrderFulfillmentCreate,
    OrderFulfillmentResponse
)
from .service import OrderService
from common.auth import ActiveUserDep
from common.database import get_database_manager, DatabaseManager
from common.exceptions import (
    OrderNotFound,
    OrderCreateError,
    OrderUpdateError,
    OrderDeleteError,
    ValidationError
)

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"]
)

def get_order_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> OrderService:
    """Dependency to get order service"""
    return OrderService(db_manager)

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Create a new order"""
    try:
        return order_service.create_order(order_data, current_user.get_uuid())
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except OrderCreateError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=OrderListResponse)
async def get_orders(
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service),
    skip: int = Query(0, ge=0, description="Number of orders to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of orders to return"),
    search: Optional[str] = Query(None, description="Search orders by number, customer name, or email"),
    status: Optional[OrderStatus] = Query(None, description="Filter by order status"),
    platform: Optional[OrderPlatform] = Query(None, description="Filter by platform"),
    start_date: Optional[datetime] = Query(None, description="Filter orders from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter orders to this date"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """Get all orders for the current user with filtering and pagination"""
    return order_service.get_orders(
        user_id=current_user.get_uuid(),
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        platform=platform,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/stats", response_model=OrderStatsResponse)
async def get_order_stats(
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Get order statistics for the current user"""
    return order_service.get_order_stats(current_user.get_uuid())

@router.post("/bulk", response_model=OrderBulkOperationResponse)
async def bulk_operation(
    bulk_request: OrderBulkOperationRequest,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Perform bulk operations on orders"""
    return order_service.bulk_operation(bulk_request, current_user.get_uuid())

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Get a specific order by ID"""
    try:
        return order_service.get_order(order_id, current_user.get_uuid())
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: UUID,
    order_data: OrderUpdate,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Update an order by ID"""
    try:
        return order_service.update_order(order_id, order_data, current_user.get_uuid())
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except OrderUpdateError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: UUID,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Delete an order by ID"""
    try:
        order_service.delete_order(order_id, current_user.get_uuid())
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OrderDeleteError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdateRequest,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Update order status"""
    try:
        return order_service.update_order_status(order_id, status_update, current_user.get_uuid())
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OrderUpdateError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/notes", response_model=OrderNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_order_note(
    order_id: UUID,
    note_data: OrderNoteCreate,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Add a note to an order"""
    try:
        return order_service.add_order_note(order_id, note_data, current_user.get_uuid())
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OrderUpdateError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{order_id}/fulfillments", response_model=OrderFulfillmentResponse, status_code=status.HTTP_201_CREATED)
async def create_fulfillment(
    order_id: UUID,
    fulfillment_data: OrderFulfillmentCreate,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Create a fulfillment for an order"""
    try:
        return order_service.create_fulfillment(order_id, fulfillment_data, current_user.get_uuid())
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except OrderUpdateError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{order_id}/notes", response_model=List[OrderNoteResponse])
async def get_order_notes(
    order_id: UUID,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service),
    include_customer_visible: bool = Query(True, description="Include customer visible notes"),
    include_internal: bool = Query(True, description="Include internal notes")
):
    """Get all notes for an order"""
    try:
        # This would be implemented in the service
        # For now, return empty list as placeholder
        return []
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{order_id}/fulfillments", response_model=List[OrderFulfillmentResponse])
async def get_order_fulfillments(
    order_id: UUID,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Get all fulfillments for an order"""
    try:
        # This would be implemented in the service
        # For now, return empty list as placeholder
        return []
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{order_id}/duplicate", response_model=OrderResponse)
async def duplicate_order(
    order_id: UUID,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Duplicate an order"""
    try:
        # This would be implemented in the service
        # For now, raise not implemented
        raise HTTPException(status_code=501, detail="Duplicate order not implemented yet")
    except OrderNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/import", response_model=OrderBulkOperationResponse)
async def import_orders(
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Import orders from external platforms"""
    try:
        # This would be implemented in the service
        # For now, raise not implemented
        raise HTTPException(status_code=501, detail="Import orders not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export/{format}")
async def export_orders(
    format: str,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service),
    order_ids: Optional[List[UUID]] = Query(None, description="Specific order IDs to export"),
    start_date: Optional[datetime] = Query(None, description="Export orders from this date"),
    end_date: Optional[datetime] = Query(None, description="Export orders to this date")
):
    """Export orders in various formats (CSV, JSON, Excel)"""
    try:
        # This would be implemented in the service
        # For now, raise not implemented
        raise HTTPException(status_code=501, detail="Export orders not implemented yet")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Etsy Integration Endpoints

@router.get("/etsy", response_model=List[OrderResponse])
async def get_etsy_orders(
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service),
    limit: int = Query(50, ge=1, le=100, description="Number of Etsy orders to return")
):
    """Get orders that originated from Etsy"""
    try:
        return order_service.get_etsy_orders(current_user.get_uuid(), limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/etsy/{etsy_receipt_id}/status", response_model=OrderResponse)
async def update_etsy_order_status(
    etsy_receipt_id: int,
    new_status: str,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Update order status based on Etsy receipt ID"""
    try:
        result = order_service.update_etsy_order_status(
            etsy_receipt_id=etsy_receipt_id,
            user_id=current_user.get_uuid(),
            new_status=new_status
        )
        
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"No order found for Etsy receipt {etsy_receipt_id}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/etsy/listing/{etsy_listing_id}", response_model=List[OrderResponse])
async def get_orders_for_etsy_listing(
    etsy_listing_id: int,
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Get orders that contain items from a specific Etsy listing"""
    try:
        return order_service.get_orders_for_etsy_listing(
            user_id=current_user.get_uuid(),
            etsy_listing_id=etsy_listing_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/etsy/sync-receipt", response_model=OrderResponse)
async def sync_order_from_etsy_receipt(
    etsy_receipt_data: Dict[str, Any],
    current_user: ActiveUserDep,
    order_service: OrderService = Depends(get_order_service)
):
    """Create or update order from Etsy receipt data"""
    try:
        return order_service.sync_order_from_etsy_receipt(
            user_id=current_user.get_uuid(),
            etsy_receipt_data=etsy_receipt_data
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))