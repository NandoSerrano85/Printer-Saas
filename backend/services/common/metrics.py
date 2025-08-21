from fastapi import APIRouter, Depends, Query
from sqlalchemy import text, func, and_
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os

from database.core import get_db
from database.entities.order import Order
from database.entities.template import EtsyProductTemplate
from common.auth import get_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def get_basic_metrics(
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get basic application metrics"""
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "tenant_id": tenant_id,
        "application": {
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development"),
            "uptime": "unknown"  # Would need startup time tracking
        }
    }
    
    try:
        # Database connection count - keeping raw SQL for system tables
        result = db.execute(text("""
            SELECT count(*) as active_connections 
            FROM pg_stat_activity 
            WHERE state = 'active'
        """)).fetchone()
        
        metrics["database"] = {
            "active_connections": result[0] if result else 0,
            "status": "connected"
        }
        
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        metrics["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    try:
        # Basic table counts for tenant using SQLAlchemy ORM
        
        # Count templates
        template_count = db.query(EtsyProductTemplate).filter(
            and_(
                EtsyProductTemplate.tenant_id == tenant_id,
                EtsyProductTemplate.is_deleted == False
            )
        ).count()
        
        # Count orders  
        order_count = db.query(Order).filter(
            and_(
                Order.tenant_id == tenant_id,
                Order.is_deleted == False
            )
        ).count()
        
        metrics["tenant_data"] = {
            "templates": template_count,
            "orders": order_count
        }
        
    except Exception as e:
        logger.error(f"Failed to get tenant metrics: {e}")
        metrics["tenant_data"] = {
            "error": str(e)
        }
    
    return metrics

@router.get("/prometheus")
async def prometheus_metrics(
    tenant_id: Optional[str] = Depends(get_tenant_context),
    db: Session = Depends(get_db)
) -> str:
    """Prometheus-formatted metrics endpoint"""
    
    metrics_lines = [
        "# HELP printer_saas_info Application information",
        "# TYPE printer_saas_info gauge",
        f'printer_saas_info{{version="1.0.0",environment="{os.getenv("ENVIRONMENT", "development")}"}} 1',
        ""
    ]
    
    try:
        # Database metrics - keeping raw SQL for system tables
        result = db.execute(text("""
            SELECT count(*) as active_connections 
            FROM pg_stat_activity 
            WHERE state = 'active'
        """)).fetchone()
        
        metrics_lines.extend([
            "# HELP database_active_connections Number of active database connections",
            "# TYPE database_active_connections gauge",
            f"database_active_connections {result[0] if result else 0}",
            ""
        ])
        
    except Exception as e:
        logger.error(f"Failed to get database metrics for Prometheus: {e}")
    
    if tenant_id:
        try:
            # Tenant-specific metrics using SQLAlchemy ORM
            
            template_count = db.query(EtsyProductTemplate).filter(
                and_(
                    EtsyProductTemplate.tenant_id == tenant_id,
                    EtsyProductTemplate.is_deleted == False
                )
            ).count()
            
            order_count = db.query(Order).filter(
                and_(
                    Order.tenant_id == tenant_id,
                    Order.is_deleted == False
                )
            ).count()
            
            metrics_lines.extend([
                "# HELP tenant_templates_total Total number of templates for tenant",
                "# TYPE tenant_templates_total gauge", 
                f'tenant_templates_total{{tenant_id="{tenant_id}"}} {template_count}',
                "",
                "# HELP tenant_orders_total Total number of orders for tenant",
                "# TYPE tenant_orders_total gauge",
                f'tenant_orders_total{{tenant_id="{tenant_id}"}} {order_count}',
                ""
            ])
            
        except Exception as e:
            logger.error(f"Failed to get tenant metrics for Prometheus: {e}")
    
    return "\n".join(metrics_lines)

@router.get("/performance")
async def performance_metrics(
    tenant_id: str = Depends(get_tenant_context),
    db: Session = Depends(get_db),
    hours: int = Query(24, ge=1, le=168, description="Hours to look back")
) -> Dict[str, Any]:
    """Get performance metrics for the specified time period"""
    
    start_time = datetime.now() - timedelta(hours=hours)
    
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "period_hours": hours,
        "start_time": start_time.isoformat(),
        "tenant_id": tenant_id
    }
    
    try:
        # Recent order activity using SQLAlchemy ORM with subqueries for aggregation
        order_query = db.query(Order).filter(
            and_(
                Order.tenant_id == tenant_id,
                Order.created_at >= start_time,
                Order.is_deleted == False
            )
        )
        
        total_orders = order_query.count()
        completed_orders = order_query.filter(Order.status == 'completed').count()
        
        # Use scalar subqueries for aggregate functions
        avg_order_value = db.query(func.avg(Order.total_amount)).filter(
            and_(
                Order.tenant_id == tenant_id,
                Order.created_at >= start_time,
                Order.is_deleted == False
            )
        ).scalar() or 0
        
        total_revenue = db.query(func.sum(Order.total_amount)).filter(
            and_(
                Order.tenant_id == tenant_id,
                Order.created_at >= start_time,
                Order.is_deleted == False
            )
        ).scalar() or 0
        
        metrics["orders"] = {
            "total": total_orders,
            "completed": completed_orders,
            "average_value": float(avg_order_value),
            "total_revenue": float(total_revenue)
        }
        
        # Template usage using SQLAlchemy ORM
        template_query = db.query(EtsyProductTemplate).filter(
            and_(
                EtsyProductTemplate.tenant_id == tenant_id,
                EtsyProductTemplate.created_at >= start_time,
                EtsyProductTemplate.is_deleted == False
            )
        )
        
        total_templates = template_query.count()
        active_templates = template_query.filter(EtsyProductTemplate.is_active == True).count()
        
        metrics["templates"] = {
            "total": total_templates,
            "active": active_templates
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        metrics["error"] = str(e)
    
    return metrics

@router.get("/status")
async def service_status() -> Dict[str, Any]:
    """Get service status information"""
    return {
        "service": "printer-saas-backend",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": {
            "templates": "enabled",
            "orders": "enabled", 
            "multi_tenant": "enabled",
            "authentication": "enabled"
        }
    }