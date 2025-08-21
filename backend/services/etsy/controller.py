from fastapi import APIRouter, Depends, Query, HTTPException, status, BackgroundTasks
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from .models import (
    EtsyOAuthInitRequest, EtsyOAuthInitResponse, EtsyOAuthCallbackRequest,
    EtsyTokenResponse, EtsyIntegrationStatus, EtsyDashboardData,
    EtsyShop, EtsyUser, EtsyListing, EtsyReceipt, EtsyShippingProfile,
    EtsyShopSection, EtsySyncRequest, EtsySyncResponse, EtsyApiResponse
)
from .service import EtsyService
from common.auth import UserOrAdminDep, get_current_user_optional
from common.database import get_database_manager, DatabaseManager
from database.core import get_db
from sqlalchemy.orm import Session
from common.exceptions import (
    EtsyAPIError, EtsyAuthError, EtsyRateLimitError, 
    EtsyTokenExpiredError, UserNotFound, ValidationError
)

router = APIRouter(
    prefix="/api/v1/etsy",
    tags=["Etsy Integration"]
)

def get_etsy_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> EtsyService:
    """Dependency to get Etsy service"""
    return EtsyService(db_manager)

# OAuth and Authentication Endpoints  

@router.get("/oauth-data")
async def get_oauth_data():
    """Get OAuth configuration data for frontend (compatible with working example)"""
    import os
    import secrets
    import hashlib
    import base64
    import random
    import string
    
    # Generate PKCE parameters (same as third-party service)
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').replace('=', '')
    
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').replace('=', '')
    
    state = ''.join(random.choices(
        string.ascii_lowercase + string.digits, 
        k=7
    ))
    
    client_id = os.getenv('ETSY_CLIENT_ID')
    if not client_id:
        raise HTTPException(
            status_code=500,
            detail="Etsy OAuth not configured"
        )
    
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    redirect_uri = f"{frontend_url}/oauth/redirect"
    
    # Store the code_verifier and state in a global dict for this session
    # In production, you'd use Redis or a database
    global _oauth_session
    _oauth_session = {
        'code_verifier': code_verifier,
        'state': state
    }
    
    return {
        "clientId": client_id,
        "redirectUri": redirect_uri,
        "codeChallenge": code_challenge,
        "state": state,
        "scopes": "listings_w listings_r shops_r shops_w transactions_r",
        "codeChallengeMethod": "S256",
        "responseType": "code",
        "oauthConnectUrl": "https://www.etsy.com/oauth/connect"
    }

# Global variable to store OAuth session data (use Redis in production)
_oauth_session = {}

@router.get("/oauth-redirect")
async def oauth_redirect(
    code: str = Query(..., description="OAuth authorization code"),
    current_user: Optional[dict] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Handle OAuth redirect (compatible with working example)"""
    import os
    import requests
    import logging
    from datetime import datetime, timezone, timedelta
    from database.entities import ThirdPartyOAuthToken
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"OAuth redirect called with code: {code[:10]}...")
        
        client_id = os.getenv('ETSY_CLIENT_ID')
        client_secret = os.getenv('ETSY_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            return {
                "status_code": 500,
                "success": False,
                "access_token": "",
                "refresh_token": "",
                "expires_in": 0,
                "message": "Etsy OAuth not configured"
            }
        
        # Get stored OAuth session data
        global _oauth_session
        code_verifier = _oauth_session.get('code_verifier')
        
        if not code_verifier:
            logger.warning("No code_verifier found in session")
            return {
                "status_code": 400,
                "success": False,
                "access_token": "",
                "refresh_token": "",
                "expires_in": 0,
                "message": "Invalid OAuth session"
            }
        
        # Exchange code for token
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        redirect_uri = f"{frontend_url}/oauth/redirect"
        
        payload = {
            'grant_type': 'authorization_code',
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'code': code,
            'code_verifier': code_verifier,
        }
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        
        logger.info("Making token request to Etsy API")
        response = requests.post("https://api.etsy.com/v3/public/oauth/token", data=payload, headers=headers)
        logger.info(f"Token response status: {response.status_code}")
        
        if response.ok:
            token_data = response.json()
            logger.info("Successfully received token data from Etsy")
            
            # Store token if user is authenticated
            if current_user:
                user_id = current_user.get("user_id")
                if user_id:
                    try:
                        from uuid import UUID
                        user_id = UUID(user_id) if isinstance(user_id, str) else user_id
                        
                        # Create or update token record
                        existing_token = db.query(ThirdPartyOAuthToken).filter(
                            ThirdPartyOAuthToken.user_id == user_id,
                            ThirdPartyOAuthToken.provider == "etsy"
                        ).first()
                        
                        if existing_token:
                            logger.info("Updating existing OAuth token record")
                            existing_token.access_token = token_data['access_token']
                            existing_token.refresh_token = token_data.get('refresh_token')
                            existing_token.expires_at = datetime.now(timezone.utc) + timedelta(
                                seconds=token_data.get('expires_in', 3600)
                            )
                        else:
                            logger.info("Creating new OAuth token record")
                            new_token = ThirdPartyOAuthToken(
                                user_id=user_id,
                                provider="etsy",
                                access_token=token_data['access_token'],
                                refresh_token=token_data.get('refresh_token'),
                                expires_at=datetime.now(timezone.utc) + timedelta(
                                    seconds=token_data.get('expires_in', 3600)
                                )
                            )
                            db.add(new_token)
                        
                        db.commit()
                        logger.info("Successfully saved OAuth token to database")
                        
                    except Exception as e:
                        logger.error(f"Database error while saving token: {str(e)}")
                        db.rollback()
                        # Don't fail the whole request if DB save fails
            
            return {
                "status_code": 200,
                "success": True,
                "access_token": token_data['access_token'],
                "refresh_token": token_data.get('refresh_token', ''),
                "expires_in": token_data.get('expires_in', 3600),
                "message": "OAuth successful"
            }
        else:
            logger.error(f"Token request failed: {response.text}")
            return {
                "status_code": response.status_code,
                "success": False,
                "access_token": "",
                "refresh_token": "",
                "expires_in": 0,
                "message": f"Token exchange failed: {response.text}"
            }
            
    except Exception as e:
        logger.error(f"Error in oauth_redirect: {str(e)}")
        return {
            "status_code": 500,
            "success": False,
            "access_token": "",
            "refresh_token": "",
            "expires_in": 0,
            "message": f"Internal error: {str(e)}"
        }

@router.get("/verify-connection")
async def verify_connection(
    current_user: UserOrAdminDep,
    db: Session = Depends(get_db)
):
    """Verify Etsy connection status"""
    import os
    import requests
    import logging
    from database.entities import ThirdPartyOAuthToken
    from datetime import datetime, timezone
    
    logger = logging.getLogger(__name__)
    
    try:
        user_id = current_user.get_uuid()
        logger.info(f"Verifying Etsy connection for user {user_id}")
        
        oauth_record = db.query(ThirdPartyOAuthToken).filter(
            ThirdPartyOAuthToken.user_id == user_id,
            ThirdPartyOAuthToken.provider == "etsy"
        ).first()
        
        if not oauth_record or not oauth_record.access_token:
            logger.warning(f"No OAuth record or access token for user {user_id}")
            return {
                "connected": False,
                "message": "No Etsy connection found"
            }
        
        # Check if token is expired
        if oauth_record.expires_at and oauth_record.expires_at < datetime.now(timezone.utc):
            logger.warning(f"Token expired for user {user_id}")
            return {
                "connected": False,
                "message": "Access token expired"
            }
        
        # Test the token with Etsy API
        client_id = os.getenv('ETSY_CLIENT_ID')
        if not client_id:
            return {
                "connected": False,
                "message": "Etsy OAuth not configured"
            }
        
        headers = {
            "Authorization": f"Bearer {oauth_record.access_token}",
            "x-api-key": client_id
        }
        
        logger.info(f"Making test request to Etsy API for user {user_id}")
        
        # Test endpoint - get user info
        test_response = requests.get(
            "https://openapi.etsy.com/v3/application/users/me",
            headers=headers
        )
        
        logger.info(f"Etsy API response status: {test_response.status_code}")
        
        if test_response.status_code == 200:
            user_data = test_response.json()
            
            # Also get shop info if available
            shop_info = None
            try:
                shops_response = requests.get(
                    "https://openapi.etsy.com/v3/application/users/me/shops",
                    headers=headers
                )
                if shops_response.status_code == 200:
                    shops_data = shops_response.json()
                    if shops_data.get("results") and len(shops_data["results"]) > 0:
                        shop_info = shops_data["results"][0]
            except Exception as e:
                logger.warning(f"Failed to get shop info: {str(e)}")
            
            logger.info(f"User {user_id} successfully connected to Etsy")
            return {
                "connected": True,
                "user_info": user_data,
                "shop_info": shop_info,
                "expires_at": int(oauth_record.expires_at.timestamp() * 1000) if oauth_record.expires_at else None
            }
        else:
            logger.warning(f"Token validation failed for user {user_id} - Etsy API returned {test_response.status_code}")
            return {
                "connected": False,
                "message": f"Token validation failed (HTTP {test_response.status_code})"
            }
            
    except Exception as e:
        logger.error(f"Connection verification error: {str(e)}")
        return {
            "connected": False,
            "message": "Connection verification failed"
        }

@router.post("/revoke-token")
async def revoke_token(
    current_user: UserOrAdminDep,
    db: Session = Depends(get_db)
):
    """Revoke Etsy access token and remove connection"""
    import logging
    from database.entities import ThirdPartyOAuthToken
    
    logger = logging.getLogger(__name__)
    
    try:
        user_id = current_user.get_uuid()
        oauth_record = db.query(ThirdPartyOAuthToken).filter(
            ThirdPartyOAuthToken.user_id == user_id,
            ThirdPartyOAuthToken.provider == "etsy"
        ).first()
        
        if not oauth_record:
            return {
                "success": True, 
                "message": "No connection found to revoke"
            }
        
        # Remove the OAuth record
        db.delete(oauth_record)
        db.commit()
        
        return {
            "success": True, 
            "message": "Connection revoked successfully"
        }
        
    except Exception as e:
        logger.error(f"Token revocation error: {str(e)}")
        return {
            "success": False, 
            "message": "Token revocation failed",
            "error": str(e)
        }

@router.post("/oauth/init", response_model=EtsyOAuthInitResponse)
async def initiate_oauth_flow(
    oauth_request: EtsyOAuthInitRequest,
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Initiate OAuth flow with Etsy"""
    try:
        return etsy_service.initiate_oauth_flow(
            user_id=current_user.get_uuid(),
            redirect_uri=oauth_request.redirect_uri
        )
    except EtsyAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/oauth/callback", response_model=EtsyTokenResponse)
async def oauth_callback(
    callback_data: EtsyOAuthCallbackRequest,
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service),
    redirect_uri: str = Query(..., description="OAuth redirect URI")
):
    """Handle OAuth callback and exchange code for token"""
    try:
        return etsy_service.complete_oauth_flow(
            user_id=current_user.get_uuid(),
            code=callback_data.code,
            code_verifier=callback_data.code_verifier,
            state=callback_data.state,
            redirect_uri=redirect_uri
        )
    except EtsyAuthError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/integration/status", response_model=EtsyIntegrationStatus)
async def get_integration_status(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Get Etsy integration status for current user"""
    return etsy_service.get_integration_status(current_user.get_uuid())

@router.delete("/integration/disconnect", response_model=EtsyApiResponse)
async def disconnect_etsy(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Disconnect Etsy integration"""
    success = etsy_service.disconnect_etsy(current_user.get_uuid())
    
    if success:
        return EtsyApiResponse(
            success=True,
            message="Etsy integration disconnected successfully"
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect Etsy integration"
        )

# Shop and User Information Endpoints

@router.get("/shop", response_model=EtsyShop)
async def get_shop_info(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Get shop information from Etsy"""
    try:
        return etsy_service.get_shop_info(current_user.get_uuid())
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user", response_model=EtsyUser)
async def get_user_info(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Get Etsy user information"""
    try:
        return etsy_service.get_user_info(current_user.get_uuid())
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Configuration Endpoints

@router.get("/taxonomies", response_model=List[Dict[str, Any]])
async def get_taxonomies(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Get Etsy taxonomies (categories)"""
    try:
        return etsy_service.get_taxonomies(current_user.get_uuid())
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shipping-profiles", response_model=List[EtsyShippingProfile])
async def get_shipping_profiles(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Get shop shipping profiles"""
    try:
        return etsy_service.get_shipping_profiles(current_user.get_uuid())
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shop-sections", response_model=List[EtsyShopSection])
async def get_shop_sections(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Get shop sections"""
    try:
        return etsy_service.get_shop_sections(current_user.get_uuid())
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Listing Management Endpoints

@router.get("/listings", response_model=List[EtsyListing])
async def get_shop_listings(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service),
    state: str = Query("active", description="Listing state (active, inactive, draft, etc.)"),
    limit: int = Query(25, ge=1, le=100, description="Number of listings to return"),
    offset: int = Query(0, ge=0, description="Number of listings to skip")
):
    """Get shop listings from Etsy"""
    try:
        return etsy_service.get_shop_listings(
            user_id=current_user.get_uuid(),
            state=state,
            limit=limit,
            offset=offset
        )
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/listings/from-template/{template_id}", response_model=EtsyListing)
async def create_listing_from_template(
    template_id: UUID,
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service),
    custom_data: Optional[Dict[str, Any]] = None
):
    """Create Etsy listing from internal template"""
    try:
        return etsy_service.create_listing_from_template(
            user_id=current_user.get_uuid(),
            template_id=template_id,
            custom_data=custom_data
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Order Management Endpoints

@router.get("/orders", response_model=List[EtsyReceipt])
async def get_shop_orders(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service),
    was_paid: bool = Query(True, description="Filter by payment status"),
    was_shipped: Optional[bool] = Query(None, description="Filter by shipping status"),
    limit: int = Query(25, ge=1, le=100, description="Number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip")
):
    """Get shop orders from Etsy"""
    try:
        return etsy_service.get_shop_orders(
            user_id=current_user.get_uuid(),
            was_paid=was_paid,
            was_shipped=was_shipped,
            limit=limit,
            offset=offset
        )
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orders/sync", response_model=Dict[str, int])
async def sync_orders(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service),
    limit: int = Query(50, ge=1, le=100, description="Number of orders to sync")
):
    """Sync Etsy orders to internal order system"""
    try:
        return etsy_service.sync_orders_to_internal(
            user_id=current_user.get_uuid(),
            limit=limit
        )
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard Data Endpoints

@router.get("/dashboard", response_model=EtsyDashboardData)
async def get_dashboard_data(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Get comprehensive dashboard data from Etsy"""
    try:
        return etsy_service.get_dashboard_data(current_user.get_uuid())
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Get simplified dashboard statistics"""
    try:
        dashboard_data = etsy_service.get_dashboard_data(current_user.get_uuid())
        
        return {
            "shop_name": dashboard_data.shop_info.shop_name,
            "total_listings": dashboard_data.shop_stats.total_listings,
            "active_listings": dashboard_data.shop_stats.active_listings,
            "total_orders": dashboard_data.shop_stats.total_orders,
            "total_revenue": float(dashboard_data.shop_stats.total_revenue),
            "orders_this_month": dashboard_data.shop_stats.orders_this_month,
            "revenue_this_month": float(dashboard_data.shop_stats.revenue_this_month),
            "average_order_value": float(dashboard_data.shop_stats.average_order_value),
            "shop_rating": dashboard_data.shop_stats.shop_rating,
            "total_reviews": dashboard_data.shop_stats.total_reviews,
            "pending_orders_count": len(dashboard_data.pending_orders),
            "low_stock_count": len(dashboard_data.low_stock_listings),
            "last_updated": dashboard_data.last_updated.isoformat()
        }
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Sync Operations

@router.post("/sync", response_model=EtsySyncResponse)
async def sync_data(
    sync_request: EtsySyncRequest,
    background_tasks: BackgroundTasks,
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Perform data sync from Etsy"""
    try:
        # For large syncs, run in background
        if sync_request.sync_type == "all" or sync_request.force_full_sync:
            # In production, this would use Celery or similar
            background_tasks.add_task(
                etsy_service.sync_data,
                current_user.get_uuid(),
                sync_request
            )
            
            return EtsySyncResponse(
                sync_id=f"bg_sync_{current_user.get_uuid()}",
                status="started",
                sync_type=sync_request.sync_type,
                started_at=datetime.now(),
                message="Background sync started"
            )
        else:
            # Run sync immediately for small operations
            return etsy_service.sync_data(current_user.get_uuid(), sync_request)
            
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health and Testing Endpoints

@router.get("/health", response_model=EtsyApiResponse)
async def health_check(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Health check for Etsy integration"""
    try:
        status = etsy_service.get_integration_status(current_user.get_uuid())
        
        if status.is_connected:
            return EtsyApiResponse(
                success=True,
                message="Etsy integration is healthy",
                data={
                    "shop_id": status.shop_id,
                    "shop_name": status.shop_name,
                    "last_sync": status.last_sync.isoformat() if status.last_sync else None
                }
            )
        else:
            return EtsyApiResponse(
                success=False,
                message="Etsy integration not connected",
                error=status.error_message
            )
            
    except Exception as e:
        return EtsyApiResponse(
            success=False,
            message="Health check failed",
            error=str(e)
        )

@router.post("/test-connection", response_model=EtsyApiResponse)
async def test_connection(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Test Etsy API connection"""
    try:
        # Set up client and test
        etsy_service._setup_client_for_user(current_user.get_uuid())
        
        if etsy_service.client.test_token():
            shop_info = etsy_service.get_shop_info(current_user.get_uuid())
            
            return EtsyApiResponse(
                success=True,
                message="Connection test successful",
                data={
                    "shop_id": shop_info.shop_id,
                    "shop_name": shop_info.shop_name,
                    "is_vacation": shop_info.is_vacation
                }
            )
        else:
            return EtsyApiResponse(
                success=False,
                message="Connection test failed",
                error="Token validation failed"
            )
            
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        return EtsyApiResponse(
            success=False,
            message="Connection test failed",
            error=str(e)
        )

# Analytics and Reporting

@router.get("/analytics/revenue", response_model=Dict[str, Any])
async def get_revenue_analytics(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get revenue analytics from Etsy"""
    try:
        # This would be expanded to provide detailed analytics
        dashboard_data = etsy_service.get_dashboard_data(current_user.get_uuid())
        
        # Simple analytics for now
        return {
            "period_days": days,
            "total_revenue": float(dashboard_data.shop_stats.total_revenue),
            "average_order_value": float(dashboard_data.shop_stats.average_order_value),
            "total_orders": dashboard_data.shop_stats.total_orders,
            "revenue_this_month": float(dashboard_data.shop_stats.revenue_this_month),
            "orders_this_month": dashboard_data.shop_stats.orders_this_month
        }
        
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/listings", response_model=Dict[str, Any])
async def get_listing_analytics(
    current_user: UserOrAdminDep,
    etsy_service: EtsyService = Depends(get_etsy_service)
):
    """Get listing analytics from Etsy"""
    try:
        dashboard_data = etsy_service.get_dashboard_data(current_user.get_uuid())
        
        return {
            "total_listings": dashboard_data.shop_stats.total_listings,
            "active_listings": dashboard_data.shop_stats.active_listings,
            "sold_listings": dashboard_data.shop_stats.sold_listings,
            "draft_listings": dashboard_data.shop_stats.draft_listings,
            "low_stock_count": len(dashboard_data.low_stock_listings),
            "low_stock_listings": [
                {
                    "listing_id": listing.listing_id,
                    "title": listing.title,
                    "quantity": listing.quantity
                }
                for listing in dashboard_data.low_stock_listings[:10]
            ]
        }
        
    except EtsyAuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except EtsyAPIError as e:
        raise HTTPException(status_code=500, detail=str(e))