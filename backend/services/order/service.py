from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timezone
import logging
from decimal import Decimal

from .models import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderListResponse,
    OrderStatsResponse,
    OrderStatus,
    FulfillmentStatus,
    PaymentStatus,
    OrderPlatform,
    OrderNoteCreate,
    OrderNoteResponse,
    OrderFulfillmentCreate,
    OrderFulfillmentResponse,
    OrderStatusUpdateRequest,
    OrderBulkOperationRequest,
    OrderBulkOperationResponse,
    OrderItemCreate,
    OrderItemUpdate,
    OrderItemResponse
)
from database.entities import Order, OrderItem, OrderNote, OrderFulfillment, User
from common.exceptions import (
    OrderNotFound,
    OrderCreateError,
    OrderUpdateError,
    OrderDeleteError,
    UserNotFound,
    ValidationError
)
from common.database import DatabaseManager

logger = logging.getLogger(__name__)

class OrderService:
    """Service for managing orders"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_order(self, order_data: OrderCreate, user_id: UUID) -> OrderResponse:
        """Create a new order with items"""
        try:
            # Validate user exists
            user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                raise UserNotFound(user_id)
            
            # Generate internal order number if not provided
            internal_order_number = self._generate_internal_order_number()
            
            # Calculate totals from items
            items_subtotal = sum(item.total_price for item in order_data.items)
            calculated_total = items_subtotal + order_data.tax_amount + order_data.shipping_amount - order_data.discount_amount
            
            # Validate total amount
            if abs(float(order_data.total_amount) - float(calculated_total)) > 0.01:
                raise ValidationError(f"Total amount {order_data.total_amount} does not match calculated total {calculated_total}")
            
            # Create order
            db_order = Order(
                tenant_id=self.db.tenant_id,
                user_id=user_id,
                internal_order_number=internal_order_number,
                etsy_receipt_id=order_data.etsy_receipt_id,
                etsy_order_id=order_data.etsy_order_id,
                shopify_order_id=order_data.shopify_order_id,
                platform=order_data.platform.value,
                order_number=order_data.order_number,
                total_amount=order_data.total_amount,
                subtotal=order_data.subtotal or items_subtotal,
                tax_amount=order_data.tax_amount,
                shipping_amount=order_data.shipping_amount,
                discount_amount=order_data.discount_amount,
                currency=order_data.currency,
                customer_email=order_data.customer_email,
                customer_name=order_data.customer_name,
                customer_phone=order_data.customer_phone,
                customer_id=order_data.customer_id,
                billing_address=order_data.billing_address.model_dump() if order_data.billing_address else None,
                shipping_address=order_data.shipping_address.model_dump() if order_data.shipping_address else None,
                special_instructions=order_data.special_instructions,
                gift_message=order_data.gift_message,
                order_date=order_data.order_date or datetime.now(timezone.utc),
                promised_date=order_data.promised_date,
                processing_priority=order_data.processing_priority,
                processing_notes=order_data.processing_notes,
                status=OrderStatus.PENDING.value,
                fulfillment_status=FulfillmentStatus.UNFULFILLED.value,
                payment_status=PaymentStatus.PENDING.value,
                created_by=user_id
            )
            
            self.db.add(db_order)
            self.db.commit()
            self.db.refresh(db_order)
            
            # Create order items
            order_items = []
            for item_data in order_data.items:
                db_item = OrderItem(
                    tenant_id=self.db.tenant_id,
                    user_id=user_id,
                    order_id=db_order.id,
                    product_template_id=item_data.product_template_id,
                    design_id=item_data.design_id,
                    mockup_id=item_data.mockup_id,
                    product_name=item_data.product_name,
                    sku=item_data.sku,
                    variant_name=item_data.variant_name,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    total_price=item_data.total_price,
                    etsy_listing_id=item_data.etsy_listing_id,
                    etsy_product_id=item_data.etsy_product_id,
                    shopify_product_id=item_data.shopify_product_id,
                    shopify_variant_id=item_data.shopify_variant_id,
                    customization_text=item_data.customization_text,
                    customization_options=item_data.customization_options,
                    custom_design_uploaded=item_data.custom_design_uploaded,
                    production_notes=item_data.production_notes,
                    estimated_production_time=item_data.estimated_production_time,
                    created_by=user_id
                )
                self.db.add(db_item)
                order_items.append(db_item)
            
            self.db.commit()
            
            # Refresh all items
            for item in order_items:
                self.db.refresh(item)
            
            logger.info(f"Created order {db_order.id} with {len(order_items)} items for user {user_id}")
            return self._build_order_response(db_order, order_items)
            
        except (UserNotFound, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            self.db.rollback()
            raise OrderCreateError(str(e))

    def get_orders(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        platform: Optional[OrderPlatform] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> OrderListResponse:
        """Get orders for user with filtering and pagination"""
        try:
            # Base query
            query = self.db.query(Order).filter(
                Order.user_id == user_id,
                Order.is_deleted == False
            )
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Order.order_number.ilike(search_term),
                        Order.internal_order_number.ilike(search_term),
                        Order.customer_name.ilike(search_term),
                        Order.customer_email.ilike(search_term)
                    )
                )
            
            if status:
                query = query.filter(Order.status == status.value)
            
            if platform:
                query = query.filter(Order.platform == platform.value)
            
            if start_date:
                query = query.filter(Order.order_date >= start_date)
            
            if end_date:
                query = query.filter(Order.order_date <= end_date)
            
            # Apply sorting
            sort_column = getattr(Order, sort_by, Order.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            orders = query.offset(skip).limit(limit).all()
            
            # Convert to response models
            order_responses = []
            for order in orders:
                items = self.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                order_responses.append(self._build_order_response(order, items))
            
            return OrderListResponse(
                orders=order_responses,
                total_count=total_count,
                page=skip // limit + 1,
                page_size=limit,
                has_next=(skip + limit) < total_count,
                has_prev=skip > 0
            )
            
        except Exception as e:
            logger.error(f"Error getting orders: {str(e)}")
            raise OrderCreateError(f"Failed to get orders: {str(e)}")

    def get_order(self, order_id: UUID, user_id: UUID) -> OrderResponse:
        """Get order by ID"""
        order = self._get_user_order(order_id, user_id)
        items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        return self._build_order_response(order, items)

    def update_order(
        self,
        order_id: UUID,
        order_data: OrderUpdate,
        user_id: UUID
    ) -> OrderResponse:
        """Update order by ID"""
        try:
            db_order = self._get_user_order(order_id, user_id)
            
            # Update fields
            update_data = order_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field in ['billing_address', 'shipping_address'] and value is not None:
                    value = value.model_dump() if hasattr(value, 'model_dump') else value
                elif field in ['status', 'fulfillment_status', 'payment_status'] and value is not None:
                    value = value.value if hasattr(value, 'value') else value
                setattr(db_order, field, value)
            
            # Update metadata
            db_order.updated_by = user_id
            
            self.db.commit()
            self.db.refresh(db_order)
            
            # Get updated items
            items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            
            logger.info(f"Updated order {order_id} for user {user_id}")
            return self._build_order_response(db_order, items)
            
        except OrderNotFound:
            raise
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {str(e)}")
            self.db.rollback()
            raise OrderUpdateError(order_id, str(e))

    def delete_order(self, order_id: UUID, user_id: UUID) -> None:
        """Delete order by ID (soft delete)"""
        try:
            db_order = self._get_user_order(order_id, user_id)
            
            # Soft delete order and items
            db_order.is_deleted = True
            db_order.deleted_at = datetime.now(timezone.utc)
            db_order.updated_by = user_id
            
            # Soft delete all items
            items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            for item in items:
                item.is_deleted = True
                item.deleted_at = datetime.now(timezone.utc)
                item.updated_by = user_id
            
            self.db.commit()
            
            logger.info(f"Deleted order {order_id} for user {user_id}")
            
        except OrderNotFound:
            raise
        except Exception as e:
            logger.error(f"Error deleting order {order_id}: {str(e)}")
            self.db.rollback()
            raise OrderDeleteError(order_id)

    def update_order_status(
        self,
        order_id: UUID,
        status_update: OrderStatusUpdateRequest,
        user_id: UUID
    ) -> OrderResponse:
        """Update order status"""
        try:
            db_order = self._get_user_order(order_id, user_id)
            
            # Update status
            db_order.status = status_update.status.value
            db_order.updated_by = user_id
            
            # Add status change note if notes provided
            if status_update.notes:
                note = OrderNote(
                    tenant_id=self.db.tenant_id,
                    user_id=user_id,
                    order_id=order_id,
                    author_id=user_id,
                    title=f"Status changed to {status_update.status.value}",
                    content=status_update.notes,
                    note_type="status_change",
                    is_customer_visible=status_update.notify_customer,
                    created_by=user_id
                )
                self.db.add(note)
            
            self.db.commit()
            self.db.refresh(db_order)
            
            # Get items
            items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
            
            logger.info(f"Updated order {order_id} status to {status_update.status.value}")
            return self._build_order_response(db_order, items)
            
        except OrderNotFound:
            raise
        except Exception as e:
            logger.error(f"Error updating order status {order_id}: {str(e)}")
            self.db.rollback()
            raise OrderUpdateError(order_id, str(e))

    def bulk_operation(
        self,
        bulk_request: OrderBulkOperationRequest,
        user_id: UUID
    ) -> OrderBulkOperationResponse:
        """Perform bulk operations on orders"""
        successful = []
        failed = []
        
        for order_id in bulk_request.order_ids:
            try:
                if bulk_request.operation == 'update_status':
                    status = OrderStatus(bulk_request.parameters.get('status'))
                    status_update = OrderStatusUpdateRequest(
                        status=status,
                        notes=bulk_request.parameters.get('notes'),
                        notify_customer=bulk_request.parameters.get('notify_customer', False)
                    )
                    self.update_order_status(order_id, status_update, user_id)
                elif bulk_request.operation == 'assign':
                    assigned_to = UUID(bulk_request.parameters.get('assigned_to'))
                    order_update = OrderUpdate(assigned_to=assigned_to)
                    self.update_order(order_id, order_update, user_id)
                elif bulk_request.operation == 'add_tags':
                    tags = bulk_request.parameters.get('tags', [])
                    self._add_tags_to_order(order_id, tags, user_id)
                elif bulk_request.operation == 'remove_tags':
                    tags = bulk_request.parameters.get('tags', [])
                    self._remove_tags_from_order(order_id, tags, user_id)
                
                successful.append(order_id)
                
            except Exception as e:
                failed.append({"id": order_id, "error": str(e)})
                logger.error(f"Bulk operation {bulk_request.operation} failed for {order_id}: {str(e)}")
        
        # Commit all successful operations
        if successful:
            self.db.commit()
        
        return OrderBulkOperationResponse(
            successful=successful,
            failed=failed,
            total_requested=len(bulk_request.order_ids),
            total_successful=len(successful),
            total_failed=len(failed)
        )

    def get_order_stats(self, user_id: UUID) -> OrderStatsResponse:
        """Get order statistics for user"""
        try:
            # Base query
            base_query = self.db.query(Order).filter(
                Order.user_id == user_id,
                Order.is_deleted == False
            )
            
            # Total orders and counts by status
            total_orders = base_query.count()
            pending_orders = base_query.filter(Order.status == OrderStatus.PENDING.value).count()
            processing_orders = base_query.filter(Order.status == OrderStatus.PROCESSING.value).count()
            completed_orders = base_query.filter(Order.status == OrderStatus.COMPLETED.value).count()
            
            # Revenue calculation
            revenue_query = base_query.filter(Order.status.in_([
                OrderStatus.COMPLETED.value,
                OrderStatus.DELIVERED.value
            ]))
            total_revenue = revenue_query.with_entities(func.sum(Order.total_amount)).scalar() or Decimal('0')
            
            # Average order value
            avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0')
            
            # Orders by status
            status_stats = self.db.query(
                Order.status,
                func.count(Order.id).label('count')
            ).filter(
                Order.user_id == user_id,
                Order.is_deleted == False
            ).group_by(Order.status).all()
            
            orders_by_status = {status: count for status, count in status_stats}
            
            # Orders by platform
            platform_stats = self.db.query(
                Order.platform,
                func.count(Order.id).label('count')
            ).filter(
                Order.user_id == user_id,
                Order.is_deleted == False
            ).group_by(Order.platform).all()
            
            orders_by_platform = {platform: count for platform, count in platform_stats}
            
            # Recent orders
            recent_orders = base_query.order_by(desc(Order.created_at)).limit(10).all()
            recent_order_responses = []
            for order in recent_orders:
                items = self.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                recent_order_responses.append(self._build_order_response(order, items))
            
            return OrderStatsResponse(
                total_orders=total_orders,
                pending_orders=pending_orders,
                processing_orders=processing_orders,
                completed_orders=completed_orders,
                total_revenue=total_revenue,
                average_order_value=avg_order_value,
                orders_by_status=orders_by_status,
                orders_by_platform=orders_by_platform,
                recent_orders=recent_order_responses
            )
            
        except Exception as e:
            logger.error(f"Error getting order stats: {str(e)}")
            raise OrderCreateError(f"Failed to get order stats: {str(e)}")

    def add_order_note(
        self,
        order_id: UUID,
        note_data: OrderNoteCreate,
        user_id: UUID
    ) -> OrderNoteResponse:
        """Add note to order"""
        try:
            # Validate order exists
            self._get_user_order(order_id, user_id)
            
            db_note = OrderNote(
                tenant_id=self.db.tenant_id,
                user_id=user_id,
                order_id=order_id,
                author_id=user_id,
                title=note_data.title,
                content=note_data.content,
                note_type=note_data.note_type,
                priority=note_data.priority,
                is_customer_visible=note_data.is_customer_visible,
                tags=','.join(note_data.tags) if note_data.tags else None,
                created_by=user_id
            )
            
            self.db.add(db_note)
            self.db.commit()
            self.db.refresh(db_note)
            
            logger.info(f"Added note to order {order_id}")
            return OrderNoteResponse.model_validate(db_note)
            
        except OrderNotFound:
            raise
        except Exception as e:
            logger.error(f"Error adding note to order {order_id}: {str(e)}")
            self.db.rollback()
            raise OrderUpdateError(order_id, str(e))

    def create_fulfillment(
        self,
        order_id: UUID,
        fulfillment_data: OrderFulfillmentCreate,
        user_id: UUID
    ) -> OrderFulfillmentResponse:
        """Create order fulfillment"""
        try:
            # Validate order exists
            order = self._get_user_order(order_id, user_id)
            
            db_fulfillment = OrderFulfillment(
                tenant_id=self.db.tenant_id,
                user_id=user_id,
                order_id=order_id,
                tracking_number=fulfillment_data.tracking_number,
                carrier=fulfillment_data.carrier,
                service_level=fulfillment_data.service_level,
                shipping_cost=fulfillment_data.shipping_cost,
                insurance_cost=fulfillment_data.insurance_cost,
                weight_oz=fulfillment_data.weight_oz,
                dimensions=fulfillment_data.dimensions,
                fulfilled_items=','.join(str(item_id) for item_id in fulfillment_data.fulfilled_items) if fulfillment_data.fulfilled_items else None,
                fulfillment_notes=fulfillment_data.fulfillment_notes,
                ship_from_address=order.billing_address,
                ship_to_address=order.shipping_address,
                shipped_date=datetime.now(timezone.utc),
                created_by=user_id
            )
            
            self.db.add(db_fulfillment)
            
            # Update order fulfillment status if all items fulfilled
            if fulfillment_data.fulfilled_items:
                total_items = self.db.query(OrderItem).filter(OrderItem.order_id == order_id).count()
                if len(fulfillment_data.fulfilled_items) >= total_items:
                    order.fulfillment_status = FulfillmentStatus.FULFILLED.value
                else:
                    order.fulfillment_status = FulfillmentStatus.PARTIAL.value
            
            self.db.commit()
            self.db.refresh(db_fulfillment)
            
            logger.info(f"Created fulfillment for order {order_id}")
            return OrderFulfillmentResponse.model_validate(db_fulfillment)
            
        except OrderNotFound:
            raise
        except Exception as e:
            logger.error(f"Error creating fulfillment for order {order_id}: {str(e)}")
            self.db.rollback()
            raise OrderUpdateError(order_id, str(e))

    def _get_user_order(self, order_id: UUID, user_id: UUID) -> Order:
        """Get order by ID and validate user access"""
        order = self.db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id,
            Order.is_deleted == False
        ).first()
        
        if not order:
            raise OrderNotFound(order_id)
        
        return order

    def _build_order_response(self, order: Order, items: List[OrderItem]) -> OrderResponse:
        """Build order response with computed fields"""
        # Convert items to response models
        item_responses = [OrderItemResponse.model_validate(item) for item in items]
        
        # Compute fields
        items_count = len(items)
        total_quantity = sum(item.quantity for item in items)
        
        # Calculate profit margin if cost data available
        profit_margin = None
        cost_of_goods = sum(
            (item.cost_of_materials or 0) + (item.cost_of_labor or 0) 
            for item in items
        )
        if cost_of_goods > 0:
            profit_margin = ((float(order.total_amount) - cost_of_goods) / float(order.total_amount)) * 100
        
        # Build response
        response_data = order.__dict__.copy()
        response_data.update({
            'items': item_responses,
            'items_count': items_count,
            'total_quantity': total_quantity,
            'profit_margin': Decimal(str(profit_margin)) if profit_margin else None,
            'cost_of_goods': Decimal(str(cost_of_goods)) if cost_of_goods > 0 else None,
            'tracking_numbers': [],  # Would be populated from fulfillments
            'tags': [],  # Would be populated from order tags
            'metadata': {}  # Would be populated from order metadata
        })
        
        return OrderResponse.model_validate(response_data)

    def _generate_internal_order_number(self) -> str:
        """Generate internal order number"""
        # Get current date for prefix
        date_prefix = datetime.now().strftime("%Y%m%d")
        
        # Get count of orders today for sequence
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = self.db.query(Order).filter(
            Order.created_at >= today_start,
            Order.tenant_id == self.db.tenant_id
        ).count()
        
        sequence = today_count + 1
        return f"ORD-{date_prefix}-{sequence:04d}"

    def _add_tags_to_order(self, order_id: UUID, tags: List[str], user_id: UUID):
        """Add tags to order"""
        order = self._get_user_order(order_id, user_id)
        # Implementation would depend on how tags are stored
        # This is a placeholder
        pass

    def _remove_tags_from_order(self, order_id: UUID, tags: List[str], user_id: UUID):
        """Remove tags from order"""
        order = self._get_user_order(order_id, user_id)
        # Implementation would depend on how tags are stored
        # This is a placeholder
        pass
    
    # Etsy Integration Methods
    
    def get_etsy_orders(self, user_id: UUID, limit: int = 50) -> List[OrderResponse]:
        """Get orders that originated from Etsy"""
        try:
            orders = self.db.query(Order).filter(
                Order.user_id == user_id,
                Order.platform == 'etsy',
                Order.is_deleted == False
            ).order_by(desc(Order.created_at)).limit(limit).all()
            
            order_responses = []
            for order in orders:
                items = self.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                order_responses.append(self._build_order_response(order, items))
            
            return order_responses
            
        except Exception as e:
            logger.error(f"Error getting Etsy orders for user {user_id}: {str(e)}")
            raise OrderCreateError(f"Failed to get Etsy orders: {str(e)}")
    
    def update_etsy_order_status(self, etsy_receipt_id: int, user_id: UUID, 
                                new_status: str) -> Optional[OrderResponse]:
        """Update order status based on Etsy receipt ID"""
        try:
            order = self.db.query(Order).filter(
                Order.user_id == user_id,
                Order.etsy_receipt_id == etsy_receipt_id,
                Order.is_deleted == False
            ).first()
            
            if not order:
                logger.warning(f"No order found for Etsy receipt {etsy_receipt_id}")
                return None
            
            order.status = new_status
            order.updated_by = user_id
            self.db.commit()
            
            items = self.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
            return self._build_order_response(order, items)
            
        except Exception as e:
            logger.error(f"Error updating Etsy order status: {str(e)}")
            self.db.rollback()
            raise OrderUpdateError(order.id if 'order' in locals() else None, str(e))
    
    def get_orders_for_etsy_listing(self, user_id: UUID, etsy_listing_id: int) -> List[OrderResponse]:
        """Get orders that contain items from a specific Etsy listing"""
        try:
            # Find order items with the Etsy listing ID
            order_items = self.db.query(OrderItem).filter(
                OrderItem.user_id == user_id,
                OrderItem.etsy_listing_id == etsy_listing_id,
                OrderItem.is_deleted == False
            ).all()
            
            # Get unique orders
            order_ids = list(set(item.order_id for item in order_items))
            
            if not order_ids:
                return []
            
            orders = self.db.query(Order).filter(
                Order.id.in_(order_ids),
                Order.is_deleted == False
            ).all()
            
            order_responses = []
            for order in orders:
                items = self.db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
                order_responses.append(self._build_order_response(order, items))
            
            return order_responses
            
        except Exception as e:
            logger.error(f"Error getting orders for Etsy listing {etsy_listing_id}: {str(e)}")
            raise OrderCreateError(f"Failed to get orders for listing: {str(e)}")
    
    def sync_order_from_etsy_receipt(self, user_id: UUID, etsy_receipt_data: Dict[str, Any]) -> OrderResponse:
        """Create or update order from Etsy receipt data"""
        try:
            etsy_receipt_id = etsy_receipt_data.get('receipt_id')
            
            # Check if order already exists
            existing_order = self.db.query(Order).filter(
                Order.user_id == user_id,
                Order.etsy_receipt_id == etsy_receipt_id
            ).first()
            
            if existing_order:
                # Update existing order
                existing_order.status = self._map_etsy_status(etsy_receipt_data)
                existing_order.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                
                items = self.db.query(OrderItem).filter(OrderItem.order_id == existing_order.id).all()
                return self._build_order_response(existing_order, items)
            
            # Create new order from Etsy data
            order_data = self._convert_etsy_receipt_to_order(etsy_receipt_data, user_id)
            return self.create_order(order_data, user_id)
            
        except Exception as e:
            logger.error(f"Error syncing order from Etsy receipt: {str(e)}")
            self.db.rollback()
            raise OrderCreateError(f"Failed to sync Etsy order: {str(e)}")
    
    def _map_etsy_status(self, etsy_receipt_data: Dict[str, Any]) -> str:
        """Map Etsy receipt status to internal order status"""
        is_paid = etsy_receipt_data.get('is_paid', False)
        is_shipped = etsy_receipt_data.get('is_shipped', False)
        
        if not is_paid:
            return 'pending'
        elif is_shipped:
            return 'shipped'
        elif is_paid:
            return 'processing'
        else:
            return 'pending'
    
    def _convert_etsy_receipt_to_order(self, etsy_receipt_data: Dict[str, Any], user_id: UUID) -> OrderCreate:
        """Convert Etsy receipt data to internal order format"""
        # Extract basic order info
        total_amount = Decimal('0')
        if etsy_receipt_data.get('grandtotal'):
            total_amount = Decimal(str(etsy_receipt_data['grandtotal'].get('amount', 0)))
        
        # Build shipping address
        shipping_address = None
        if etsy_receipt_data.get('first_line'):
            shipping_address = {
                'name': etsy_receipt_data.get('name', ''),
                'line1': etsy_receipt_data.get('first_line', ''),
                'line2': etsy_receipt_data.get('second_line'),
                'city': etsy_receipt_data.get('city', ''),
                'state': etsy_receipt_data.get('state'),
                'zip': etsy_receipt_data.get('zip', ''),
                'country': etsy_receipt_data.get('country_iso', ''),
            }
        
        # Process order items from transactions
        items = []
        for transaction in etsy_receipt_data.get('transactions', []):
            item_price = Decimal('0')
            if transaction.get('price'):
                item_price = Decimal(str(transaction['price'].get('amount', 0)))
            
            item = OrderItemCreate(
                etsy_listing_id=transaction.get('listing_id'),
                product_name=transaction.get('title', 'Unknown Product'),
                quantity=transaction.get('quantity', 1),
                unit_price=item_price,
                total_price=item_price * transaction.get('quantity', 1),
                customization_text=transaction.get('personalization')
            )
            items.append(item)
        
        return OrderCreate(
            etsy_receipt_id=etsy_receipt_data.get('receipt_id'),
            etsy_order_id=etsy_receipt_data.get('order_id'),
            platform=OrderPlatform.ETSY,
            order_number=str(etsy_receipt_data.get('receipt_id')),
            total_amount=total_amount,
            currency=etsy_receipt_data.get('grandtotal', {}).get('currency_code', 'USD'),
            customer_email=etsy_receipt_data.get('payment_email'),
            customer_name=etsy_receipt_data.get('name'),
            shipping_address=shipping_address,
            special_instructions=etsy_receipt_data.get('message_from_buyer'),
            gift_message=etsy_receipt_data.get('gift_message'),
            items=items
        )