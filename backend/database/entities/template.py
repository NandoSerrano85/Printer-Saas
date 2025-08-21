from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin
from .user import User

# Association table for many-to-many relationship between DesignImages and EtsyProductTemplate
design_template_association = Table(
    'design_template_association',
    MultiTenantBase.metadata,
    Column('design_image_id', UUID(as_uuid=True), ForeignKey('design_images.id', ondelete='CASCADE'), primary_key=True),
    Column('product_template_id', UUID(as_uuid=True), ForeignKey('etsy_product_templates.id', ondelete='CASCADE'), primary_key=True),
    Column('tenant_id', String, nullable=False, index=True)  # Add tenant_id for multi-tenant support
)

class EtsyProductTemplate(MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin):
    """Product templates for Etsy listings with multi-tenant support"""
    __tablename__ = 'etsy_product_templates'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)  # Template identifier
    template_title = Column(String(255), nullable=True)  # User-friendly template name
    title = Column(String(255), nullable=True)  # Etsy listing title
    description = Column(Text, nullable=True)
    who_made = Column(String(50), nullable=True)  # i_did, collective, someone_else
    when_made = Column(String(50), nullable=True)  # made_to_order, 2020_2023, etc.
    taxonomy_id = Column(Integer, nullable=True)  # Etsy taxonomy ID
    price = Column(Float, nullable=True)
    materials = Column(Text, nullable=True)  # Comma-separated or JSON string
    shop_section_id = Column(Integer, nullable=True)  # Etsy shop section ID
    quantity = Column(Integer, nullable=True)
    tags = Column(Text, nullable=True)  # Comma-separated or JSON string
    
    # Physical product dimensions
    item_weight = Column(Float, nullable=True)
    item_weight_unit = Column(String(10), nullable=True)  # oz, lb, g, kg
    item_length = Column(Float, nullable=True)
    item_width = Column(Float, nullable=True)
    item_height = Column(Float, nullable=True)
    item_dimensions_unit = Column(String(10), nullable=True)  # in, cm, mm
    
    # Etsy specific fields
    is_taxable = Column(Boolean, nullable=True)
    type = Column(String(50), nullable=True)  # physical, digital
    processing_min = Column(Integer, nullable=True)  # Processing time minimum
    processing_max = Column(Integer, nullable=True)  # Processing time maximum
    return_policy_id = Column(Integer, nullable=True)  # Etsy return policy ID
    
    # Template metadata
    is_active = Column(Boolean, default=True, index=True)
    category = Column(String(100), nullable=True)  # Custom category for organization
    priority = Column(Integer, default=0)  # For sorting/ordering templates
    
    # Relationships
    user = relationship('User', back_populates='etsy_product_templates')
    canvas_configs = relationship('CanvasConfig', back_populates='product_template', cascade='all, delete-orphan')
    size_configs = relationship('SizeConfig', back_populates='product_template', cascade='all, delete-orphan')
    design_images = relationship('DesignImage', secondary=design_template_association, back_populates='product_templates')
    mockups = relationship('Mockup', back_populates='product_template')
    order_items = relationship('OrderItem', back_populates='product_template')
    
    @property
    def materials_list(self):
        """Get materials as a list"""
        if not self.materials:
            return []
        return [material.strip() for material in self.materials.split(',') if material.strip()]
    
    @materials_list.setter
    def materials_list(self, materials):
        """Set materials from a list"""
        if isinstance(materials, list):
            self.materials = ', '.join(materials)
        else:
            self.materials = materials
    
    @property
    def tags_list(self):
        """Get tags as a list"""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    @tags_list.setter
    def tags_list(self, tags):
        """Set tags from a list"""
        if isinstance(tags, list):
            self.tags = ', '.join(tags)
        else:
            self.tags = tags
    
    def get_dimensions_dict(self):
        """Get dimensions as a dictionary"""
        return {
            'length': self.item_length,
            'width': self.item_width,
            'height': self.item_height,
            'unit': self.item_dimensions_unit
        }
    
    def get_weight_dict(self):
        """Get weight as a dictionary"""
        return {
            'weight': self.item_weight,
            'unit': self.item_weight_unit
        }
    
    def __repr__(self):
        return f"<EtsyProductTemplate(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"

class TemplateCategory(MultiTenantBase, UserScopedMixin):
    """Categories for organizing product templates"""
    __tablename__ = 'template_categories'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)  # Icon name/class
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship('User')
    
    def __repr__(self):
        return f"<TemplateCategory(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"

class TemplateVersion(MultiTenantBase, UserScopedMixin):
    """Version history for product templates"""
    __tablename__ = 'template_versions'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id', ondelete='CASCADE'), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    change_summary = Column(Text, nullable=True)
    template_data = Column(Text, nullable=False)  # JSON snapshot of template at this version
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    
    # Relationships
    user = relationship('User', foreign_keys=[user_id])
    created_by_user = relationship('User', foreign_keys=[created_by])
    template = relationship('EtsyProductTemplate')
    
    def __repr__(self):
        return f"<TemplateVersion(template_id='{self.template_id}', version={self.version_number})>"

class TemplateTag(MultiTenantBase, UserScopedMixin):
    """Custom tags for templates (different from Etsy tags)"""
    __tablename__ = 'template_tags'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)
    color = Column(String(7), nullable=True)  # Hex color code
    description = Column(Text, nullable=True)
    usage_count = Column(Integer, default=0)  # How many times this tag is used
    
    # Relationships
    user = relationship('User')
    
    def __repr__(self):
        return f"<TemplateTag(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"

# Association table for template custom tags
template_custom_tags = Table(
    'template_custom_tags',
    MultiTenantBase.metadata,
    Column('template_id', UUID(as_uuid=True), ForeignKey('etsy_product_templates.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('template_tags.id', ondelete='CASCADE'), primary_key=True),
    Column('tenant_id', String, nullable=False, index=True)
)