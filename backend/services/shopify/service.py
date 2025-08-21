from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import logging
import json
import uuid as uuid_lib

from .models import (
    ShopifyOAuthInitRequest, ShopifyOAuthInitResponse, ShopifyOAuthCallbackRequest,
    ShopifyTokenResponse, ShopifyShop, ShopifyProduct, ShopifyProductCreate,
    ShopifyProductUpdate, ShopifyOrder, ShopifyCustomer, ShopifyCollection,
    ShopifyCollectionCreate, ShopifyBatchOperation, ShopifyBatchResult,
    OrderPreview, ShopifyDashboardData, ShopifyShopStats, ShopifyIntegrationStatus,
    ShopifySyncRequest, ShopifySyncResponse
)
from .client import ShopifyAPIClient
from database.entities import User, Order, ThirdPartyOAuthToken, ShopifyProductTemplate
from common.database import DatabaseManager
from common.exceptions import (
    UserNotFound, ShopifyAPIError, ShopifyAuthenticationError,
    DatabaseError, ValidationError
)

logger = logging.getLogger(__name__)

class ShopifyService:
    """Service for managing Shopify integration and data synchronization"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.client = ShopifyAPIClient()
    
    def _get_user_client(self, user_id: UUID) -> ShopifyAPIClient:
        """Get authenticated Shopify client for user"""
        user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            raise UserNotFound(user_id)
        
        # Get Shopify OAuth token
        token = self.db.query(ThirdPartyOAuthToken).filter(
            ThirdPartyOAuthToken.user_id == user_id,
            ThirdPartyOAuthToken.platform == 'shopify',
            ThirdPartyOAuthToken.is_active == True
        ).first()
        
        if not token:
            raise ShopifyAuthenticationError("Shopify not connected for this user")
        
        if token.expires_at and token.expires_at <= datetime.now(timezone.utc):
            raise ShopifyAuthenticationError("Shopify token has expired")
        
        client = ShopifyAPIClient(user_id=str(user_id), tenant_id=self.db.tenant_id)
        client.set_credentials(token.access_token, token.shop_domain)
        
        return client
    
    # OAuth Methods
    
    def initiate_oauth_flow(self, oauth_request: ShopifyOAuthInitRequest, user_id: UUID) -> ShopifyOAuthInitResponse:
        """Initiate OAuth flow for Shopify"""
        try:
            # Validate user exists
            user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                raise UserNotFound(user_id)
            
            # Generate state for CSRF protection
            state = str(uuid_lib.uuid4())
            
            # Store state in session/cache (in production, use Redis)
            # For now, we'll store it in the database temporarily
            existing_token = self.db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id,
                ThirdPartyOAuthToken.platform == 'shopify'
            ).first()
            
            if existing_token:
                existing_token.oauth_state = state
                existing_token.updated_at = datetime.now(timezone.utc)
            else:
                oauth_token = ThirdPartyOAuthToken(
                    user_id=user_id,
                    platform='shopify',
                    oauth_state=state,
                    shop_domain=oauth_request.shop_domain,
                    is_active=False  # Will be activated after successful OAuth
                )
                self.db.add(oauth_token)
            
            self.db.commit()
            
            # Generate OAuth URL
            return self.client.generate_oauth_url(
                shop_domain=oauth_request.shop_domain,
                redirect_uri=oauth_request.redirect_uri,
                state=state
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error initiating Shopify OAuth for user {user_id}: {str(e)}")
            raise ShopifyAPIError(f"Failed to initiate OAuth flow: {str(e)}")
    
    def handle_oauth_callback(self, callback_data: ShopifyOAuthCallbackRequest, user_id: UUID) -> ShopifyTokenResponse:
        """Handle OAuth callback and exchange code for token"""
        try:
            # Validate state parameter
            stored_token = self.db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id,
                ThirdPartyOAuthToken.platform == 'shopify',
                ThirdPartyOAuthToken.oauth_state == callback_data.state
            ).first()
            
            if not stored_token:
                raise ShopifyAuthenticationError("Invalid state parameter")
            
            # Exchange code for token
            token_response = self.client.exchange_code_for_token(callback_data)
            
            # Update database with new token
            stored_token.access_token = token_response.access_token
            stored_token.refresh_token = None  # Shopify doesn't use refresh tokens
            stored_token.expires_at = None  # Shopify tokens don't expire
            stored_token.scopes = token_response.scope
            stored_token.shop_domain = token_response.shop_domain
            stored_token.is_active = True
            stored_token.oauth_state = None  # Clear state
            stored_token.updated_at = datetime.now(timezone.utc)
            
            self.db.commit()
            
            logger.info(f"Successfully connected Shopify for user {user_id}")
            return token_response
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error handling Shopify OAuth callback for user {user_id}: {str(e)}")
            raise ShopifyAPIError(f"OAuth callback failed: {str(e)}")
    
    def disconnect_shopify(self, user_id: UUID) -> bool:
        """Disconnect Shopify integration"""
        try:
            token = self.db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id,
                ThirdPartyOAuthToken.platform == 'shopify'
            ).first()
            
            if token:
                token.is_active = False
                token.access_token = None
                token.updated_at = datetime.now(timezone.utc)
                self.db.commit()
            
            logger.info(f"Disconnected Shopify for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error disconnecting Shopify for user {user_id}: {str(e)}")
            return False
    
    def get_integration_status(self, user_id: UUID) -> ShopifyIntegrationStatus:
        """Get Shopify integration status for user"""
        try:
            token = self.db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id,
                ThirdPartyOAuthToken.platform == 'shopify'
            ).first()
            
            if not token or not token.is_active:
                return ShopifyIntegrationStatus(
                    user_id=user_id,
                    tenant_id=self.db.tenant_id,
                    is_connected=False,
                    sync_status="not_connected"
                )
            
            # Test connection
            error_message = None
            shop_name = None
            
            try:
                client = self._get_user_client(user_id)
                shop_info = client.get_shop_info()
                shop_name = shop_info.name
            except Exception as e:
                error_message = str(e)
            
            return ShopifyIntegrationStatus(
                user_id=user_id,
                tenant_id=self.db.tenant_id,
                is_connected=token.is_active and error_message is None,
                shop_domain=token.shop_domain,
                shop_name=shop_name,
                last_sync=token.last_sync_at,
                sync_status="connected" if error_message is None else "error",
                error_message=error_message,
                permissions=token.scopes.split(',') if token.scopes else []
            )
            
        except Exception as e:
            logger.error(f"Error getting Shopify integration status for user {user_id}: {str(e)}")
            return ShopifyIntegrationStatus(
                user_id=user_id,
                tenant_id=self.db.tenant_id,
                is_connected=False,
                sync_status="error",
                error_message=str(e)
            )
    
    # Shop Methods
    
    def get_shop_info(self, user_id: UUID) -> ShopifyShop:
        """Get shop information"""
        client = self._get_user_client(user_id)
        return client.get_shop_info()
    
    # Product Methods
    
    def get_products(
        self,
        user_id: UUID,
        limit: int = 50,
        page_info: Optional[str] = None,
        status: Optional[str] = None,
        product_type: Optional[str] = None,
        vendor: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get products with pagination"""
        client = self._get_user_client(user_id)
        return client.get_products(
            limit=limit,
            page_info=page_info,
            status=status,
            product_type=product_type,
            vendor=vendor
        )
    
    def get_product(self, user_id: UUID, product_id: int) -> ShopifyProduct:
        """Get a specific product"""
        client = self._get_user_client(user_id)
        return client.get_product(product_id)
    
    def create_product(self, user_id: UUID, product_data: ShopifyProductCreate) -> ShopifyProduct:
        """Create a new product"""
        client = self._get_user_client(user_id)
        return client.create_product(product_data)
    
    def update_product(self, user_id: UUID, product_id: int, product_data: ShopifyProductUpdate) -> ShopifyProduct:
        """Update an existing product"""
        client = self._get_user_client(user_id)
        return client.update_product(product_id, product_data)
    
    def delete_product(self, user_id: UUID, product_id: int) -> bool:
        """Delete a product"""
        client = self._get_user_client(user_id)
        return client.delete_product(product_id)
    
    def batch_update_products(self, user_id: UUID, batch_operation: ShopifyBatchOperation) -> ShopifyBatchResult:
        """Perform batch operations on products"""
        client = self._get_user_client(user_id)
        return client.batch_update_products(batch_operation)
    
    # Order Methods
    
    def get_orders(
        self,
        user_id: UUID,
        limit: int = 50,
        page_info: Optional[str] = None,
        status: Optional[str] = None,
        financial_status: Optional[str] = None,
        fulfillment_status: Optional[str] = None,
        created_at_min: Optional[datetime] = None,
        created_at_max: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get orders with pagination and filtering"""
        client = self._get_user_client(user_id)
        return client.get_orders(
            limit=limit,
            page_info=page_info,
            status=status,
            financial_status=financial_status,
            fulfillment_status=fulfillment_status,
            created_at_min=created_at_min,
            created_at_max=created_at_max
        )
    
    def get_order(self, user_id: UUID, order_id: int) -> ShopifyOrder:
        """Get a specific order"""
        client = self._get_user_client(user_id)
        return client.get_order(order_id)
    
    def get_order_preview(self, user_id: UUID, order_id: int) -> OrderPreview:
        """Get order preview with upload links and custom design data"""
        client = self._get_user_client(user_id)
        return client.get_order_preview(order_id)
    
    def sync_order_from_shopify_order(self, user_id: UUID, shopify_order_data: Dict[str, Any]) -> 'OrderResponse':
        """Convert Shopify order to internal order format"""
        from services.order.service import OrderService
        from services.order.models import OrderCreate
        
        order_service = OrderService(self.db)
        
        # Map Shopify order to internal order format
        order_data = OrderCreate(
            customer_email=shopify_order_data.get('email', ''),
            customer_name=f"{shopify_order_data.get('billing_address', {}).get('first_name', '')} {shopify_order_data.get('billing_address', {}).get('last_name', '')}".strip(),
            total_amount=Decimal(str(shopify_order_data.get('total_price', '0'))),
            status='pending',
            platform='shopify',
            platform_order_id=str(shopify_order_data.get('id', '')),
            shipping_address=shopify_order_data.get('shipping_address', {}),
            billing_address=shopify_order_data.get('billing_address', {}),
            items=[{
                'name': item.get('title', ''),
                'quantity': item.get('quantity', 1),
                'price': Decimal(str(item.get('price', '0'))),
                'sku': item.get('sku', ''),
                'variant_id': item.get('variant_id')
            } for item in shopify_order_data.get('line_items', [])],
            metadata={
                'shopify_order_number': shopify_order_data.get('order_number'),
                'shopify_financial_status': shopify_order_data.get('financial_status'),
                'shopify_fulfillment_status': shopify_order_data.get('fulfillment_status'),
                'shopify_order_created_at': shopify_order_data.get('created_at')
            }
        )
        
        return order_service.create_order(user_id, order_data)
    
    # Collection Methods
    
    def get_collections(self, user_id: UUID, collection_type: str = 'all') -> List[ShopifyCollection]:
        """Get collections"""
        client = self._get_user_client(user_id)
        return client.get_collections(collection_type)
    
    def create_collection(self, user_id: UUID, collection_data: ShopifyCollectionCreate) -> ShopifyCollection:
        """Create a new collection"""
        client = self._get_user_client(user_id)
        return client.create_collection(collection_data)
    
    # Customer Methods
    
    def get_customers(self, user_id: UUID, limit: int = 50, page_info: Optional[str] = None) -> Dict[str, Any]:
        """Get customers with pagination"""
        client = self._get_user_client(user_id)
        return client.get_customers(limit, page_info)
    
    def get_customer(self, user_id: UUID, customer_id: int) -> ShopifyCustomer:
        """Get a specific customer"""
        client = self._get_user_client(user_id)
        return client.get_customer(customer_id)
    
    # Sync Methods
    
    def sync_data(self, user_id: UUID, sync_request: ShopifySyncRequest) -> ShopifySyncResponse:
        """Sync data from Shopify"""
        sync_id = str(uuid_lib.uuid4())
        started_at = datetime.now(timezone.utc)
        
        try:
            client = self._get_user_client(user_id)
            
            records_processed = 0
            records_updated = 0
            records_created = 0
            errors = []
            
            if sync_request.sync_type in ['orders', 'all']:
                try:
                    # Sync orders
                    order_params = {}
                    if sync_request.date_range_start:
                        order_params['created_at_min'] = sync_request.date_range_start
                    if sync_request.date_range_end:
                        order_params['created_at_max'] = sync_request.date_range_end
                    
                    orders_data = client.get_orders(**order_params)
                    
                    for shopify_order in orders_data['orders']:
                        try:
                            self.sync_order_from_shopify_order(user_id, shopify_order.model_dump())
                            records_processed += 1
                            records_created += 1
                        except Exception as e:
                            errors.append(f"Order {shopify_order.id}: {str(e)}")
                            
                except Exception as e:
                    errors.append(f"Order sync failed: {str(e)}")
            
            if sync_request.sync_type in ['products', 'all']:
                try:
                    # Sync products (basic sync - could be enhanced)
                    products_data = client.get_products()
                    records_processed += len(products_data['products'])
                    
                except Exception as e:
                    errors.append(f"Product sync failed: {str(e)}")
            
            # Update last sync time
            token = self.db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id,
                ThirdPartyOAuthToken.platform == 'shopify'
            ).first()
            
            if token:
                token.last_sync_at = datetime.now(timezone.utc)
                self.db.commit()
            
            return ShopifySyncResponse(
                sync_id=sync_id,
                status='completed' if not errors else 'completed_with_errors',
                sync_type=sync_request.sync_type,
                records_processed=records_processed,
                records_updated=records_updated,
                records_created=records_created,
                errors=errors,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                message=f"Sync completed. Processed {records_processed} records."
            )
            
        except Exception as e:
            logger.error(f"Sync failed for user {user_id}: {str(e)}")
            return ShopifySyncResponse(
                sync_id=sync_id,
                status='error',
                sync_type=sync_request.sync_type,
                errors=[str(e)],
                started_at=started_at,
                message=f"Sync failed: {str(e)}"
            )
    
    # Dashboard Methods
    
    def get_dashboard_data(self, user_id: UUID) -> ShopifyDashboardData:
        """Get dashboard data from Shopify"""
        try:
            client = self._get_user_client(user_id)
            
            # Get shop info
            shop_info = client.get_shop_info()
            
            # Get recent orders
            orders_data = client.get_orders(limit=10)
            recent_orders = orders_data['orders']
            
            # Get recent products
            products_data = client.get_products(limit=10)
            recent_products = products_data['products']
            
            # Get pending orders
            pending_orders_data = client.get_orders(
                financial_status='pending',
                limit=20
            )
            pending_orders = pending_orders_data['orders']
            
            # Get collections
            collections = client.get_collections()
            
            # Calculate stats
            total_orders_data = client.get_orders(limit=1)  # Just to get count info
            total_products_data = client.get_products(limit=1)
            
            # Calculate revenue (this is simplified - in production you'd aggregate properly)
            total_revenue = sum(order.total_price for order in recent_orders)
            
            # Get low stock products (simplified)
            low_stock_products = [p for p in recent_products if any(
                v.inventory_quantity < 10 for v in p.variants
            )]
            
            shop_stats = ShopifyShopStats(
                total_products=len(recent_products),  # Simplified
                published_products=len([p for p in recent_products if p.status == 'active']),
                draft_products=len([p for p in recent_products if p.status == 'draft']),
                total_orders=len(recent_orders),  # Simplified
                total_customers=0,  # Would need separate API call
                total_revenue=Decimal(str(total_revenue)),
                orders_this_month=len([o for o in recent_orders if o.created_at.month == datetime.now().month]),
                revenue_this_month=Decimal(str(sum(
                    order.total_price for order in recent_orders 
                    if order.created_at.month == datetime.now().month
                ))),
                average_order_value=Decimal(str(total_revenue / len(recent_orders))) if recent_orders else Decimal('0'),
                total_collections=len(collections),
                pending_orders=len(pending_orders)
            )
            
            return ShopifyDashboardData(
                shop_info=shop_info,
                shop_stats=shop_stats,
                recent_orders=recent_orders,
                recent_products=recent_products,
                pending_orders=pending_orders,
                low_stock_products=low_stock_products,
                collections=collections
            )
            
        except Exception as e:
            logger.error(f"Error getting Shopify dashboard data for user {user_id}: {str(e)}")
            raise ShopifyAPIError(f"Failed to get dashboard data: {str(e)}")
    
    # Template Methods
    
    def create_listing_from_template(self, user_id: UUID, template_id: UUID, customizations: Optional[Dict[str, Any]] = None) -> ShopifyProduct:
        """Create Shopify product from template"""
        try:
            # Get template
            template = self.db.query(ShopifyProductTemplate).filter(
                ShopifyProductTemplate.id == template_id,
                ShopifyProductTemplate.user_id == user_id,
                ShopifyProductTemplate.is_deleted == False
            ).first()
            
            if not template:
                raise ValidationError("Template not found")
            
            # Apply customizations
            product_data = template.template_data.copy()
            if customizations:
                product_data.update(customizations)
            
            # Create product
            product_create = ShopifyProductCreate(**product_data)
            return self.create_product(user_id, product_create)
            
        except Exception as e:
            logger.error(f"Error creating listing from template {template_id} for user {user_id}: {str(e)}")
            raise ShopifyAPIError(f"Failed to create listing from template: {str(e)}")
    
    # Utility Methods
    
    def test_connection(self, user_id: UUID) -> bool:
        """Test Shopify connection"""
        try:
            client = self._get_user_client(user_id)
            return client.test_connection()
        except Exception:
            return False