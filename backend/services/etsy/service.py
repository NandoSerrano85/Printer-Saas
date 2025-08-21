from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, timezone, timedelta
import logging
import asyncio
from decimal import Decimal

from .client import EtsyAPIClient
from .models import (
    EtsyOAuthInitResponse, EtsyTokenResponse, EtsyIntegrationStatus,
    EtsyDashboardData, EtsyShopStats, EtsySyncRequest, EtsySyncResponse,
    EtsyShop, EtsyUser, EtsyListing, EtsyReceipt, EtsyTransaction,
    EtsyTaxonomy, EtsyShippingProfile, EtsyShopSection
)
from database.entities import User, ThirdPartyOAuthToken, Order, OrderItem, EtsyProductTemplate
from common.exceptions import (
    EtsyAPIError, EtsyAuthError, UserNotFound, ValidationError
)
from common.database import DatabaseManager

logger = logging.getLogger(__name__)

class EtsyService:
    """Comprehensive Etsy integration service for multi-tenant SaaS"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.client = EtsyAPIClient(tenant_id=db_manager.tenant_id)
    
    # OAuth and Authentication Methods
    
    def initiate_oauth_flow(self, user_id: UUID, redirect_uri: str) -> EtsyOAuthInitResponse:
        """Initiate OAuth flow for user"""
        try:
            # Validate user exists
            user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                raise UserNotFound(user_id)
            
            # Generate OAuth data
            oauth_data = self.client.generate_oauth_data(redirect_uri)
            
            # Store state and code_verifier temporarily (in production, use Redis)
            # For now, we'll store in database or cache
            
            logger.info(f"OAuth flow initiated for user {user_id}")
            return oauth_data
            
        except Exception as e:
            logger.error(f"Error initiating OAuth flow for user {user_id}: {str(e)}")
            raise EtsyAuthError(f"Failed to initiate OAuth flow: {str(e)}")
    
    def complete_oauth_flow(self, user_id: UUID, code: str, code_verifier: str, 
                           state: str, redirect_uri: str) -> EtsyTokenResponse:
        """Complete OAuth flow and store tokens"""
        try:
            # Validate user exists
            user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                raise UserNotFound(user_id)
            
            # Exchange code for token
            token_response = self.client.exchange_code_for_token(code, code_verifier, redirect_uri)
            
            # Set client credentials for subsequent API calls
            self.client.set_credentials(
                access_token=token_response.access_token,
                refresh_token=token_response.refresh_token,
                expires_at=token_response.expires_at
            )
            
            # Get user's shop information
            try:
                user_shops = self.client.get_user_shops()
                shop_id = user_shops[0].shop_id if user_shops else None
                self.client.shop_id = shop_id
            except Exception as e:
                logger.warning(f"Could not get shop info during OAuth: {e}")
                shop_id = None
            
            # Store or update OAuth token in database
            existing_token = self.db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id,
                ThirdPartyOAuthToken.provider == 'etsy'
            ).first()
            
            if existing_token:
                # Update existing token
                existing_token.access_token = token_response.access_token
                existing_token.refresh_token = token_response.refresh_token
                existing_token.expires_at = token_response.expires_at
                existing_token.updated_at = datetime.now(timezone.utc)
            else:
                # Create new token record
                new_token = ThirdPartyOAuthToken(
                    tenant_id=self.db.tenant_id,
                    user_id=user_id,
                    provider='etsy',
                    access_token=token_response.access_token,
                    refresh_token=token_response.refresh_token,
                    expires_at=token_response.expires_at,
                    scope='listings_w listings_r shops_r shops_w transactions_r',
                    metadata={'shop_id': shop_id} if shop_id else {},
                    created_by=user_id
                )
                self.db.add(new_token)
            
            self.db.commit()
            
            logger.info(f"OAuth flow completed for user {user_id}, shop_id: {shop_id}")
            return token_response
            
        except Exception as e:
            logger.error(f"Error completing OAuth flow for user {user_id}: {str(e)}")
            self.db.rollback()
            raise EtsyAuthError(f"Failed to complete OAuth flow: {str(e)}")
    
    def get_integration_status(self, user_id: UUID) -> EtsyIntegrationStatus:
        """Get Etsy integration status for user"""
        try:
            # Get OAuth token
            token = self.db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id,
                ThirdPartyOAuthToken.provider == 'etsy'
            ).first()
            
            if not token:
                return EtsyIntegrationStatus(
                    user_id=user_id,
                    tenant_id=self.db.tenant_id,
                    is_connected=False
                )
            
            # Check if token is valid
            is_connected = True
            error_message = None
            
            try:
                # Set up client with stored credentials
                self.client.set_credentials(
                    access_token=token.access_token,
                    refresh_token=token.refresh_token,
                    expires_at=token.expires_at
                )
                
                # Test the token
                if not self.client.test_token():
                    is_connected = False
                    error_message = "Token validation failed"
                    
            except Exception as e:
                is_connected = False
                error_message = str(e)
            
            # Get shop info if connected
            shop_id = None
            shop_name = None
            if is_connected and token.metadata:
                shop_id = token.metadata.get('shop_id')
                shop_name = token.metadata.get('shop_name')
            
            return EtsyIntegrationStatus(
                user_id=user_id,
                tenant_id=self.db.tenant_id,
                is_connected=is_connected,
                shop_id=shop_id,
                shop_name=shop_name,
                token_expires_at=token.expires_at,
                last_sync=token.updated_at,
                sync_status="connected" if is_connected else "error",
                error_message=error_message,
                permissions=token.scope.split() if token.scope else []
            )
            
        except Exception as e:
            logger.error(f"Error getting integration status for user {user_id}: {str(e)}")
            return EtsyIntegrationStatus(
                user_id=user_id,
                tenant_id=self.db.tenant_id,
                is_connected=False,
                error_message=str(e)
            )
    
    def disconnect_etsy(self, user_id: UUID) -> bool:
        """Disconnect Etsy integration for user"""
        try:
            # Remove OAuth token
            token = self.db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id,
                ThirdPartyOAuthToken.provider == 'etsy'
            ).first()
            
            if token:
                self.db.delete(token)
                self.db.commit()
                logger.info(f"Disconnected Etsy integration for user {user_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting Etsy for user {user_id}: {str(e)}")
            self.db.rollback()
            return False
    
    # API Data Methods
    
    def _setup_client_for_user(self, user_id: UUID) -> bool:
        """Set up Etsy client with user's credentials"""
        token = self.db.query(ThirdPartyOAuthToken).filter(
            ThirdPartyOAuthToken.user_id == user_id,
            ThirdPartyOAuthToken.provider == 'etsy'
        ).first()
        
        if not token:
            raise EtsyAuthError("User not connected to Etsy")
        
        self.client.set_credentials(
            access_token=token.access_token,
            refresh_token=token.refresh_token,
            expires_at=token.expires_at,
            shop_id=token.metadata.get('shop_id') if token.metadata else None
        )
        
        return True
    
    def get_shop_info(self, user_id: UUID) -> EtsyShop:
        """Get shop information for user"""
        self._setup_client_for_user(user_id)
        return self.client.get_shop()
    
    def get_user_info(self, user_id: UUID) -> EtsyUser:
        """Get Etsy user information"""
        self._setup_client_for_user(user_id)
        return self.client.get_current_user()
    
    def get_taxonomies(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get Etsy taxonomies for user"""
        self._setup_client_for_user(user_id)
        return self.client.get_flat_taxonomy()
    
    def get_shipping_profiles(self, user_id: UUID) -> List[EtsyShippingProfile]:
        """Get shipping profiles for user's shop"""
        self._setup_client_for_user(user_id)
        return self.client.get_shipping_profiles()
    
    def get_shop_sections(self, user_id: UUID) -> List[EtsyShopSection]:
        """Get shop sections for user's shop"""
        self._setup_client_for_user(user_id)
        return self.client.get_shop_sections()
    
    # Listing Management
    
    def get_shop_listings(self, user_id: UUID, state: str = "active", 
                         limit: int = 100, offset: int = 0) -> List[EtsyListing]:
        """Get shop listings"""
        self._setup_client_for_user(user_id)
        return self.client.get_shop_listings(state=state, limit=limit, offset=offset)
    
    def create_listing_from_template(self, user_id: UUID, template_id: UUID, 
                                   custom_data: Optional[Dict[str, Any]] = None) -> EtsyListing:
        """Create Etsy listing from internal template"""
        try:
            # Get template
            template = self.db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.id == template_id,
                EtsyProductTemplate.user_id == user_id,
                EtsyProductTemplate.is_deleted == False
            ).first()
            
            if not template:
                raise ValidationError(f"Template {template_id} not found")
            
            self._setup_client_for_user(user_id)
            
            # Build listing data from template
            listing_data = {
                'quantity': template.quantity or 1,
                'title': template.title or template.name,
                'description': template.description or "",
                'price': float(template.price) if template.price else 10.0,
                'who_made': template.who_made or 'i_did',
                'when_made': template.when_made or 'made_to_order',
                'taxonomy_id': template.taxonomy_id,
                'shipping_profile_id': template.shipping_profile_id,
                'return_policy_id': template.return_policy_id,
                'processing_min': template.processing_min or 1,
                'processing_max': template.processing_max or 3,
                'is_taxable': template.is_taxable if template.is_taxable is not None else True,
                'type': template.type or 'physical'
            }
            
            # Add materials and tags
            if template.materials:
                materials = template.materials.split(',') if isinstance(template.materials, str) else template.materials
                listing_data['materials'] = [m.strip() for m in materials if m.strip()][:13]
            
            if template.tags:
                tags = template.tags.split(',') if isinstance(template.tags, str) else template.tags
                listing_data['tags'] = [t.strip() for t in tags if t.strip()][:13]
            
            # Add shop section
            if template.shop_section_id:
                listing_data['shop_section_id'] = template.shop_section_id
            
            # Add dimensions
            if template.item_weight:
                listing_data['item_weight'] = float(template.item_weight)
            if template.item_length:
                listing_data['item_length'] = float(template.item_length)
            if template.item_width:
                listing_data['item_width'] = float(template.item_width)
            if template.item_height:
                listing_data['item_height'] = float(template.item_height)
            if template.item_dimensions_unit:
                listing_data['item_dimensions_unit'] = template.item_dimensions_unit
            
            # Apply custom overrides
            if custom_data:
                listing_data.update(custom_data)
            
            # Create the listing
            listing = self.client.create_draft_listing(listing_data)
            
            logger.info(f"Created Etsy listing {listing.listing_id} from template {template_id}")
            return listing
            
        except Exception as e:
            logger.error(f"Error creating listing from template {template_id}: {str(e)}")
            raise EtsyAPIError(f"Failed to create listing: {str(e)}")
    
    # Order Management
    
    def get_shop_orders(self, user_id: UUID, was_paid: bool = True, 
                       was_shipped: Optional[bool] = None, limit: int = 100, 
                       offset: int = 0) -> List[EtsyReceipt]:
        """Get shop orders (receipts)"""
        self._setup_client_for_user(user_id)
        return self.client.get_shop_receipts(
            was_paid=was_paid, 
            was_shipped=was_shipped, 
            limit=limit, 
            offset=offset
        )
    
    def sync_orders_to_internal(self, user_id: UUID, limit: int = 50) -> Dict[str, int]:
        """Sync Etsy orders to internal order system"""
        try:
            self._setup_client_for_user(user_id)
            
            # Get recent orders from Etsy
            etsy_receipts = self.client.get_shop_receipts(limit=limit)
            
            synced_count = 0
            updated_count = 0
            
            for receipt in etsy_receipts:
                # Check if order already exists
                existing_order = self.db.query(Order).filter(
                    Order.user_id == user_id,
                    Order.etsy_receipt_id == receipt.receipt_id
                ).first()
                
                if existing_order:
                    # Update existing order
                    existing_order.status = self._map_etsy_status_to_internal(receipt)
                    existing_order.updated_at = datetime.now(timezone.utc)
                    updated_count += 1
                else:
                    # Create new order
                    order = Order(
                        tenant_id=self.db.tenant_id,
                        user_id=user_id,
                        etsy_receipt_id=receipt.receipt_id,
                        etsy_order_id=receipt.order_id,
                        platform='etsy',
                        order_number=str(receipt.receipt_id),
                        status=self._map_etsy_status_to_internal(receipt),
                        total_amount=Decimal(str(receipt.grandtotal.get('amount', 0))) if receipt.grandtotal else Decimal('0'),
                        currency=receipt.grandtotal.get('currency_code', 'USD') if receipt.grandtotal else 'USD',
                        customer_email=receipt.payment_email,
                        customer_name=receipt.name,
                        shipping_address=self._format_shipping_address(receipt),
                        order_date=receipt.creation_timestamp,
                        processing_notes=receipt.message_from_buyer,
                        created_by=user_id
                    )
                    self.db.add(order)
                    self.db.flush()  # Get order ID
                    
                    # Get and create order items
                    try:
                        transactions = self.client.get_receipt_transactions(receipt.receipt_id)
                        for transaction in transactions:
                            order_item = OrderItem(
                                tenant_id=self.db.tenant_id,
                                user_id=user_id,
                                order_id=order.id,
                                etsy_listing_id=transaction.listing_id,
                                product_name=transaction.title,
                                quantity=transaction.quantity,
                                unit_price=Decimal(str(transaction.price.get('amount', 0))) if transaction.price else Decimal('0'),
                                total_price=Decimal(str(transaction.price.get('amount', 0))) * transaction.quantity if transaction.price else Decimal('0'),
                                customization_text=transaction.personalization,
                                created_by=user_id
                            )
                            self.db.add(order_item)
                    except Exception as e:
                        logger.warning(f"Could not sync transactions for receipt {receipt.receipt_id}: {e}")
                    
                    synced_count += 1
            
            self.db.commit()
            
            logger.info(f"Synced {synced_count} new orders and updated {updated_count} orders for user {user_id}")
            return {'synced': synced_count, 'updated': updated_count}
            
        except Exception as e:
            logger.error(f"Error syncing orders for user {user_id}: {str(e)}")
            self.db.rollback()
            raise EtsyAPIError(f"Failed to sync orders: {str(e)}")
    
    # Dashboard Data
    
    def get_dashboard_data(self, user_id: UUID) -> EtsyDashboardData:
        """Get comprehensive dashboard data from Etsy"""
        try:
            self._setup_client_for_user(user_id)
            
            # Get basic info
            shop_info = self.client.get_shop()
            user_info = self.client.get_current_user()
            
            # Get recent data
            recent_orders = self.client.get_shop_receipts(limit=10)
            recent_listings = self.client.get_shop_listings(limit=10)
            
            # Get pending orders (not shipped)
            pending_orders = self.client.get_shop_receipts(was_paid=True, was_shipped=False, limit=20)
            
            # Calculate stats
            total_revenue = sum(
                float(receipt.grandtotal.get('amount', 0)) if receipt.grandtotal else 0
                for receipt in recent_orders
            )
            
            # Get orders from this month
            month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            orders_this_month = [
                order for order in recent_orders 
                if order.creation_timestamp >= month_start
            ]
            
            revenue_this_month = sum(
                float(receipt.grandtotal.get('amount', 0)) if receipt.grandtotal else 0
                for receipt in orders_this_month
            )
            
            avg_order_value = Decimal(str(total_revenue / len(recent_orders))) if recent_orders else Decimal('0')
            
            shop_stats = EtsyShopStats(
                total_listings=shop_info.listing_active_count,
                active_listings=shop_info.listing_active_count,
                total_orders=len(recent_orders),
                total_revenue=Decimal(str(total_revenue)),
                orders_this_month=len(orders_this_month),
                revenue_this_month=Decimal(str(revenue_this_month)),
                average_order_value=avg_order_value,
                shop_rating=shop_info.review_average,
                total_reviews=shop_info.review_count
            )
            
            # Find low stock listings (quantity < 5)
            low_stock_listings = [
                listing for listing in recent_listings 
                if listing.quantity < 5
            ]
            
            return EtsyDashboardData(
                shop_info=shop_info,
                user_info=user_info,
                shop_stats=shop_stats,
                recent_orders=recent_orders,
                recent_listings=recent_listings,
                pending_orders=pending_orders,
                low_stock_listings=low_stock_listings,
                last_updated=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"Error getting dashboard data for user {user_id}: {str(e)}")
            raise EtsyAPIError(f"Failed to get dashboard data: {str(e)}")
    
    # Helper Methods
    
    def _map_etsy_status_to_internal(self, receipt: EtsyReceipt) -> str:
        """Map Etsy receipt status to internal order status"""
        if not receipt.is_paid:
            return 'pending'
        elif receipt.is_shipped:
            return 'shipped'
        elif receipt.is_paid:
            return 'processing'
        else:
            return 'pending'
    
    def _format_shipping_address(self, receipt: EtsyReceipt) -> Dict[str, Any]:
        """Format Etsy receipt address to internal format"""
        return {
            'name': receipt.name,
            'line1': receipt.first_line,
            'line2': receipt.second_line,
            'city': receipt.city,
            'state': receipt.state,
            'zip': receipt.zip,
            'country': receipt.country_iso,
            'formatted_address': receipt.formatted_address
        }
    
    # Sync Operations
    
    def sync_data(self, user_id: UUID, sync_request: EtsySyncRequest) -> EtsySyncResponse:
        """Perform data sync based on request"""
        sync_id = f"sync_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            self._setup_client_for_user(user_id)
            
            records_processed = 0
            records_updated = 0
            records_created = 0
            errors = []
            
            if sync_request.sync_type in ['orders', 'all']:
                try:
                    order_result = self.sync_orders_to_internal(user_id, limit=100)
                    records_created += order_result['synced']
                    records_updated += order_result['updated']
                    records_processed += order_result['synced'] + order_result['updated']
                except Exception as e:
                    errors.append(f"Order sync error: {str(e)}")
            
            if sync_request.sync_type in ['listings', 'all']:
                try:
                    # Future: Implement listing sync
                    pass
                except Exception as e:
                    errors.append(f"Listing sync error: {str(e)}")
            
            return EtsySyncResponse(
                sync_id=sync_id,
                status='completed' if not errors else 'completed_with_errors',
                sync_type=sync_request.sync_type,
                records_processed=records_processed,
                records_updated=records_updated,
                records_created=records_created,
                errors=errors,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                message=f"Sync completed. Processed {records_processed} records."
            )
            
        except Exception as e:
            logger.error(f"Error during sync for user {user_id}: {str(e)}")
            return EtsySyncResponse(
                sync_id=sync_id,
                status='error',
                sync_type=sync_request.sync_type,
                errors=[str(e)],
                started_at=datetime.now(timezone.utc),
                message=f"Sync failed: {str(e)}"
            )