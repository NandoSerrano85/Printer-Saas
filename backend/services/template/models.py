from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID

class EtsyProductTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Template name")
    template_title: Optional[str] = Field(None, max_length=255, description="User-friendly template title")
    title: Optional[str] = Field(None, max_length=255, description="Etsy listing title")
    description: Optional[str] = Field(None, description="Product description")
    who_made: Optional[str] = Field(None, description="Who made the product")
    when_made: Optional[str] = Field(None, description="When the product was made")
    taxonomy_id: Optional[int] = Field(None, description="Etsy taxonomy ID")
    price: Optional[float] = Field(None, ge=0, description="Product price")
    materials: Optional[Union[str, List[str]]] = Field(None, description="Materials used")
    shop_section_id: Optional[int] = Field(None, description="Etsy shop section ID")
    quantity: Optional[int] = Field(None, ge=0, description="Available quantity")
    tags: Optional[Union[str, List[str]]] = Field(None, description="Product tags")
    
    # Physical dimensions
    item_weight: Optional[float] = Field(None, ge=0, description="Item weight")
    item_weight_unit: Optional[str] = Field(None, description="Weight unit (oz, lb, g, kg)")
    item_length: Optional[float] = Field(None, ge=0, description="Item length")
    item_width: Optional[float] = Field(None, ge=0, description="Item width")
    item_height: Optional[float] = Field(None, ge=0, description="Item height")
    item_dimensions_unit: Optional[str] = Field(None, description="Dimensions unit (in, cm, mm)")
    
    # Etsy specific fields
    is_taxable: Optional[bool] = Field(None, description="Is item taxable")
    type: Optional[str] = Field(None, description="Product type (physical, digital)")
    processing_min: Optional[int] = Field(None, ge=1, description="Minimum processing time")
    processing_max: Optional[int] = Field(None, ge=1, description="Maximum processing time")
    return_policy_id: Optional[int] = Field(None, description="Return policy ID")
    
    # Organization fields
    category: Optional[str] = Field(None, max_length=100, description="Custom category")
    priority: Optional[int] = Field(0, description="Template priority")
    
    @validator('materials', pre=True)
    def validate_materials(cls, v):
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        elif isinstance(v, str):
            return v.strip() if v.strip() else None
        return v
    
    @validator('tags', pre=True)
    def validate_tags(cls, v):
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        elif isinstance(v, str):
            return v.strip() if v.strip() else None
        return v
    
    @validator('processing_max')
    def validate_processing_times(cls, v, values):
        processing_min = values.get('processing_min')
        if processing_min is not None and v is not None and v < processing_min:
            raise ValueError('processing_max must be >= processing_min')
        return v

class EtsyProductTemplateCreate(EtsyProductTemplateBase):
    """Model for creating a new template"""
    pass

class EtsyProductTemplateUpdate(BaseModel):
    """Model for updating a template (all fields optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    template_title: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    who_made: Optional[str] = None
    when_made: Optional[str] = None
    taxonomy_id: Optional[int] = None
    price: Optional[float] = Field(None, ge=0)
    materials: Optional[Union[str, List[str]]] = None
    shop_section_id: Optional[int] = None
    quantity: Optional[int] = Field(None, ge=0)
    tags: Optional[Union[str, List[str]]] = None
    
    # Physical dimensions
    item_weight: Optional[float] = Field(None, ge=0)
    item_weight_unit: Optional[str] = None
    item_length: Optional[float] = Field(None, ge=0)
    item_width: Optional[float] = Field(None, ge=0)
    item_height: Optional[float] = Field(None, ge=0)
    item_dimensions_unit: Optional[str] = None
    
    # Etsy specific fields
    is_taxable: Optional[bool] = None
    type: Optional[str] = None
    processing_min: Optional[int] = Field(None, ge=1)
    processing_max: Optional[int] = Field(None, ge=1)
    return_policy_id: Optional[int] = None
    
    # Organization fields
    category: Optional[str] = Field(None, max_length=100)
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class EtsyProductTemplateResponse(EtsyProductTemplateBase):
    """Model for template responses"""
    id: UUID
    user_id: UUID
    tenant_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Computed fields
    materials_list: Optional[List[str]] = None
    tags_list: Optional[List[str]] = None
    
    model_config = ConfigDict(from_attributes=True)
    
    @validator('materials_list', pre=False, always=True)
    def compute_materials_list(cls, v, values):
        materials = values.get('materials')
        if isinstance(materials, str) and materials:
            return [item.strip() for item in materials.split(',') if item.strip()]
        elif isinstance(materials, list):
            return materials
        return []
    
    @validator('tags_list', pre=False, always=True)
    def compute_tags_list(cls, v, values):
        tags = values.get('tags')
        if isinstance(tags, str) and tags:
            return [item.strip() for item in tags.split(',') if item.strip()]
        elif isinstance(tags, list):
            return tags
        return []

class TemplateListResponse(BaseModel):
    """Response model for template lists"""
    templates: List[EtsyProductTemplateResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

class TemplateStatsResponse(BaseModel):
    """Response model for template statistics"""
    total_templates: int
    active_templates: int
    templates_by_category: dict
    recently_used: List[EtsyProductTemplateResponse]
    most_used: List[EtsyProductTemplateResponse]

class EtsyTaxonomyResponse(BaseModel):
    """Response model for Etsy taxonomies"""
    id: int
    name: str
    level: int
    parent_id: Optional[int] = None
    path: List[str] = []
    full_path_taxonomy_ids: List[int] = []

class EtsyShopSectionResponse(BaseModel):
    """Response model for Etsy shop sections"""
    shop_section_id: int
    title: str
    rank: int
    user_id: int

class TemplateBulkOperationRequest(BaseModel):
    """Model for bulk operations on templates"""
    template_ids: List[UUID] = Field(..., min_items=1, description="List of template IDs")
    operation: str = Field(..., description="Operation to perform (activate, deactivate, delete)")
    
    @validator('operation')
    def validate_operation(cls, v):
        allowed_operations = ['activate', 'deactivate', 'delete', 'duplicate']
        if v not in allowed_operations:
            raise ValueError(f'Operation must be one of: {", ".join(allowed_operations)}')
        return v

class TemplateBulkOperationResponse(BaseModel):
    """Response model for bulk operations"""
    successful: List[UUID]
    failed: List[dict]  # [{"id": UUID, "error": str}]
    total_requested: int
    total_successful: int
    total_failed: int

class TemplateImportRequest(BaseModel):
    """Model for importing templates"""
    source_type: str = Field(..., description="Source type (csv, json, etsy)")
    data: Union[str, dict] = Field(..., description="Import data")
    
    @validator('source_type')
    def validate_source_type(cls, v):
        allowed_sources = ['csv', 'json', 'etsy']
        if v not in allowed_sources:
            raise ValueError(f'Source type must be one of: {", ".join(allowed_sources)}')
        return v

class TemplateExportRequest(BaseModel):
    """Model for exporting templates"""
    template_ids: Optional[List[UUID]] = Field(None, description="Specific template IDs to export (all if not provided)")
    format: str = Field('json', description="Export format (json, csv)")
    include_usage_stats: bool = Field(False, description="Include usage statistics")
    
    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['json', 'csv']
        if v not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v