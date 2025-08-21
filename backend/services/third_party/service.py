import os
import hashlib
import base64
import secrets
import random
import string
import requests
import logging
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, timedelta, timezone

from .models import ThirdPartyOauthDataResponse, ThirdPartyOauthResponse, EtsyConnectionStatus, EtsyDisconnectResponse
from database.entities import ThirdPartyOAuthToken, User

logger = logging.getLogger(__name__)

ETSY_API_CONFIG = {
    'base_url': 'https://openapi.etsy.com/v3',
    'ping_url': 'https://api.etsy.com/v3/application/openapi-ping',
    'token_url': 'https://api.etsy.com/v3/public/oauth/token',
    'oauth_connect_url': 'https://www.etsy.com/oauth/connect',
    'scopes': 'listings_w listings_r shops_r shops_w transactions_r',
    'code_challenge_method': 'S256',
    'response_type': 'code',
}

DEFAULTS = {
    'token_expiry_buffer': 60,  # seconds before expiry to refresh
    'default_expires_in': 3600,  # 1 hour in seconds
    'state_length': 7,
    'code_verifier_length': 32,
}

# Load OAuth credentials from environment
def get_etsy_credentials():
    """Get Etsy OAuth credentials from environment"""
    client_id = os.getenv('ETSY_CLIENT_ID')
    client_secret = os.getenv('ETSY_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.warning("Etsy credentials not configured in environment")
        return None, None
    
    if client_id == 'your-etsy-client-id' or client_secret == 'your-etsy-client-secret':
        logger.warning("Etsy credentials are using placeholder values")
        return None, None
    
    return client_id, client_secret

# Generate a secure code verifier and code challenge
def generate_code_verifier_code_challenge_and_state():
    """Generate PKCE code verifier, challenge, and state"""
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(DEFAULTS['code_verifier_length'])
    ).decode('utf-8').replace('=', '')
    
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode('utf-8').replace('=', '')
    
    state = ''.join(random.choices(
        string.ascii_lowercase + string.digits, 
        k=DEFAULTS['state_length']
    ))
    
    return code_verifier, code_challenge, state

# Global OAuth variables (regenerated for each session)
clientVerifier, codeChallenge, state = generate_code_verifier_code_challenge_and_state()

def get_redirect_uri():
    """Get the correct redirect URI for OAuth flow"""
    # Use frontend redirect URI for production
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    return f"{frontend_url}/oauth/redirect"

def get_oauth_variables():
    """Get OAuth variables for use in routes"""
    client_id, client_secret = get_etsy_credentials()
    
    return {
        'clientID': client_id,
        'clientSecret': client_secret,
        'state': state,
        'redirectUri': get_redirect_uri(),
        'clientVerifier': clientVerifier,
        'codeChallenge': codeChallenge,
    }

def get_oauth_data() -> ThirdPartyOauthDataResponse:
    """Get OAuth configuration data for frontend"""
    oauth_vars = get_oauth_variables()
    
    if not oauth_vars['clientID']:
        raise Exception("Etsy OAuth not configured")
    
    return ThirdPartyOauthDataResponse(
        clientId=oauth_vars['clientID'],
        redirectUri=oauth_vars['redirectUri'],
        codeChallenge=oauth_vars['codeChallenge'],
        state=oauth_vars['state'],
        scopes=ETSY_API_CONFIG['scopes'],
        codeChallengeMethod=ETSY_API_CONFIG['code_challenge_method'],
        responseType=ETSY_API_CONFIG['response_type'],
        oauthConnectUrl=ETSY_API_CONFIG['oauth_connect_url']
    )

def oauth_redirect(code: str, user_id: Optional[UUID], db: Session) -> ThirdPartyOauthResponse:
    """Handle OAuth redirect and exchange code for token"""
    oauth_vars = get_oauth_variables()
    
    if not oauth_vars['clientID'] or not oauth_vars['clientSecret']:
        return ThirdPartyOauthResponse(
            status_code=500,
            success=False,
            access_token="",
            refresh_token="",
            expires_in=0,
            message="Etsy OAuth not configured"
        )
    
    logger.info(f"Starting OAuth redirect for user {user_id}")
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    try:
        # Check if user has existing token (for refresh flow)
        third_party_oauth_token = None
        if user_id:
            third_party_oauth_token = db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id
            ).first()
        
        # Prepare payload for token exchange
        payload = {
            'grant_type': 'authorization_code',
            'client_id': oauth_vars['clientID'],
            'redirect_uri': oauth_vars['redirectUri'],
            'code': code,
            'code_verifier': oauth_vars['clientVerifier'],
        }
        
        logger.info(f"Making token request to Etsy API")
        response = requests.post(ETSY_API_CONFIG['token_url'], data=payload, headers=headers)
        logger.info(f"Token response status: {response.status_code}")
        
        if response.ok:
            token_data = response.json()
            logger.info("Successfully received token data from Etsy")
            
            # Store token if user is authenticated
            if user_id:
                # Create or update token record
                if not third_party_oauth_token:
                    logger.info("Creating new OAuth token record")
                    third_party_oauth_token = ThirdPartyOAuthToken(
                        user_id=user_id,
                        provider="etsy",
                        access_token=token_data['access_token'],
                        refresh_token=token_data.get('refresh_token'),
                        expires_at=datetime.now(timezone.utc) + timedelta(
                            seconds=token_data.get('expires_in', DEFAULTS['default_expires_in'])
                        )
                    )
                    db.add(third_party_oauth_token)
                else:
                    logger.info("Updating existing OAuth token record")
                    third_party_oauth_token.access_token = token_data['access_token']
                    third_party_oauth_token.refresh_token = token_data.get('refresh_token')
                    third_party_oauth_token.expires_at = datetime.now(timezone.utc) + timedelta(
                        seconds=token_data.get('expires_in', DEFAULTS['default_expires_in'])
                    )
                
                try:
                    db.commit()
                    logger.info("Successfully saved OAuth token to database")
                except Exception as e:
                    logger.error(f"Database error while saving token: {str(e)}")
                    db.rollback()
                    raise
                    
            return ThirdPartyOauthResponse(
                status_code=200,
                success=True,
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', ''),
                expires_in=token_data.get('expires_in', DEFAULTS['default_expires_in']),
                message="OAuth successful"
            )
        else:
            logger.error(f"Token request failed: {response.text}")
            return ThirdPartyOauthResponse(
                status_code=response.status_code,
                success=False,
                access_token="",
                refresh_token="",
                expires_in=0,
                message=f"Token exchange failed: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Error in oauth_redirect: {str(e)}")
        return ThirdPartyOauthResponse(
            status_code=500,
            success=False,
            access_token="",
            refresh_token="",
            expires_in=0,
            message=f"Internal error: {str(e)}"
        )

def oauth_redirect_legacy(code: str) -> ThirdPartyOauthResponse:
    """Legacy OAuth redirect for non-authenticated users"""
    return oauth_redirect(code, None, None)

def verify_etsy_connection(user_id: UUID, db: Session) -> EtsyConnectionStatus:
    """Verify if the current Etsy connection is valid"""
    try:
        logger.info(f"Verifying Etsy connection for user {user_id}")
        
        oauth_record = db.query(ThirdPartyOAuthToken).filter(
            ThirdPartyOAuthToken.user_id == user_id,
            ThirdPartyOAuthToken.provider == "etsy"
        ).first()
        
        if not oauth_record or not oauth_record.access_token:
            logger.warning(f"No OAuth record or access token for user {user_id}")
            return EtsyConnectionStatus(
                connected=False,
                message="No Etsy connection found"
            )
        
        # Check if token is expired
        if oauth_record.expires_at and oauth_record.expires_at < datetime.now(timezone.utc):
            logger.warning(f"Token expired for user {user_id}")
            return EtsyConnectionStatus(
                connected=False,
                message="Access token expired"
            )
        
        # Test the token with Etsy API
        oauth_vars = get_oauth_variables()
        if not oauth_vars['clientID']:
            return EtsyConnectionStatus(
                connected=False,
                message="Etsy OAuth not configured"
            )
        
        headers = {
            "Authorization": f"Bearer {oauth_record.access_token}",
            "x-api-key": oauth_vars['clientID']
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
            return EtsyConnectionStatus(
                connected=True,
                user_info=user_data,
                shop_info=shop_info,
                expires_at=int(oauth_record.expires_at.timestamp() * 1000) if oauth_record.expires_at else None
            )
        else:
            logger.warning(f"Token validation failed for user {user_id} - Etsy API returned {test_response.status_code}")
            return EtsyConnectionStatus(
                connected=False,
                message=f"Token validation failed (HTTP {test_response.status_code})"
            )
            
    except Exception as e:
        logger.error(f"Connection verification error: {str(e)}")
        return EtsyConnectionStatus(
            connected=False,
            message="Connection verification failed"
        )

def revoke_etsy_token(user_id: UUID, db: Session) -> EtsyDisconnectResponse:
    """Revoke Etsy access token and remove connection"""
    try:
        oauth_record = db.query(ThirdPartyOAuthToken).filter(
            ThirdPartyOAuthToken.user_id == user_id,
            ThirdPartyOAuthToken.provider == "etsy"
        ).first()
        
        if not oauth_record:
            return EtsyDisconnectResponse(
                success=True, 
                message="No connection found to revoke"
            )
        
        # Remove the OAuth record
        db.delete(oauth_record)
        db.commit()
        
        return EtsyDisconnectResponse(
            success=True, 
            message="Connection revoked successfully"
        )
        
    except Exception as e:
        logger.error(f"Token revocation error: {str(e)}")
        return EtsyDisconnectResponse(
            success=False, 
            message="Token revocation failed",
            error=str(e)
        )