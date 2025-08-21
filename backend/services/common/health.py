from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
import asyncio
import os
import logging
from datetime import datetime
from typing import Dict, Any

from database.core import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check endpoint"""
    checks = {}
    overall_status = "healthy"
    
    # Check database connectivity
    try:
        db = next(get_db())
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
        db.close()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = f"unhealthy: {str(e)}"
        overall_status = "unhealthy"
    
    # Check Redis connectivity (if configured)
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            import redis
            r = redis.Redis.from_url(redis_url)
            r.ping()
            checks["redis"] = "healthy"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            checks["redis"] = f"unhealthy: {str(e)}"
            overall_status = "unhealthy"
    else:
        checks["redis"] = "not_configured"
    
    # Check disk space
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_percent = (free / total) * 100
        if free_percent < 10:  # Less than 10% free space
            checks["disk"] = f"warning: only {free_percent:.1f}% free"
            if free_percent < 5:
                overall_status = "unhealthy"
        else:
            checks["disk"] = "healthy"
    except Exception as e:
        logger.error(f"Disk health check failed: {e}")
        checks["disk"] = f"error: {str(e)}"
    
    # Check memory usage
    try:
        import psutil
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            checks["memory"] = f"warning: {memory.percent:.1f}% used"
            if memory.percent > 95:
                overall_status = "unhealthy"
        else:
            checks["memory"] = "healthy"
    except ImportError:
        checks["memory"] = "not_available"
    except Exception as e:
        logger.error(f"Memory health check failed: {e}")
        checks["memory"] = f"error: {str(e)}"
    
    # Service-specific checks
    checks["service"] = "healthy"
    checks["timestamp"] = datetime.now().isoformat()
    checks["uptime"] = "unknown"  # Would need app startup time tracking
    
    response = {
        "status": overall_status,
        "checks": checks,
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }
    
    # Return 200 for healthy, 503 for unhealthy
    if overall_status == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response
        )
    
    return response

@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return {"status": "pong", "timestamp": datetime.now().isoformat()}

@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    try:
        # Check if database is ready
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "ready",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint"""
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }