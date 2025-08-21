from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging

from .models import (
    DashboardOverview, DashboardMetrics, DashboardAlert,
    DashboardQuickAction, DashboardWidget, CompleteDashboard
)
from database.entities import User, Order, EtsyProductTemplate, ThirdPartyOAuthToken
from common.database import DatabaseManager
from common.exceptions import UserNotFound, DashboardDataError
from services.etsy.service import EtsyService
from services.order.service import OrderService
from services.template.service import TemplateService
from services.shopify.service import ShopifyService

logger = logging.getLogger(__name__)

class DashboardService:
    """Service for dashboard data aggregation and management"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.etsy_service = EtsyService(db_manager)
        self.shopify_service = ShopifyService(db_manager)
        self.order_service = OrderService(db_manager)
        self.template_service = TemplateService(db_manager)
    
    def get_dashboard_overview(self, user_id: UUID) -> DashboardOverview:
        """Get dashboard overview data"""
        try:
            # Validate user exists
            user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                raise UserNotFound(user_id)
            
            # Get order statistics
            order_stats = self._get_order_statistics(user_id)
            
            # Get template statistics
            template_stats = self._get_template_statistics(user_id)
            
            # Get Etsy integration status
            etsy_status = self.etsy_service.get_integration_status(user_id)
            etsy_shop_name = None
            etsy_last_sync = None
            
            if etsy_status.is_connected:
                try:
                    etsy_shop = self.etsy_service.get_shop_info(user_id)
                    etsy_shop_name = etsy_shop.shop_name
                    etsy_last_sync = etsy_status.last_sync
                except Exception as e:
                    logger.warning(f"Could not get Etsy shop info: {e}")
            
            # Get Shopify integration status
            shopify_status = self.shopify_service.get_integration_status(user_id)
            shopify_shop_name = None
            shopify_last_sync = None
            
            if shopify_status.is_connected:
                try:
                    shopify_shop = self.shopify_service.get_shop_info(user_id)
                    shopify_shop_name = shopify_shop.name
                    shopify_last_sync = shopify_status.last_sync
                except Exception as e:
                    logger.warning(f"Could not get Shopify shop info: {e}")
            
            return DashboardOverview(
                user_id=user_id,
                tenant_id=self.db.tenant_id,
                shop_name=user.shop_name,
                
                # Order stats
                total_orders=order_stats['total_orders'],
                pending_orders=order_stats['pending_orders'],
                processing_orders=order_stats['processing_orders'],
                completed_orders=order_stats['completed_orders'],
                total_revenue=order_stats['total_revenue'],
                this_month_revenue=order_stats['this_month_revenue'],
                
                # Template stats
                total_templates=template_stats['total_templates'],
                active_templates=template_stats['active_templates'],
                
                # Recent activity
                recent_orders_count=order_stats.get('recent_count', 0),
                recent_templates_count=template_stats.get('recent_count', 0),
                
                # Etsy integration
                etsy_connected=etsy_status.is_connected,
                etsy_shop_name=etsy_shop_name,
                etsy_last_sync=etsy_last_sync,
                
                # Shopify integration
                shopify_connected=shopify_status.is_connected,
                shopify_shop_name=shopify_shop_name,
                shopify_last_sync=shopify_last_sync,
                
                last_updated=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error getting dashboard overview for user {user_id}: {str(e)}")
            raise DashboardDataError(f"Failed to get dashboard overview: {str(e)}")
    
    def get_dashboard_metrics(self, user_id: UUID, days: int = 30) -> DashboardMetrics:
        """Get detailed dashboard metrics"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days)
            
            # Get order metrics
            orders_by_status = self._get_orders_by_status(user_id, start_date, end_date)
            orders_by_platform = self._get_orders_by_platform(user_id, start_date, end_date)
            revenue_by_month = self._get_revenue_by_month(user_id, start_date, end_date)
            
            # Get template metrics
            templates_by_category = self._get_templates_by_category(user_id)
            most_used_templates = self._get_most_used_templates(user_id)
            
            # Get Etsy metrics if connected
            etsy_metrics = None
            etsy_status = self.etsy_service.get_integration_status(user_id)
            if etsy_status.is_connected:
                try:
                    etsy_dashboard = self.etsy_service.get_dashboard_data(user_id)
                    etsy_metrics = {
                        'shop_views': etsy_dashboard.shop_stats.total_views,
                        'shop_favorites': etsy_dashboard.shop_stats.total_favorites,
                        'conversion_rate': etsy_dashboard.shop_stats.conversion_rate,
                        'shop_rating': etsy_dashboard.shop_stats.shop_rating,
                        'total_reviews': etsy_dashboard.shop_stats.total_reviews,
                        'low_stock_count': len(etsy_dashboard.low_stock_listings),
                        'pending_orders_count': len(etsy_dashboard.pending_orders)
                    }
                except Exception as e:
                    logger.warning(f"Could not get Etsy metrics: {e}")
            
            # Get Shopify metrics if connected
            shopify_metrics = None
            shopify_status = self.shopify_service.get_integration_status(user_id)
            if shopify_status.is_connected:
                try:
                    shopify_dashboard = self.shopify_service.get_dashboard_data(user_id)
                    shopify_metrics = {
                        'total_products': shopify_dashboard.shop_stats.total_products,
                        'total_orders': shopify_dashboard.shop_stats.total_orders,
                        'total_revenue': float(shopify_dashboard.shop_stats.total_revenue),
                        'average_order_value': float(shopify_dashboard.shop_stats.average_order_value),
                        'pending_orders_count': shopify_dashboard.shop_stats.pending_orders,
                        'low_stock_count': len(shopify_dashboard.low_stock_products),
                        'collections_count': shopify_dashboard.shop_stats.total_collections
                    }
                except Exception as e:
                    logger.warning(f"Could not get Shopify metrics: {e}")
            
            # Calculate performance metrics
            total_orders = sum(orders_by_status.values())
            total_revenue = sum(month['revenue'] for month in revenue_by_month)
            avg_order_value = Decimal(str(total_revenue / total_orders)) if total_orders > 0 else Decimal('0')
            
            return DashboardMetrics(
                period_start=start_date,
                period_end=end_date,
                orders_by_status=orders_by_status,
                orders_by_platform=orders_by_platform,
                revenue_by_month=revenue_by_month,
                templates_by_category=templates_by_category,
                most_used_templates=most_used_templates,
                etsy_metrics=etsy_metrics,
                shopify_metrics=shopify_metrics,
                average_order_value=avg_order_value,
                conversion_rate=etsy_metrics.get('conversion_rate', 0.0) if etsy_metrics else 0.0
            )
            
        except Exception as e:
            logger.error(f"Error getting dashboard metrics for user {user_id}: {str(e)}")
            raise DashboardDataError(f"Failed to get dashboard metrics: {str(e)}")
    
    def get_dashboard_alerts(self, user_id: UUID) -> List[DashboardAlert]:
        """Get dashboard alerts and notifications"""
        alerts = []
        
        try:
            # Check Etsy integration status
            etsy_status = self.etsy_service.get_integration_status(user_id)
            
            # Check Shopify integration status
            shopify_status = self.shopify_service.get_integration_status(user_id)
            if not etsy_status.is_connected:
                alerts.append(DashboardAlert(
                    id="etsy_not_connected",
                    type="warning",
                    title="Etsy Not Connected",
                    message="Connect your Etsy shop to sync orders and listings automatically.",
                    action_url="/etsy/connect",
                    action_text="Connect Etsy",
                    priority="high"
                ))
            elif etsy_status.error_message:
                alerts.append(DashboardAlert(
                    id="etsy_error",
                    type="alert",
                    title="Etsy Connection Issue",
                    message=f"There's an issue with your Etsy connection: {etsy_status.error_message}",
                    action_url="/etsy/reconnect",
                    action_text="Reconnect",
                    priority="high"
                ))
            
            # Check Shopify integration status
            if not shopify_status.is_connected:
                alerts.append(DashboardAlert(
                    id="shopify_not_connected",
                    type="info",
                    title="Shopify Not Connected",
                    message="Connect your Shopify store to sync products, orders, and collections automatically.",
                    action_url="/shopify/connect",
                    action_text="Connect Shopify",
                    priority="normal"
                ))
            elif shopify_status.error_message:
                alerts.append(DashboardAlert(
                    id="shopify_error",
                    type="alert",
                    title="Shopify Connection Issue",
                    message=f"There's an issue with your Shopify connection: {shopify_status.error_message}",
                    action_url="/shopify/reconnect",
                    action_text="Reconnect",
                    priority="high"
                ))
            
            # Check for recent orders
            recent_orders = self.order_service.get_orders(user_id, limit=5)
            pending_count = len([o for o in recent_orders.orders if o.status == 'pending'])
            
            if pending_count > 5:
                alerts.append(DashboardAlert(
                    id="pending_orders",
                    type="warning",
                    title="Pending Orders",
                    message=f"You have {pending_count} pending orders that need attention.",
                    action_url="/orders?status=pending",
                    action_text="View Orders",
                    priority="normal"
                ))
            
            # Check template count
            template_stats = self.template_service.get_template_stats(user_id)
            if template_stats.total_templates == 0:
                alerts.append(DashboardAlert(
                    id="no_templates",
                    type="info",
                    title="Create Your First Template",
                    message="Start by creating your first product template to streamline your listings.",
                    action_url="/templates/create",
                    action_text="Create Template",
                    priority="normal"
                ))
            
            # Check for Etsy-specific alerts
            if etsy_status.is_connected:
                try:
                    etsy_dashboard = self.etsy_service.get_dashboard_data(user_id)
                    
                    # Low stock alert
                    if len(etsy_dashboard.low_stock_listings) > 0:
                        alerts.append(DashboardAlert(
                            id="low_stock",
                            type="warning",
                            title="Low Stock Items",
                            message=f"{len(etsy_dashboard.low_stock_listings)} listings are running low on stock.",
                            action_url="/etsy/listings?filter=low_stock",
                            action_text="View Listings",
                            priority="normal"
                        ))
                    
                    # Vacation mode alert
                    if etsy_dashboard.shop_info.is_vacation:
                        alerts.append(DashboardAlert(
                            id="vacation_mode",
                            type="info",
                            title="Shop in Vacation Mode",
                            message="Your Etsy shop is currently in vacation mode.",
                            action_url="/etsy/shop/settings",
                            action_text="Manage Shop",
                            priority="low"
                        ))
                        
                except Exception as e:
                    logger.warning(f"Could not check Etsy alerts: {e}")
            
            # Check for Shopify-specific alerts
            if shopify_status.is_connected:
                try:
                    shopify_dashboard = self.shopify_service.get_dashboard_data(user_id)
                    
                    # Low stock alert
                    if len(shopify_dashboard.low_stock_products) > 0:
                        alerts.append(DashboardAlert(
                            id="shopify_low_stock",
                            type="warning",
                            title="Low Stock Products",
                            message=f"{len(shopify_dashboard.low_stock_products)} products are running low on stock.",
                            action_url="/shopify/products?filter=low_stock",
                            action_text="View Products",
                            priority="normal"
                        ))
                    
                    # Draft products alert
                    draft_count = shopify_dashboard.shop_stats.draft_products
                    if draft_count > 5:
                        alerts.append(DashboardAlert(
                            id="shopify_draft_products",
                            type="info",
                            title="Draft Products",
                            message=f"You have {draft_count} draft products that could be published.",
                            action_url="/shopify/products?status=draft",
                            action_text="Review Drafts",
                            priority="low"
                        ))
                        
                except Exception as e:
                    logger.warning(f"Could not check Shopify alerts: {e}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error getting dashboard alerts for user {user_id}: {str(e)}")
            return []
    
    def get_quick_actions(self, user_id: UUID) -> List[DashboardQuickAction]:
        """Get quick action buttons for dashboard"""
        actions = [
            DashboardQuickAction(
                id="create_template",
                title="Create Template",
                description="Create a new product template",
                icon="plus",
                action_url="/templates/create",
                category="templates"
            ),
            DashboardQuickAction(
                id="view_orders",
                title="View Orders",
                description="Manage your orders",
                icon="shopping-bag",
                action_url="/orders",
                category="orders"
            ),
            DashboardQuickAction(
                id="sync_etsy",
                title="Sync Etsy",
                description="Sync data from Etsy",
                icon="refresh",
                action_url="/etsy/sync",
                category="etsy"
            ),
            DashboardQuickAction(
                id="create_listing",
                title="Create Listing",
                description="Create a new Etsy listing",
                icon="external-link",
                action_url="/etsy/listings/create",
                category="etsy"
            ),
            DashboardQuickAction(
                id="sync_shopify",
                title="Sync Shopify",
                description="Sync data from Shopify",
                icon="refresh",
                action_url="/shopify/sync",
                category="shopify"
            ),
            DashboardQuickAction(
                id="create_shopify_product",
                title="Create Product",
                description="Create a new Shopify product",
                icon="package",
                action_url="/shopify/products/create",
                category="shopify"
            ),
            DashboardQuickAction(
                id="batch_edit_products",
                title="Batch Edit",
                description="Batch edit Shopify products",
                icon="edit",
                action_url="/shopify/products/batch",
                category="shopify"
            )
        ]
        
        # Enable/disable actions based on user status
        etsy_status = self.etsy_service.get_integration_status(user_id)
        shopify_status = self.shopify_service.get_integration_status(user_id)
        
        for action in actions:
            if action.category == "etsy":
                action.is_enabled = etsy_status.is_connected
            elif action.category == "shopify":
                action.is_enabled = shopify_status.is_connected
        
        return actions
    
    def get_complete_dashboard(self, user_id: UUID) -> CompleteDashboard:
        """Get complete dashboard data"""
        try:
            overview = self.get_dashboard_overview(user_id)
            metrics = self.get_dashboard_metrics(user_id)
            alerts = self.get_dashboard_alerts(user_id)
            quick_actions = self.get_quick_actions(user_id)
            
            # Default widgets
            widgets = [
                DashboardWidget(
                    id="revenue_chart",
                    title="Revenue Overview",
                    type="chart",
                    position={"x": 0, "y": 0, "width": 6, "height": 4},
                    config={"chart_type": "line", "data_source": "revenue_by_month"}
                ),
                DashboardWidget(
                    id="order_status",
                    title="Order Status",
                    type="metric",
                    position={"x": 6, "y": 0, "width": 3, "height": 2},
                    config={"metric": "orders_by_status"}
                ),
                DashboardWidget(
                    id="recent_orders",
                    title="Recent Orders",
                    type="table",
                    position={"x": 0, "y": 4, "width": 6, "height": 4},
                    config={"data_source": "recent_orders", "limit": 10}
                )
            ]
            
            return CompleteDashboard(
                overview=overview,
                metrics=metrics,
                alerts=alerts,
                quick_actions=quick_actions,
                widgets=widgets
            )
            
        except Exception as e:
            logger.error(f"Error getting complete dashboard for user {user_id}: {str(e)}")
            raise DashboardDataError(f"Failed to get dashboard data: {str(e)}")
    
    # Helper methods
    
    def _get_order_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """Get order statistics"""
        from sqlalchemy import func
        
        # Basic counts
        total_orders = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.is_deleted == False
        ).count()
        
        pending_orders = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status == 'pending',
            Order.is_deleted == False
        ).count()
        
        processing_orders = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status == 'processing',
            Order.is_deleted == False
        ).count()
        
        completed_orders = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status.in_(['completed', 'delivered']),
            Order.is_deleted == False
        ).count()
        
        # Revenue calculation
        total_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            Order.user_id == user_id,
            Order.status.in_(['completed', 'delivered']),
            Order.is_deleted == False
        ).scalar() or Decimal('0')
        
        # This month revenue
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_revenue = self.db.query(func.sum(Order.total_amount)).filter(
            Order.user_id == user_id,
            Order.status.in_(['completed', 'delivered']),
            Order.created_at >= month_start,
            Order.is_deleted == False
        ).scalar() or Decimal('0')
        
        # Recent orders count
        week_ago = datetime.now() - timedelta(days=7)
        recent_count = self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.created_at >= week_ago,
            Order.is_deleted == False
        ).count()
        
        return {
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'processing_orders': processing_orders,
            'completed_orders': completed_orders,
            'total_revenue': total_revenue,
            'this_month_revenue': this_month_revenue,
            'recent_count': recent_count
        }
    
    def _get_template_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """Get template statistics"""
        total_templates = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.is_deleted == False
        ).count()
        
        active_templates = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.is_active == True,
            EtsyProductTemplate.is_deleted == False
        ).count()
        
        # Recent templates count
        week_ago = datetime.now() - timedelta(days=7)
        recent_count = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.created_at >= week_ago,
            EtsyProductTemplate.is_deleted == False
        ).count()
        
        return {
            'total_templates': total_templates,
            'active_templates': active_templates,
            'recent_count': recent_count
        }
    
    def _get_orders_by_status(self, user_id: UUID, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Get order counts by status"""
        from sqlalchemy import func
        
        result = self.db.query(
            Order.status,
            func.count(Order.id).label('count')
        ).filter(
            Order.user_id == user_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.is_deleted == False
        ).group_by(Order.status).all()
        
        return {row.status: row.count for row in result}
    
    def _get_orders_by_platform(self, user_id: UUID, start_date: datetime, end_date: datetime) -> Dict[str, int]:
        """Get order counts by platform"""
        from sqlalchemy import func
        
        result = self.db.query(
            Order.platform,
            func.count(Order.id).label('count')
        ).filter(
            Order.user_id == user_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.is_deleted == False
        ).group_by(Order.platform).all()
        
        return {row.platform: row.count for row in result}
    
    def _get_revenue_by_month(self, user_id: UUID, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get revenue by month"""
        from sqlalchemy import func, extract
        
        result = self.db.query(
            extract('year', Order.created_at).label('year'),
            extract('month', Order.created_at).label('month'),
            func.sum(Order.total_amount).label('revenue'),
            func.count(Order.id).label('orders')
        ).filter(
            Order.user_id == user_id,
            Order.created_at >= start_date,
            Order.created_at <= end_date,
            Order.status.in_(['completed', 'delivered']),
            Order.is_deleted == False
        ).group_by(
            extract('year', Order.created_at),
            extract('month', Order.created_at)
        ).order_by(
            extract('year', Order.created_at),
            extract('month', Order.created_at)
        ).all()
        
        return [
            {
                'year': int(row.year),
                'month': int(row.month),
                'revenue': float(row.revenue or 0),
                'orders': row.orders
            }
            for row in result
        ]
    
    def _get_templates_by_category(self, user_id: UUID) -> Dict[str, int]:
        """Get template counts by category"""
        from sqlalchemy import func
        
        result = self.db.query(
            EtsyProductTemplate.category,
            func.count(EtsyProductTemplate.id).label('count')
        ).filter(
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.is_deleted == False
        ).group_by(EtsyProductTemplate.category).all()
        
        return {(row.category or 'Uncategorized'): row.count for row in result}
    
    def _get_most_used_templates(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get most used templates"""
        templates = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.is_deleted == False
        ).order_by(EtsyProductTemplate.priority.desc()).limit(5).all()
        
        return [
            {
                'id': str(template.id),
                'name': template.name,
                'category': template.category,
                'priority': template.priority,
                'created_at': template.created_at.isoformat()
            }
            for template in templates
        ]