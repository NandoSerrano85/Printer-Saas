from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
import logging

from common.auth import get_current_user
from common.database import get_database_manager
from database.core import create_core_tables

# Import service routers
from services.auth.controller import router as auth_router
from services.tenant.controller import router as tenant_router
from services.user.controller import router as user_router
from services.template.controller import router as template_router
from services.order.controller import router as order_router
from services.etsy.controller import router as etsy_router
from services.shopify.controller import router as shopify_router
from services.dashboard.controller import router as dashboard_router
from services.third_party.controller import router as third_party_router

# Import common routers
from services.common.health import router as health_router
from services.common.metrics import router as metrics_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Printer SaaS Backend...")
    
    # Initialize database
    print("DEBUG: About to call create_core_tables()")
    create_core_tables()
    print("DEBUG: Finished calling create_core_tables()")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Printer SaaS Backend...")

# Create FastAPI application
app = FastAPI(
    title="Printer SaaS Backend",
    description="Multi-tenant print-on-demand SaaS platform backend",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
from services.common.security_middleware import TenantSecurityMiddleware
app.add_middleware(TenantSecurityMiddleware)

# Include health and metrics routers (no auth required)
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(metrics_router, prefix="/metrics", tags=["Metrics"])

# Include auth and tenant management routers (no auth required for auth/tenant endpoints)
app.include_router(
    tenant_router,
    tags=["Tenant Management"]
)

app.include_router(
    auth_router,
    tags=["Authentication"]
)

app.include_router(
    user_router,
    tags=["User Management"]
)

# Include service routers (auth is handled within each router)
app.include_router(
    template_router,
    tags=["Templates"]
)

app.include_router(
    order_router,
    tags=["Orders"]
)

app.include_router(
    etsy_router,
    tags=["Etsy Integration"]
)

app.include_router(
    shopify_router,
    tags=["Shopify Integration"]
)

app.include_router(
    dashboard_router,
    tags=["Dashboard"]
)

app.include_router(
    third_party_router,
    tags=["Third Party Integration"]
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Printer SaaS Backend API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "v1",
        "status": "healthy",
        "services": {
            "auth": "active",
            "user_management": "active",
            "templates": "active",
            "orders": "active",
            "etsy": "active",
            "shopify": "active",
            "dashboard": "active",
            "health": "active",
            "metrics": "active"
        },
        "features": {
            "multi_tenant": "enabled",
            "authentication": "enabled",
            "user_management": "enabled",
            "role_based_access": "enabled",
            "email_verification": "enabled",
            "two_factor_auth": "enabled",
            "password_reset": "enabled",
            "etsy_integration": "enabled",
            "shopify_integration": "enabled",
            "order_management": "enabled",
            "template_management": "enabled",
            "dashboard_analytics": "enabled",
            "real_time_sync": "enabled",
            "batch_operations": "enabled",
            "order_preview": "enabled"
        }
    }

if __name__ == "__main__":
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    workers = int(os.getenv("WORKERS", 1))
    log_level = os.getenv("LOG_LEVEL", "info")
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run application
    if workers > 1:
        # Use gunicorn for production with multiple workers
        logger.info(f"Starting server with {workers} workers on {host}:{port}")
    else:
        # Use uvicorn for development
        logger.info(f"Starting development server on {host}:{port}")
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=os.getenv("RELOAD", "false").lower() == "true",
            log_level=log_level
        )