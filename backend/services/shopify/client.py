import asyncio
import hashlib
import hmac
import json
import time
import uuid
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
import requests
from urllib.parse import urlencode, urlparse
import logging

from .models import (
    ShopifyAPIConfig, ShopifyTokenResponse, ShopifyShop, ShopifyProduct,
    ShopifyProductCreate, ShopifyProductUpdate, ShopifyOrder, ShopifyCustomer,
    ShopifyCollection, ShopifyCollectionCreate, ShopifySmartCollection,
    ShopifyCustomCollection, ShopifyBatchOperation, ShopifyBatchResult,
    OrderPreview, OrderPreviewItem, ShopifyOAuthInitResponse,
    ShopifyOAuthCallbackRequest, ShopifyApiResponse
)
from common.exceptions import ShopifyAPIError, ShopifyAuthenticationError, ShopifyRateLimitError

logger = logging.getLogger(__name__)

class ShopifyAPIClient:
    """
    Shopify API client with OAuth 2.0 support, rate limiting, and comprehensive error handling
    """
    
    def __init__(self, user_id: Optional[str] = None, tenant_id: Optional[str] = None):
        self.config = ShopifyAPIConfig()
        self.session = requests.Session()
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.access_token = None
        self.shop_domain = None
        
        # Rate limiting
        self.rate_limit_remaining = 40  # Shopify default bucket size
        self.rate_limit_reset_time = time.time() + 1  # Reset every second
        self.last_request_time = 0
        
        # API versioning
        self.api_version = "2023-10"
        
        # Session configuration
        self.session.headers.update({
            'User-Agent': 'PrinterSaaS-ShopifyClient/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Client credentials (should be loaded from environment)
        import os
        self.client_id = os.getenv('SHOPIFY_CLIENT_ID')
        self.client_secret = os.getenv('SHOPIFY_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            logger.warning("Shopify client credentials not found in environment variables")
    
    def set_credentials(self, access_token: str, shop_domain: str):
        """Set the access token and shop domain for API calls"""
        self.access_token = access_token
        self.shop_domain = shop_domain.replace('.myshopify.com', '')
        
        self.session.headers.update({
            'X-Shopify-Access-Token': access_token
        })
    
    def _get_base_url(self) -> str:
        """Get the base URL for API calls"""
        if not self.shop_domain:
            raise ShopifyAuthenticationError("Shop domain not set")
        return f"https://{self.shop_domain}.myshopify.com/admin/api/{self.api_version}"
    
    def _wait_for_rate_limit(self):
        """Implement rate limiting to respect Shopify's API limits"""
        current_time = time.time()
        
        # Check if bucket needs to be reset
        if current_time >= self.rate_limit_reset_time:
            self.rate_limit_remaining = 40  # Reset bucket
            self.rate_limit_reset_time = current_time + 1
        
        # If no calls remaining, wait until reset
        if self.rate_limit_remaining <= 0:
            sleep_time = self.rate_limit_reset_time - current_time
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                self.rate_limit_remaining = 40
                self.rate_limit_reset_time = time.time() + 1
        
        # Minimum time between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < 0.5:  # Minimum 500ms between requests
            time.sleep(0.5 - time_since_last)
        
        self.last_request_time = time.time()
        self.rate_limit_remaining -= 1
    
    def _update_rate_limit_from_headers(self, headers: Dict[str, str]):
        """Update rate limit info from response headers"""
        if 'X-Shopify-Shop-Api-Call-Limit' in headers:
            limit_info = headers['X-Shopify-Shop-Api-Call-Limit']
            try:
                current, maximum = map(int, limit_info.split('/'))
                self.rate_limit_remaining = maximum - current
            except (ValueError, TypeError):
                logger.warning(f"Could not parse rate limit header: {limit_info}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> requests.Response:
        """Make a request to the Shopify API with error handling and rate limiting"""
        
        if not self.access_token:
            raise ShopifyAuthenticationError("Access token not set")
        
        self._wait_for_rate_limit()
        
        url = f"{self._get_base_url()}{endpoint}"
        
        try:
            # Prepare request data
            request_kwargs = {
                'params': params,
                'timeout': kwargs.get('timeout', 30),
                **kwargs
            }
            
            if data is not None:
                request_kwargs['data'] = json.dumps(data)
            
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, **request_kwargs)
            
            # Update rate limit info
            self._update_rate_limit_from_headers(response.headers)
            
            # Handle common HTTP errors
            if response.status_code == 401:
                raise ShopifyAuthenticationError("Invalid or expired access token")
            elif response.status_code == 403:
                raise ShopifyAuthenticationError("Insufficient permissions")
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                raise ShopifyRateLimitError(f"Rate limit exceeded, retry after {retry_after} seconds")
            elif response.status_code >= 400:
                error_detail = "Unknown error"
                try:
                    error_data = response.json()
                    error_detail = error_data.get('errors', error_data.get('error', str(error_data)))
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                
                raise ShopifyAPIError(
                    detail=f"Shopify API error: {error_detail}",
                    status_code=response.status_code
                )
            
            return response
            
        except requests.exceptions.Timeout:
            raise ShopifyAPIError("Request timeout")
        except requests.exceptions.ConnectionError:
            raise ShopifyAPIError("Connection error")
        except requests.exceptions.RequestException as e:
            raise ShopifyAPIError(f"Request failed: {str(e)}")
    
    def _get_json_response(self, response: requests.Response) -> Dict[str, Any]:
        """Extract JSON data from response"""
        try:
            return response.json()
        except ValueError:
            raise ShopifyAPIError("Invalid JSON response from Shopify API")
    
    # OAuth Methods
    
    def generate_oauth_url(self, shop_domain: str, redirect_uri: str, state: str) -> ShopifyOAuthInitResponse:
        """Generate OAuth authorization URL"""
        shop_domain = shop_domain.replace('.myshopify.com', '')
        
        params = {
            'client_id': self.client_id,
            'scope': self.config.scopes,
            'redirect_uri': redirect_uri,
            'state': state,
            'grant_options[]': 'per-user'
        }
        
        oauth_url = f"https://{shop_domain}.myshopify.com/admin/oauth/authorize?" + urlencode(params)
        
        return ShopifyOAuthInitResponse(
            oauth_url=oauth_url,
            shop_domain=shop_domain,
            client_id=self.client_id,
            redirect_uri=redirect_uri,
            scopes=self.config.scopes,
            state=state
        )
    
    def verify_webhook_hmac(self, data: bytes, hmac_header: str) -> bool:
        """Verify HMAC signature for webhooks"""
        if not self.client_secret:
            return False
        
        calculated_hmac = hmac.new(
            self.client_secret.encode('utf-8'),
            data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(calculated_hmac, hmac_header)
    
    def exchange_code_for_token(self, callback_data: ShopifyOAuthCallbackRequest) -> ShopifyTokenResponse:
        """Exchange authorization code for access token"""
        
        # Verify HMAC if provided
        if callback_data.hmac:
            params_to_verify = {
                'code': callback_data.code,
                'shop': callback_data.shop,
                'state': callback_data.state
            }
            query_string = urlencode(sorted(params_to_verify.items()))
            
            calculated_hmac = hmac.new(
                self.client_secret.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(calculated_hmac, callback_data.hmac):
                raise ShopifyAuthenticationError("Invalid HMAC signature")
        
        # Exchange code for token
        token_url = f"https://{callback_data.shop}.myshopify.com/admin/oauth/access_token"
        
        token_data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': callback_data.code
        }
        
        try:
            response = requests.post(token_url, json=token_data, timeout=30)
            response.raise_for_status()
            
            token_response = response.json()
            
            return ShopifyTokenResponse(
                access_token=token_response['access_token'],
                scope=token_response['scope'],
                shop_domain=callback_data.shop
            )
            
        except requests.exceptions.RequestException as e:
            raise ShopifyAuthenticationError(f"Token exchange failed: {str(e)}")
    
    # Shop Methods
    
    def get_shop_info(self) -> ShopifyShop:
        """Get shop information"""
        response = self._make_request('GET', '/shop.json')
        data = self._get_json_response(response)
        return ShopifyShop(**data['shop'])
    
    # Product Methods
    
    def get_products(
        self,
        limit: int = 50,
        page_info: Optional[str] = None,
        status: Optional[str] = None,
        product_type: Optional[str] = None,
        vendor: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get products with pagination"""
        params = {'limit': min(limit, 250)}  # Shopify max is 250
        
        if page_info:
            params['page_info'] = page_info
        if status:
            params['status'] = status
        if product_type:
            params['product_type'] = product_type
        if vendor:
            params['vendor'] = vendor
        
        response = self._make_request('GET', '/products.json', params=params)
        data = self._get_json_response(response)
        
        products = [ShopifyProduct(**product) for product in data['products']]
        
        # Extract pagination info from Link header
        link_header = response.headers.get('Link', '')
        next_page_info = None
        prev_page_info = None
        
        if 'rel="next"' in link_header:
            # Parse Link header for next page info
            import re
            next_match = re.search(r'<[^>]*page_info=([^&>]+)[^>]*>; rel="next"', link_header)
            if next_match:
                next_page_info = next_match.group(1)
        
        if 'rel="previous"' in link_header:
            prev_match = re.search(r'<[^>]*page_info=([^&>]+)[^>]*>; rel="previous"', link_header)
            if prev_match:
                prev_page_info = prev_match.group(1)
        
        return {
            'products': products,
            'has_next': next_page_info is not None,
            'has_prev': prev_page_info is not None,
            'next_page_info': next_page_info,
            'prev_page_info': prev_page_info
        }
    
    def get_product(self, product_id: int) -> ShopifyProduct:
        """Get a specific product"""
        response = self._make_request('GET', f'/products/{product_id}.json')
        data = self._get_json_response(response)
        return ShopifyProduct(**data['product'])
    
    def create_product(self, product_data: ShopifyProductCreate) -> ShopifyProduct:
        """Create a new product"""
        data = {'product': product_data.model_dump(exclude_none=True)}
        response = self._make_request('POST', '/products.json', data=data)
        result = self._get_json_response(response)
        return ShopifyProduct(**result['product'])
    
    def update_product(self, product_id: int, product_data: ShopifyProductUpdate) -> ShopifyProduct:
        """Update an existing product"""
        data = {'product': product_data.model_dump(exclude_none=True)}
        response = self._make_request('PUT', f'/products/{product_id}.json', data=data)
        result = self._get_json_response(response)
        return ShopifyProduct(**result['product'])
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product"""
        response = self._make_request('DELETE', f'/products/{product_id}.json')
        return response.status_code == 200
    
    # Batch Operations
    
    def batch_update_products(self, batch_operation: ShopifyBatchOperation) -> ShopifyBatchResult:
        """Perform batch operations on products"""
        result = ShopifyBatchResult(total_requested=len(batch_operation.product_ids))
        
        for product_id in batch_operation.product_ids:
            try:
                if batch_operation.operation == 'update':
                    update_data = ShopifyProductUpdate(**batch_operation.data)
                    self.update_product(product_id, update_data)
                elif batch_operation.operation == 'delete':
                    self.delete_product(product_id)
                elif batch_operation.operation == 'publish':
                    self.update_product(product_id, ShopifyProductUpdate(status='active'))
                elif batch_operation.operation == 'unpublish':
                    self.update_product(product_id, ShopifyProductUpdate(status='draft'))
                
                result.successful.append(product_id)
                result.total_successful += 1
                
            except Exception as e:
                result.failed.append({
                    'product_id': product_id,
                    'error': str(e)
                })
                result.total_failed += 1
                logger.error(f"Batch operation failed for product {product_id}: {str(e)}")
        
        return result
    
    # Order Methods
    
    def get_orders(
        self,
        limit: int = 50,
        page_info: Optional[str] = None,
        status: Optional[str] = None,
        financial_status: Optional[str] = None,
        fulfillment_status: Optional[str] = None,
        created_at_min: Optional[datetime] = None,
        created_at_max: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get orders with pagination and filtering"""
        params = {'limit': min(limit, 250)}
        
        if page_info:
            params['page_info'] = page_info
        if status:
            params['status'] = status
        if financial_status:
            params['financial_status'] = financial_status
        if fulfillment_status:
            params['fulfillment_status'] = fulfillment_status
        if created_at_min:
            params['created_at_min'] = created_at_min.isoformat()
        if created_at_max:
            params['created_at_max'] = created_at_max.isoformat()
        
        response = self._make_request('GET', '/orders.json', params=params)
        data = self._get_json_response(response)
        
        orders = [ShopifyOrder(**order) for order in data['orders']]
        
        # Extract pagination info
        link_header = response.headers.get('Link', '')
        next_page_info = None
        
        if 'rel="next"' in link_header:
            import re
            next_match = re.search(r'<[^>]*page_info=([^&>]+)[^>]*>; rel="next"', link_header)
            if next_match:
                next_page_info = next_match.group(1)
        
        return {
            'orders': orders,
            'has_next': next_page_info is not None,
            'next_page_info': next_page_info
        }
    
    def get_order(self, order_id: int) -> ShopifyOrder:
        """Get a specific order"""
        response = self._make_request('GET', f'/orders/{order_id}.json')
        data = self._get_json_response(response)
        return ShopifyOrder(**data['order'])
    
    def get_order_preview(self, order_id: int) -> OrderPreview:
        """Get order preview with upload links and custom design data"""
        order = self.get_order(order_id)
        
        preview_items = []
        has_uploads = False
        total_items_with_uploads = 0
        
        for line_item in order.line_items:
            upload_url = None
            preview_image_url = None
            custom_design_data = None
            
            # Check line item properties for upload links and custom data
            for prop in line_item.properties:
                if prop.get('name') == 'upload_url':
                    upload_url = prop.get('value')
                    has_uploads = True
                    total_items_with_uploads += 1
                elif prop.get('name') == 'preview_image':
                    preview_image_url = prop.get('value')
                elif prop.get('name') == 'custom_design':
                    try:
                        custom_design_data = json.loads(prop.get('value', '{}'))
                    except:
                        pass
            
            preview_items.append(OrderPreviewItem(
                line_item_id=line_item.id,
                product_title=line_item.title,
                variant_title=line_item.variant_title,
                quantity=line_item.quantity,
                upload_url=upload_url,
                preview_image_url=preview_image_url,
                custom_design_data=custom_design_data,
                mockup_urls=[],  # Could be populated from custom design data
                processing_status='pending' if upload_url else 'completed'
            ))
        
        return OrderPreview(
            order_id=order.id,
            order_name=order.name,
            customer_email=order.email,
            created_at=order.created_at,
            items=preview_items,
            has_uploads=has_uploads,
            preview_ready=all(item.processing_status == 'completed' for item in preview_items),
            total_items_with_uploads=total_items_with_uploads
        )
    
    # Collection Methods
    
    def get_collections(self, collection_type: str = 'all') -> List[Union[ShopifyCollection, ShopifySmartCollection, ShopifyCustomCollection]]:
        """Get collections (smart and custom)"""
        collections = []
        
        if collection_type in ['all', 'smart']:
            response = self._make_request('GET', '/smart_collections.json')
            data = self._get_json_response(response)
            collections.extend([ShopifySmartCollection(**col) for col in data['smart_collections']])
        
        if collection_type in ['all', 'custom']:
            response = self._make_request('GET', '/custom_collections.json')
            data = self._get_json_response(response)
            collections.extend([ShopifyCustomCollection(**col) for col in data['custom_collections']])
        
        return collections
    
    def create_collection(self, collection_data: ShopifyCollectionCreate) -> Union[ShopifySmartCollection, ShopifyCustomCollection]:
        """Create a new collection"""
        if collection_data.rules:
            # Smart collection
            data = {
                'smart_collection': {
                    **collection_data.model_dump(exclude_none=True, exclude={'rules', 'disjunctive'}),
                    'rules': [rule.model_dump() for rule in collection_data.rules],
                    'disjunctive': collection_data.disjunctive
                }
            }
            response = self._make_request('POST', '/smart_collections.json', data=data)
            result = self._get_json_response(response)
            return ShopifySmartCollection(**result['smart_collection'])
        else:
            # Custom collection
            data = {'custom_collection': collection_data.model_dump(exclude_none=True, exclude={'rules', 'disjunctive'})}
            response = self._make_request('POST', '/custom_collections.json', data=data)
            result = self._get_json_response(response)
            return ShopifyCustomCollection(**result['custom_collection'])
    
    # Customer Methods
    
    def get_customers(self, limit: int = 50, page_info: Optional[str] = None) -> Dict[str, Any]:
        """Get customers with pagination"""
        params = {'limit': min(limit, 250)}
        
        if page_info:
            params['page_info'] = page_info
        
        response = self._make_request('GET', '/customers.json', params=params)
        data = self._get_json_response(response)
        
        customers = [ShopifyCustomer(**customer) for customer in data['customers']]
        
        return {
            'customers': customers,
            'has_next': 'Link' in response.headers and 'rel="next"' in response.headers['Link']
        }
    
    def get_customer(self, customer_id: int) -> ShopifyCustomer:
        """Get a specific customer"""
        response = self._make_request('GET', f'/customers/{customer_id}.json')
        data = self._get_json_response(response)
        return ShopifyCustomer(**data['customer'])
    
    # Utility Methods
    
    def test_connection(self) -> bool:
        """Test the API connection"""
        try:
            self.get_shop_info()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_api_usage(self) -> Dict[str, Any]:
        """Get API usage information"""
        return {
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset_time': self.rate_limit_reset_time,
            'user_id': self.user_id,
            'shop_domain': self.shop_domain
        }