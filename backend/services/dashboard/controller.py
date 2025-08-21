from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from uuid import UUID

from .models import (
    DashboardOverview, DashboardMetrics, DashboardAlert,
    DashboardQuickAction, CompleteDashboard
)
from .service import DashboardService
from common.auth import UserOrAdminDep
from common.database import get_database_manager, DatabaseManager
from common.exceptions import UserNotFound, DashboardDataError

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["Dashboard"]
)

def get_dashboard_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> DashboardService:
    """Dependency to get dashboard service"""
    return DashboardService(db_manager)

@router.get("/", response_model=CompleteDashboard)
async def get_complete_dashboard(
    current_user: UserOrAdminDep,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get complete dashboard data"""
    try:
        return dashboard_service.get_complete_dashboard(current_user.get_uuid())
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DashboardDataError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/overview", response_model=DashboardOverview)
async def get_dashboard_overview(
    current_user: UserOrAdminDep,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get dashboard overview data"""
    try:
        return dashboard_service.get_dashboard_overview(current_user.get_uuid())
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DashboardDataError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: UserOrAdminDep,
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get detailed dashboard metrics"""
    try:
        return dashboard_service.get_dashboard_metrics(current_user.get_uuid(), days=days)
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DashboardDataError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts", response_model=List[DashboardAlert])
async def get_dashboard_alerts(
    current_user: UserOrAdminDep,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get dashboard alerts and notifications"""
    try:
        return dashboard_service.get_dashboard_alerts(current_user.get_uuid())
    except Exception as e:
        # Don't fail the request if alerts can't be loaded
        return []

@router.get("/quick-actions", response_model=List[DashboardQuickAction])
async def get_quick_actions(
    current_user: UserOrAdminDep,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get quick action buttons for dashboard"""
    try:
        return dashboard_service.get_quick_actions(current_user.get_uuid())
    except Exception as e:
        # Don't fail the request if quick actions can't be loaded
        return []

@router.get("/summary", response_model=dict)
async def get_dashboard_summary(
    current_user: UserOrAdminDep,
    dashboard_service: DashboardService = Depends(get_dashboard_service)
):
    """Get simplified dashboard summary for API clients"""
    try:
        overview = dashboard_service.get_dashboard_overview(current_user.get_uuid())
        
        return {
            "user_id": str(overview.user_id),
            "shop_name": overview.shop_name,
            "stats": {
                "total_orders": overview.total_orders,
                "pending_orders": overview.pending_orders,
                "total_revenue": float(overview.total_revenue),
                "this_month_revenue": float(overview.this_month_revenue),
                "total_templates": overview.total_templates,
                "active_templates": overview.active_templates
            },
            "etsy": {
                "connected": overview.etsy_connected,
                "shop_name": overview.etsy_shop_name,
                "last_sync": overview.etsy_last_sync.isoformat() if overview.etsy_last_sync else None
            },
            "shopify": {
                "connected": overview.shopify_connected,
                "shop_name": overview.shopify_shop_name,
                "last_sync": overview.shopify_last_sync.isoformat() if overview.shopify_last_sync else None
            },
            "last_updated": overview.last_updated.isoformat()
        }
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DashboardDataError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics", response_model=dict)
async def get_dashboard_analytics(
    current_user: UserOrAdminDep,
    dashboard_service: DashboardService = Depends(get_dashboard_service),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get dashboard analytics data for new tenants"""
    try:
        # For new tenants without data, return empty analytics
        return {
            "revenue": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "data": [0, 0, 0, 0, 0, 0]  # Placeholder data for new tenants
            },
            "orders": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"], 
                "data": [0, 0, 0, 0, 0, 0]  # Placeholder data for new tenants
            },
            "top_products": []  # Placeholder data for new tenants
        }
    except Exception as e:
        # Return empty analytics data for any errors
        return {
            "revenue": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "data": [0, 0, 0, 0, 0, 0]
            },
            "orders": {
                "labels": ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
                "data": [0, 0, 0, 0, 0, 0]
            },
            "top_products": []
        }