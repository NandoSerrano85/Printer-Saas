from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timezone
import logging
import json

from .models import (
    EtsyProductTemplateCreate,
    EtsyProductTemplateUpdate,
    EtsyProductTemplateResponse,
    TemplateListResponse,
    TemplateStatsResponse,
    TemplateBulkOperationRequest,
    TemplateBulkOperationResponse,
    EtsyTaxonomyResponse,
    EtsyShopSectionResponse
)
from database.entities import EtsyProductTemplate, User, ThirdPartyOAuthToken
from common.exceptions import (
    TemplateNotFound,
    TemplateAlreadyExists,
    TemplateCreateError,
    TemplateUpdateError,
    TemplateDeleteError,
    UserNotFound,
    ValidationError
)
from common.database import DatabaseManager

logger = logging.getLogger(__name__)

class TemplateService:
    """Service for managing product templates"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_template(self, template_data: EtsyProductTemplateCreate, user_id: UUID) -> EtsyProductTemplateResponse:
        """Create a new template for the user"""
        try:
            # Validate user exists
            user = self.db.query(User).filter(User.id == user_id, User.is_active == True).first()
            if not user:
                raise UserNotFound(user_id)
            
            # Check if template name already exists for this user
            existing_template = self.db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user_id,
                EtsyProductTemplate.name == template_data.name,
                EtsyProductTemplate.is_deleted == False
            ).first()
            
            if existing_template:
                raise TemplateAlreadyExists(template_data.name)
            
            # Process materials and tags
            materials_str = self._process_list_field(template_data.materials)
            tags_str = self._process_list_field(template_data.tags)
            
            # Create template
            db_template = EtsyProductTemplate(
                tenant_id=self.db.tenant_id,
                user_id=user_id,
                name=template_data.name,
                template_title=template_data.template_title,
                title=template_data.title,
                description=template_data.description,
                who_made=template_data.who_made,
                when_made=template_data.when_made,
                taxonomy_id=template_data.taxonomy_id,
                price=template_data.price,
                materials=materials_str,
                shop_section_id=template_data.shop_section_id,
                quantity=template_data.quantity,
                tags=tags_str,
                item_weight=template_data.item_weight,
                item_weight_unit=template_data.item_weight_unit,
                item_length=template_data.item_length,
                item_width=template_data.item_width,
                item_height=template_data.item_height,
                item_dimensions_unit=template_data.item_dimensions_unit,
                is_taxable=template_data.is_taxable,
                type=template_data.type,
                processing_min=template_data.processing_min,
                processing_max=template_data.processing_max,
                return_policy_id=template_data.return_policy_id,
                category=template_data.category,
                priority=template_data.priority,
                created_by=user_id
            )
            
            self.db.add(db_template)
            self.db.commit()
            self.db.refresh(db_template)
            
            logger.info(f"Created template {db_template.id} for user {user_id}")
            return EtsyProductTemplateResponse.model_validate(db_template)
            
        except (TemplateAlreadyExists, UserNotFound):
            raise
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            self.db.rollback()
            raise TemplateCreateError(str(e))

    def get_templates(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> TemplateListResponse:
        """Get templates for user with filtering and pagination"""
        try:
            # Base query
            query = self.db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user_id,
                EtsyProductTemplate.is_deleted == False
            )
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        EtsyProductTemplate.name.ilike(search_term),
                        EtsyProductTemplate.title.ilike(search_term),
                        EtsyProductTemplate.description.ilike(search_term),
                        EtsyProductTemplate.tags.ilike(search_term)
                    )
                )
            
            if category:
                query = query.filter(EtsyProductTemplate.category == category)
            
            if is_active is not None:
                query = query.filter(EtsyProductTemplate.is_active == is_active)
            
            # Apply sorting
            sort_column = getattr(EtsyProductTemplate, sort_by, EtsyProductTemplate.created_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            templates = query.offset(skip).limit(limit).all()
            
            # Convert to response models
            template_responses = [EtsyProductTemplateResponse.model_validate(t) for t in templates]
            
            return TemplateListResponse(
                templates=template_responses,
                total_count=total_count,
                page=skip // limit + 1,
                page_size=limit,
                has_next=(skip + limit) < total_count,
                has_prev=skip > 0
            )
            
        except Exception as e:
            logger.error(f"Error getting templates: {str(e)}")
            raise TemplateCreateError(f"Failed to get templates: {str(e)}")

    def get_template(self, template_id: UUID, user_id: UUID) -> EtsyProductTemplateResponse:
        """Get template by ID"""
        template = self._get_user_template(template_id, user_id)
        return EtsyProductTemplateResponse.model_validate(template)

    def update_template(
        self,
        template_id: UUID,
        template_data: EtsyProductTemplateUpdate,
        user_id: UUID
    ) -> EtsyProductTemplateResponse:
        """Update template by ID"""
        try:
            db_template = self._get_user_template(template_id, user_id)
            
            # Check if new name conflicts with existing template (excluding current template)
            if template_data.name and template_data.name != db_template.name:
                existing_template = self.db.query(EtsyProductTemplate).filter(
                    EtsyProductTemplate.user_id == user_id,
                    EtsyProductTemplate.name == template_data.name,
                    EtsyProductTemplate.id != template_id,
                    EtsyProductTemplate.is_deleted == False
                ).first()
                
                if existing_template:
                    raise TemplateAlreadyExists(template_data.name)
            
            # Update fields
            update_data = template_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field in ['materials', 'tags'] and value is not None:
                    value = self._process_list_field(value)
                setattr(db_template, field, value)
            
            # Update metadata
            db_template.updated_by = user_id
            db_template.version += 1
            
            self.db.commit()
            self.db.refresh(db_template)
            
            logger.info(f"Updated template {template_id} for user {user_id}")
            return EtsyProductTemplateResponse.model_validate(db_template)
            
        except (TemplateNotFound, TemplateAlreadyExists):
            raise
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {str(e)}")
            self.db.rollback()
            raise TemplateUpdateError(template_id, str(e))

    def delete_template(self, template_id: UUID, user_id: UUID) -> None:
        """Delete template by ID (soft delete)"""
        try:
            db_template = self._get_user_template(template_id, user_id)
            
            # Soft delete
            db_template.is_deleted = True
            db_template.deleted_at = datetime.now(timezone.utc)
            db_template.updated_by = user_id
            
            self.db.commit()
            
            logger.info(f"Deleted template {template_id} for user {user_id}")
            
        except TemplateNotFound:
            raise
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {str(e)}")
            self.db.rollback()
            raise TemplateDeleteError(template_id)

    def duplicate_template(self, template_id: UUID, user_id: UUID, new_name: str) -> EtsyProductTemplateResponse:
        """Duplicate an existing template"""
        try:
            original_template = self._get_user_template(template_id, user_id)
            
            # Check if new name already exists
            existing_template = self.db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user_id,
                EtsyProductTemplate.name == new_name,
                EtsyProductTemplate.is_deleted == False
            ).first()
            
            if existing_template:
                raise TemplateAlreadyExists(new_name)
            
            # Create duplicate
            duplicate_data = {
                'tenant_id': self.db.tenant_id,
                'user_id': user_id,
                'name': new_name,
                'template_title': original_template.template_title,
                'title': original_template.title,
                'description': original_template.description,
                'who_made': original_template.who_made,
                'when_made': original_template.when_made,
                'taxonomy_id': original_template.taxonomy_id,
                'price': original_template.price,
                'materials': original_template.materials,
                'shop_section_id': original_template.shop_section_id,
                'quantity': original_template.quantity,
                'tags': original_template.tags,
                'item_weight': original_template.item_weight,
                'item_weight_unit': original_template.item_weight_unit,
                'item_length': original_template.item_length,
                'item_width': original_template.item_width,
                'item_height': original_template.item_height,
                'item_dimensions_unit': original_template.item_dimensions_unit,
                'is_taxable': original_template.is_taxable,
                'type': original_template.type,
                'processing_min': original_template.processing_min,
                'processing_max': original_template.processing_max,
                'return_policy_id': original_template.return_policy_id,
                'category': original_template.category,
                'priority': original_template.priority,
                'created_by': user_id
            }
            
            db_duplicate = EtsyProductTemplate(**duplicate_data)
            
            self.db.add(db_duplicate)
            self.db.commit()
            self.db.refresh(db_duplicate)
            
            logger.info(f"Duplicated template {template_id} to {db_duplicate.id}")
            return EtsyProductTemplateResponse.model_validate(db_duplicate)
            
        except (TemplateNotFound, TemplateAlreadyExists):
            raise
        except Exception as e:
            logger.error(f"Error duplicating template {template_id}: {str(e)}")
            self.db.rollback()
            raise TemplateCreateError(f"Failed to duplicate template: {str(e)}")

    def bulk_operation(
        self,
        bulk_request: TemplateBulkOperationRequest,
        user_id: UUID
    ) -> TemplateBulkOperationResponse:
        """Perform bulk operations on templates"""
        successful = []
        failed = []
        
        for template_id in bulk_request.template_ids:
            try:
                if bulk_request.operation == 'activate':
                    self._bulk_activate_template(template_id, user_id)
                elif bulk_request.operation == 'deactivate':
                    self._bulk_deactivate_template(template_id, user_id)
                elif bulk_request.operation == 'delete':
                    self.delete_template(template_id, user_id)
                elif bulk_request.operation == 'duplicate':
                    # For duplicate, we'll need additional data like new names
                    # This is simplified - in reality you'd need a mapping of IDs to new names
                    new_name = f"Copy of {template_id}"
                    self.duplicate_template(template_id, user_id, new_name)
                
                successful.append(template_id)
                
            except Exception as e:
                failed.append({"id": template_id, "error": str(e)})
                logger.error(f"Bulk operation {bulk_request.operation} failed for {template_id}: {str(e)}")
        
        # Commit all successful operations
        if successful:
            self.db.commit()
        
        return TemplateBulkOperationResponse(
            successful=successful,
            failed=failed,
            total_requested=len(bulk_request.template_ids),
            total_successful=len(successful),
            total_failed=len(failed)
        )

    def get_template_stats(self, user_id: UUID) -> TemplateStatsResponse:
        """Get template statistics for user"""
        try:
            # Total and active templates count
            total_query = self.db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user_id,
                EtsyProductTemplate.is_deleted == False
            )
            
            total_templates = total_query.count()
            active_templates = total_query.filter(EtsyProductTemplate.is_active == True).count()
            
            # Templates by category
            category_stats = self.db.query(
                EtsyProductTemplate.category,
                func.count(EtsyProductTemplate.id).label('count')
            ).filter(
                EtsyProductTemplate.user_id == user_id,
                EtsyProductTemplate.is_deleted == False,
                EtsyProductTemplate.is_active == True
            ).group_by(EtsyProductTemplate.category).all()
            
            templates_by_category = {
                category or 'Uncategorized': count 
                for category, count in category_stats
            }
            
            # Recently used templates (by updated_at)
            recently_used = self.db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user_id,
                EtsyProductTemplate.is_deleted == False,
                EtsyProductTemplate.is_active == True
            ).order_by(desc(EtsyProductTemplate.updated_at)).limit(5).all()
            
            # Most used templates (by usage_count if we had that field, for now use priority)
            most_used = self.db.query(EtsyProductTemplate).filter(
                EtsyProductTemplate.user_id == user_id,
                EtsyProductTemplate.is_deleted == False,
                EtsyProductTemplate.is_active == True
            ).order_by(desc(EtsyProductTemplate.priority)).limit(5).all()
            
            return TemplateStatsResponse(
                total_templates=total_templates,
                active_templates=active_templates,
                templates_by_category=templates_by_category,
                recently_used=[EtsyProductTemplateResponse.model_validate(t) for t in recently_used],
                most_used=[EtsyProductTemplateResponse.model_validate(t) for t in most_used]
            )
            
        except Exception as e:
            logger.error(f"Error getting template stats: {str(e)}")
            raise TemplateCreateError(f"Failed to get template stats: {str(e)}")

    def get_etsy_taxonomies(self, user_id: UUID) -> List[EtsyTaxonomyResponse]:
        """Get Etsy taxonomies via API"""
        # This would integrate with Etsy API
        # For now, return empty list as placeholder
        logger.info(f"Getting Etsy taxonomies for user {user_id}")
        return []

    def get_etsy_shop_sections(self, user_id: UUID) -> List[EtsyShopSectionResponse]:
        """Get Etsy shop sections via API"""
        # This would integrate with Etsy API using stored OAuth tokens
        try:
            # Get user's Etsy OAuth token
            oauth_token = self.db.query(ThirdPartyOAuthToken).filter(
                ThirdPartyOAuthToken.user_id == user_id,
                ThirdPartyOAuthToken.provider == 'etsy'
            ).first()
            
            if not oauth_token:
                logger.warning(f"No Etsy OAuth token found for user {user_id}")
                return []
            
            # TODO: Integrate with actual Etsy API
            # For now, return placeholder data
            logger.info(f"Getting Etsy shop sections for user {user_id}")
            return []
            
        except Exception as e:
            logger.error(f"Error getting Etsy shop sections: {str(e)}")
            return []

    def _get_user_template(self, template_id: UUID, user_id: UUID) -> EtsyProductTemplate:
        """Get template by ID and validate user access"""
        template = self.db.query(EtsyProductTemplate).filter(
            EtsyProductTemplate.id == template_id,
            EtsyProductTemplate.user_id == user_id,
            EtsyProductTemplate.is_deleted == False
        ).first()
        
        if not template:
            raise TemplateNotFound(template_id)
        
        return template

    def _process_list_field(self, field_value) -> Optional[str]:
        """Process list fields to comma-separated strings"""
        if field_value is None:
            return None
        if isinstance(field_value, list):
            return ','.join(str(item).strip() for item in field_value if str(item).strip())
        return str(field_value).strip() if str(field_value).strip() else None

    def _bulk_activate_template(self, template_id: UUID, user_id: UUID):
        """Activate a template"""
        template = self._get_user_template(template_id, user_id)
        template.is_active = True
        template.updated_by = user_id

    def _bulk_deactivate_template(self, template_id: UUID, user_id: UUID):
        """Deactivate a template"""
        template = self._get_user_template(template_id, user_id)
        template.is_active = False
        template.updated_by = user_id