import os
import time
import secrets
import hashlib
import base64
import string
import random
import requests
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
import logging
from urllib.parse import urlencode

from .models import (
    EtsyAPIConfig, EtsyOAuthInitResponse, EtsyTokenResponse,
    EtsyShop, EtsyUser, EtsyListing, EtsyReceipt, EtsyTransaction,
    EtsyTaxonomy, EtsyShippingProfile, EtsyShopSection, EtsyListResponse,
    EtsyErrorResponse
)
from common.exceptions import (
    ValidationError, EtsyAPIError, EtsyAuthError, 
    EtsyRateLimitError, EtsyTokenExpiredError
)

logger = logging.getLogger(__name__)

class EtsyAPIClient:
    """Comprehensive Etsy API client with OAuth, rate limiting, and multi-tenant support"""
    
    def __init__(self, user_id: Optional[str] = None, tenant_id: Optional[str] = None):
        self.config = EtsyAPIConfig()
        self.session = requests.Session()
        self.user_id = user_id
        self.tenant_id = tenant_id
        
        # OAuth credentials from environment
        self.client_id = os.getenv('ETSY_CLIENT_ID')
        self.client_secret = os.getenv('ETSY_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            logger.warning("Etsy API credentials not found in environment variables")
        
        # Token management
        self.oauth_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: Optional[float] = None
        self.shop_id: Optional[int] = None
        
        # Rate limiting
        self._rate_limit_remaining = 10000  # Etsy allows 10,000 requests per day
        self._rate_limit_reset = time.time() + 86400  # 24 hours
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
        
        # Session configuration
        self.session.headers.update({
            'User-Agent': 'PrinterSaaS/1.0 (Etsy Integration)',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def set_credentials(self, access_token: str, refresh_token: Optional[str] = None, 
                       expires_at: Optional[datetime] = None, shop_id: Optional[int] = None):
        """Set OAuth credentials for API calls"""
        self.oauth_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = expires_at.timestamp() if expires_at else None
        self.shop_id = shop_id
        
        # Update session headers
        self.session.headers.update({
            'x-api-key': self.client_id,
            'Authorization': f'Bearer {self.oauth_token}'
        })
    
    def generate_oauth_data(self, redirect_uri: str) -> EtsyOAuthInitResponse:
        """Generate OAuth flow data with PKCE"""
        # Generate PKCE code verifier and challenge
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').replace('=', '')
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).decode('utf-8').replace('=', '')
        
        # Generate state for CSRF protection
        state = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
        
        oauth_data = EtsyOAuthInitResponse(
            oauth_connect_url=self.config.oauth_connect_url,
            client_id=self.client_id,
            redirect_uri=redirect_uri,
            scopes=self.config.scopes,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=self.config.code_challenge_method,
            response_type=self.config.response_type
        )
        
        # Store code_verifier temporarily (in production, use Redis or database)
        self._temp_code_verifier = code_verifier
        
        return oauth_data
    
    def exchange_code_for_token(self, code: str, code_verifier: str, 
                               redirect_uri: str) -> EtsyTokenResponse:
        """Exchange OAuth code for access token"""
        try:
            data = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'redirect_uri': redirect_uri,
                'code': code,
                'code_verifier': code_verifier
            }
            
            response = requests.post(self.config.token_url, data=data)
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
                raise EtsyAuthError("Failed to exchange authorization code for token")
            
            token_data = response.json()
            
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data['expires_in'])
            
            return EtsyTokenResponse(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                expires_in=token_data['expires_in'],
                token_type=token_data.get('token_type', 'Bearer'),
                expires_at=expires_at
            )
            
        except requests.RequestException as e:
            logger.error(f"Network error during token exchange: {e}")
            raise EtsyAuthError("Network error during token exchange")
        except Exception as e:
            logger.error(f"Unexpected error during token exchange: {e}")
            raise EtsyAuthError("Unexpected error during token exchange")
    
    def refresh_access_token(self) -> EtsyTokenResponse:
        """Refresh expired access token"""
        if not self.refresh_token:
            raise EtsyTokenExpiredError("No refresh token available")
        
        try:
            data = {
                'grant_type': 'refresh_token',
                'client_id': self.client_id,
                'refresh_token': self.refresh_token
            }
            
            response = requests.post(self.config.token_url, data=data)
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                raise EtsyTokenExpiredError("Failed to refresh access token")
            
            token_data = response.json()
            
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_data['expires_in'])
            
            # Update stored credentials
            self.oauth_token = token_data['access_token']
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
            self.token_expiry = expires_at.timestamp()
            
            # Update session headers
            self.session.headers.update({
                'Authorization': f'Bearer {self.oauth_token}'
            })
            
            return EtsyTokenResponse(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', self.refresh_token),
                expires_in=token_data['expires_in'],
                token_type=token_data.get('token_type', 'Bearer'),
                expires_at=expires_at
            )
            
        except requests.RequestException as e:
            logger.error(f"Network error during token refresh: {e}")
            raise EtsyTokenExpiredError("Network error during token refresh")
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {e}")
            raise EtsyTokenExpiredError("Unexpected error during token refresh")
    
    def is_token_expired(self) -> bool:
        """Check if access token is expired or about to expire"""
        if not self.token_expiry:
            return True
        return time.time() > (self.token_expiry - 60)  # Refresh 1 minute before expiry
    
    def ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.oauth_token:
            raise EtsyAuthError("No access token available")
        
        if self.is_token_expired():
            logger.info("Access token expired, refreshing...")
            self.refresh_access_token()
    
    def test_token(self) -> bool:
        """Test if current access token is valid"""
        try:
            response = self._make_request('GET', '/application/openapi-ping')
            return response.status_code == 200
        except:
            return False
    
    def _handle_rate_limiting(self):
        """Handle rate limiting between requests"""
        current_time = time.time()
        
        # Ensure minimum interval between requests
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last)
        
        self._last_request_time = time.time()
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, files: Optional[Dict] = None) -> requests.Response:
        """Make authenticated request to Etsy API with error handling"""
        self.ensure_valid_token()
        self._handle_rate_limiting()
        
        url = f"{self.config.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data if data and not files else None,
                data=data if files else None,
                files=files,
                timeout=30
            )
            
            # Update rate limit info from headers
            if 'X-RateLimit-Remaining' in response.headers:
                self._rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
            
            if 'X-RateLimit-Reset' in response.headers:
                self._rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                raise EtsyRateLimitError(f"Rate limited, retry after {retry_after} seconds")
            
            # Handle authentication errors
            if response.status_code == 401:
                logger.error("Authentication failed, token may be invalid")
                raise EtsyAuthError("Authentication failed")
            
            # Handle other client errors
            if 400 <= response.status_code < 500:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('error_msg', f"Client error: {response.status_code}")
                logger.error(f"Client error: {response.status_code} - {error_msg}")
                raise EtsyAPIError(error_msg, status_code=response.status_code)
            
            # Handle server errors
            if response.status_code >= 500:
                logger.error(f"Server error: {response.status_code}")
                raise EtsyAPIError("Etsy API server error", status_code=response.status_code)
            
            return response
            
        except requests.RequestException as e:
            logger.error(f"Network error making request to {url}: {e}")
            raise EtsyAPIError(f"Network error: {e}")
    
    # User and Shop Methods
    def get_current_user(self) -> EtsyUser:
        """Get current authenticated user info"""
        response = self._make_request('GET', '/application/users/me')
        user_data = response.json()
        return EtsyUser(**user_data)
    
    def get_user_shops(self, user_id: Optional[int] = None) -> List[EtsyShop]:
        """Get shops for a user"""
        if not user_id:
            user = self.get_current_user()
            user_id = user.user_id
        
        response = self._make_request('GET', f'/application/users/{user_id}/shops')
        shops_data = response.json()
        return [EtsyShop(**shop) for shop in shops_data.get('results', [])]
    
    def get_shop(self, shop_id: Optional[int] = None) -> EtsyShop:
        """Get shop information"""
        if not shop_id:
            shop_id = self.shop_id
        
        if not shop_id:
            shops = self.get_user_shops()
            if shops:
                shop_id = shops[0].shop_id
                self.shop_id = shop_id
            else:
                raise EtsyAPIError("No shop found for user")
        
        response = self._make_request('GET', f'/application/shops/{shop_id}')
        shop_data = response.json()
        return EtsyShop(**shop_data)
    
    # Taxonomy Methods
    def get_seller_taxonomy(self) -> List[EtsyTaxonomy]:
        """Get Etsy seller taxonomy"""
        response = self._make_request('GET', '/application/seller-taxonomy/nodes')
        taxonomy_data = response.json()
        return [EtsyTaxonomy(**node) for node in taxonomy_data.get('results', [])]
    
    def get_flat_taxonomy(self) -> List[Dict[str, Any]]:
        """Get flattened taxonomy for easier use"""
        taxonomies = self.get_seller_taxonomy()
        flat_list = []
        
        def flatten_node(node: EtsyTaxonomy, path: str = ""):
            current_path = f"{path} > {node.name}" if path else node.name
            
            if not node.children:  # Leaf node
                flat_list.append({
                    "id": node.id,
                    "name": node.name,
                    "full_path": current_path,
                    "level": node.level,
                    "parent_id": node.parent_id
                })
            
            for child in node.children:
                flatten_node(child, current_path)
        
        for taxonomy in taxonomies:
            flatten_node(taxonomy)
        
        return sorted(flat_list, key=lambda x: x["name"].lower())
    
    # Shop Configuration Methods
    def get_shipping_profiles(self, shop_id: Optional[int] = None) -> List[EtsyShippingProfile]:
        """Get shop shipping profiles"""
        if not shop_id:
            shop_id = self.shop_id
        
        response = self._make_request('GET', f'/application/shops/{shop_id}/shipping-profiles')
        profiles_data = response.json()
        return [EtsyShippingProfile(**profile) for profile in profiles_data.get('results', [])]
    
    def get_shop_sections(self, shop_id: Optional[int] = None) -> List[EtsyShopSection]:
        """Get shop sections"""
        if not shop_id:
            shop_id = self.shop_id
        
        response = self._make_request('GET', f'/application/shops/{shop_id}/sections')
        sections_data = response.json()
        return [EtsyShopSection(**section) for section in sections_data.get('results', [])]
    
    # Listing Methods
    def get_shop_listings(self, shop_id: Optional[int] = None, state: str = "active", 
                         limit: int = 100, offset: int = 0) -> List[EtsyListing]:
        """Get shop listings"""
        if not shop_id:
            shop_id = self.shop_id
        
        params = {
            'state': state,
            'limit': min(limit, 100),  # Etsy max is 100
            'offset': offset
        }
        
        response = self._make_request('GET', f'/application/shops/{shop_id}/listings', params=params)
        listings_data = response.json()
        return [EtsyListing(**listing) for listing in listings_data.get('results', [])]
    
    def get_listing(self, listing_id: int) -> EtsyListing:
        """Get specific listing"""
        response = self._make_request('GET', f'/application/listings/{listing_id}')
        listing_data = response.json()
        return EtsyListing(**listing_data)
    
    def create_draft_listing(self, listing_data: Dict[str, Any], shop_id: Optional[int] = None) -> EtsyListing:
        """Create a draft listing"""
        if not shop_id:
            shop_id = self.shop_id
        
        response = self._make_request('POST', f'/application/shops/{shop_id}/listings', data=listing_data)
        listing_response = response.json()
        return EtsyListing(**listing_response)
    
    def update_listing(self, listing_id: int, listing_data: Dict[str, Any], 
                      shop_id: Optional[int] = None) -> EtsyListing:
        """Update existing listing"""
        if not shop_id:
            shop_id = self.shop_id
        
        response = self._make_request('PATCH', f'/application/shops/{shop_id}/listings/{listing_id}', 
                                    data=listing_data)
        listing_response = response.json()
        return EtsyListing(**listing_response)
    
    def upload_listing_image(self, listing_id: int, image_path: str, 
                           shop_id: Optional[int] = None) -> Dict[str, Any]:
        """Upload image to listing"""
        if not shop_id:
            shop_id = self.shop_id
        
        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = self._make_request('POST', 
                                        f'/application/shops/{shop_id}/listings/{listing_id}/images',
                                        files=files)
        
        return response.json()
    
    # Order Methods
    def get_shop_receipts(self, shop_id: Optional[int] = None, was_paid: bool = True, 
                         was_shipped: bool = None, limit: int = 100, offset: int = 0) -> List[EtsyReceipt]:
        """Get shop receipts (orders)"""
        if not shop_id:
            shop_id = self.shop_id
        
        params = {
            'was_paid': str(was_paid).lower(),
            'limit': min(limit, 100),
            'offset': offset
        }
        
        if was_shipped is not None:
            params['was_shipped'] = str(was_shipped).lower()
        
        response = self._make_request('GET', f'/application/shops/{shop_id}/receipts', params=params)
        receipts_data = response.json()
        return [EtsyReceipt(**receipt) for receipt in receipts_data.get('results', [])]
    
    def get_receipt(self, receipt_id: int, shop_id: Optional[int] = None) -> EtsyReceipt:
        """Get specific receipt"""
        if not shop_id:
            shop_id = self.shop_id
        
        response = self._make_request('GET', f'/application/shops/{shop_id}/receipts/{receipt_id}')
        receipt_data = response.json()
        return EtsyReceipt(**receipt_data)
    
    def get_receipt_transactions(self, receipt_id: int, shop_id: Optional[int] = None) -> List[EtsyTransaction]:
        """Get transactions for a receipt"""
        if not shop_id:
            shop_id = self.shop_id
        
        response = self._make_request('GET', f'/application/shops/{shop_id}/receipts/{receipt_id}/transactions')
        transactions_data = response.json()
        return [EtsyTransaction(**transaction) for transaction in transactions_data.get('results', [])]
    
    def update_receipt_tracking(self, receipt_id: int, tracking_code: str, carrier_name: str,
                              shop_id: Optional[int] = None) -> Dict[str, Any]:
        """Update receipt tracking information"""
        if not shop_id:
            shop_id = self.shop_id
        
        data = {
            'tracking_code': tracking_code,
            'carrier_name': carrier_name
        }
        
        response = self._make_request('POST', f'/application/shops/{shop_id}/receipts/{receipt_id}/tracking',
                                    data=data)
        return response.json()
    
    # Analytics and Stats Methods
    def get_shop_stats(self, shop_id: Optional[int] = None) -> Dict[str, Any]:
        """Get comprehensive shop statistics"""
        if not shop_id:
            shop_id = self.shop_id
        
        # Get basic shop info
        shop = self.get_shop(shop_id)
        
        # Get listings stats
        active_listings = self.get_shop_listings(shop_id, state="active", limit=1)
        total_active = len(active_listings) if active_listings else 0
        
        # Get recent orders
        recent_receipts = self.get_shop_receipts(shop_id, limit=50)
        
        # Calculate stats
        total_revenue = sum(
            float(receipt.grandtotal.get('amount', 0)) if receipt.grandtotal else 0
            for receipt in recent_receipts
        )
        
        return {
            'shop_info': shop,
            'total_listings': shop.listing_active_count,
            'active_listings': total_active,
            'total_orders': len(recent_receipts),
            'total_revenue': total_revenue,
            'recent_orders': recent_receipts[:10],
            'shop_rating': shop.review_average,
            'total_reviews': shop.review_count
        }