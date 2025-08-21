from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import List, Optional
from uuid import UUID

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
from .service import TemplateService
from common.auth import ActiveUserDep
from common.database import get_database_manager, DatabaseManager
from common.exceptions import (
    TemplateNotFound,
    TemplateAlreadyExists,
    TemplateCreateError,
    TemplateUpdateError,
    TemplateDeleteError,
    ValidationError
)

router = APIRouter(
    prefix="/api/v1/templates",
    tags=["Templates"]
)

def get_template_service(db_manager: DatabaseManager = Depends(get_database_manager)) -> TemplateService:
    """Dependency to get template service"""
    return TemplateService(db_manager)

@router.post("/", response_model=EtsyProductTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: EtsyProductTemplateCreate,
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service)
):
    """Create a new product template"""
    try:
        return template_service.create_template(template_data, current_user.get_uuid())
    except TemplateAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TemplateCreateError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=TemplateListResponse)
async def get_templates(
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service),
    skip: int = Query(0, ge=0, description="Number of templates to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of templates to return"),
    search: Optional[str] = Query(None, description="Search templates by name, title, description, or tags"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """Get all templates for the current user with filtering and pagination"""
    return template_service.get_templates(
        user_id=current_user.get_uuid(),
        skip=skip,
        limit=limit,
        search=search,
        category=category,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/stats", response_model=TemplateStatsResponse)
async def get_template_stats(
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service)
):
    """Get template statistics for the current user"""
    return template_service.get_template_stats(current_user.get_uuid())

@router.get("/etsy/taxonomies", response_model=List[EtsyTaxonomyResponse])
async def get_etsy_taxonomies(
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service)
):
    """Get Etsy product taxonomies"""
    return template_service.get_etsy_taxonomies(current_user.get_uuid())

@router.get("/etsy/shop-sections", response_model=List[EtsyShopSectionResponse])
async def get_etsy_shop_sections(
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service)
):
    """Get Etsy shop sections"""
    return template_service.get_etsy_shop_sections(current_user.get_uuid())

@router.post("/bulk", response_model=TemplateBulkOperationResponse)
async def bulk_operation(
    bulk_request: TemplateBulkOperationRequest,
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service)
):
    """Perform bulk operations on templates"""
    return template_service.bulk_operation(bulk_request, current_user.get_uuid())

@router.get("/{template_id}", response_model=EtsyProductTemplateResponse)
async def get_template(
    template_id: UUID,
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service)
):
    """Get a specific template by ID"""
    try:
        return template_service.get_template(template_id, current_user.get_uuid())
    except TemplateNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{template_id}", response_model=EtsyProductTemplateResponse)
async def update_template(
    template_id: UUID,
    template_data: EtsyProductTemplateUpdate,
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service)
):
    """Update a template by ID"""
    try:
        return template_service.update_template(template_id, template_data, current_user.get_uuid())
    except TemplateNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TemplateAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TemplateUpdateError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service)
):
    """Delete a template by ID"""
    try:
        template_service.delete_template(template_id, current_user.get_uuid())
    except TemplateNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TemplateDeleteError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{template_id}/duplicate", response_model=EtsyProductTemplateResponse)
async def duplicate_template(
    template_id: UUID,
    current_user: ActiveUserDep,
    template_service: TemplateService = Depends(get_template_service),
    new_name: str = Query(..., description="Name for the duplicated template")
):
    """Duplicate a template with a new name"""
    try:
        return template_service.duplicate_template(template_id, current_user.get_uuid(), new_name)
    except TemplateNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TemplateAlreadyExists as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TemplateCreateError as e:
        raise HTTPException(status_code=500, detail=str(e))