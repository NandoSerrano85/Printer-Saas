from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from database.core import get_db
from common.auth import get_current_user_optional, ActiveUserDep
from .models import ThirdPartyOauthDataResponse, ThirdPartyOauthResponse, EtsyConnectionStatus, EtsyDisconnectResponse
from . import service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/api/v1/third-party',
    tags=['third-party']
)

@router.get("/oauth-data", response_model=ThirdPartyOauthDataResponse)
async def get_oauth_data():
    """API endpoint to get OAuth configuration data for the frontend."""
    try:
        return service.get_oauth_data()
    except Exception as e:
        logger.error(f"Error getting OAuth data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth configuration not available"
        )

@router.get('/oauth-redirect', response_model=ThirdPartyOauthResponse)
async def oauth_redirect(
    code: str = Query(..., description="OAuth authorization code"),
    current_user: Optional[dict] = Depends(get_current_user_optional), 
    db: Session = Depends(get_db)
):
    """Handle OAuth redirect from Etsy"""
    try:
        logger.info(f"OAuth redirect called with code: {code[:10]}...")
        
        user_id = None
        if current_user:
            user_id = current_user.get("user_id")
            if isinstance(user_id, str):
                try:
                    user_id = UUID(user_id)
                except ValueError:
                    logger.warning(f"Invalid user_id format: {user_id}")
                    user_id = None
        
        if not user_id:
            logger.warning("No authenticated user found, using legacy flow")
            return service.oauth_redirect_legacy(code)
            
        logger.info(f"Processing OAuth redirect for user {user_id}")
        response = service.oauth_redirect(code, user_id, db)
        
        if not response.success:
            logger.error(f"OAuth redirect failed: {response.message}")
            raise HTTPException(
                status_code=response.status_code,
                detail=response.message
            )
            
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in oauth_redirect endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get('/oauth-redirect-legacy', response_model=ThirdPartyOauthResponse)
async def oauth_redirect_legacy(code: str = Query(..., description="OAuth authorization code")):
    """Legacy OAuth redirect for non-authenticated users"""
    try:
        return service.oauth_redirect_legacy(code)
    except Exception as e:
        logger.error(f"Error in legacy oauth redirect: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get('/verify-connection', response_model=EtsyConnectionStatus)
async def verify_etsy_connection(
    current_user: ActiveUserDep,
    db: Session = Depends(get_db)
):
    """Verify if the current Etsy connection is valid"""
    try:
        user_id = current_user.get_uuid()
        return service.verify_etsy_connection(user_id, db)
    except Exception as e:
        logger.error(f"Error verifying connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Connection verification failed"
        )

@router.post('/revoke-token', response_model=EtsyDisconnectResponse)
async def revoke_etsy_token(
    current_user: ActiveUserDep,
    db: Session = Depends(get_db)
):
    """Revoke Etsy access token and remove connection"""
    try:
        user_id = current_user.get_uuid()
        return service.revoke_etsy_token(user_id, db)
    except Exception as e:
        logger.error(f"Error revoking token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token revocation failed"
        )