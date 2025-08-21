from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey, Table, JSON, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin
from .template import design_template_association

# Association table for many-to-many relationship between DesignImages and SizeConfig
design_size_config_association = Table(
    'design_size_config_association',
    MultiTenantBase.metadata,
    Column('design_image_id', UUID(as_uuid=True), ForeignKey('design_images.id', ondelete='CASCADE'), primary_key=True),
    Column('size_config_id', UUID(as_uuid=True), ForeignKey('size_configs.id', ondelete='CASCADE'), primary_key=True),
    Column('tenant_id', String, nullable=False, index=True)
)

class DesignImage(MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin):
    """Design images/files uploaded by users"""
    __tablename__ = 'design_images'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)  # Original name before processing
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=True)  # Public URL for the file
    file_size = Column(Integer, nullable=True)  # File size in bytes
    mime_type = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    canvas_config_id = Column(UUID(as_uuid=True), ForeignKey('canvas_configs.id'), nullable=True, index=True)
    
    # Image properties
    width_pixels = Column(Integer, nullable=True)
    height_pixels = Column(Integer, nullable=True)
    dpi = Column(Integer, nullable=True)
    color_mode = Column(String(20), nullable=True)  # RGB, CMYK, etc.
    has_transparency = Column(Boolean, default=False)
    
    # Classification and metadata
    is_active = Column(Boolean, default=True, index=True)
    is_digital = Column(Boolean, default=False)
    design_type = Column(String(50), nullable=True, index=True)  # vector, raster, svg, etc.
    category = Column(String(100), nullable=True, index=True)  # For organization
    tags = Column(ARRAY(String), default=[])  # Array of tags
    design_metadata = Column(JSON, default=dict)  # Flexible metadata storage
    
    # Processing status
    processing_status = Column(String(50), default='pending', index=True)  # pending, processing, completed, failed
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Analytics
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)  # How many times used in mockups
    
    # Relationships
    user = relationship('User', back_populates='design_images')
    product_templates = relationship('EtsyProductTemplate', secondary=design_template_association, back_populates='design_images')
    canvas_config = relationship('CanvasConfig', back_populates='design_images')
    size_configs = relationship('SizeConfig', secondary=design_size_config_association, back_populates='design_images')
    design_variants = relationship('DesignVariant', back_populates='original_design', cascade='all, delete-orphan')
    mockup_designs = relationship('MockupDesignAssociation', back_populates='design_image')
    
    @property
    def file_extension(self):
        """Get file extension"""
        if not self.filename:
            return None
        return self.filename.split('.')[-1].lower() if '.' in self.filename else None
    
    @property
    def is_vector(self):
        """Check if design is vector format"""
        vector_formats = ['svg', 'ai', 'eps', 'pdf']
        return self.file_extension in vector_formats
    
    @property
    def is_raster(self):
        """Check if design is raster format"""
        raster_formats = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']
        return self.file_extension in raster_formats
    
    def get_dimensions_dict(self):
        """Get image dimensions as dictionary"""
        return {
            'width': self.width_pixels,
            'height': self.height_pixels,
            'dpi': self.dpi
        }
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count = (self.usage_count or 0) + 1
    
    def increment_download(self):
        """Increment download count and update last downloaded"""
        from datetime import datetime, timezone
        self.download_count = (self.download_count or 0) + 1
        self.last_downloaded = datetime.now(timezone.utc)
    
    def __repr__(self):
        return f"<DesignImage(id='{self.id}', filename='{self.filename}', user_id='{self.user_id}')>"

class DesignVariant(MultiTenantBase, UserScopedMixin):
    """Variants of a design (different sizes, formats, etc.)"""
    __tablename__ = 'design_variants'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    original_design_id = Column(UUID(as_uuid=True), ForeignKey('design_images.id', ondelete='CASCADE'), nullable=False, index=True)
    variant_name = Column(String(100), nullable=False)  # 'thumbnail', 'large', 'print-ready', etc.
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    width_pixels = Column(Integer, nullable=True)
    height_pixels = Column(Integer, nullable=True)
    dpi = Column(Integer, nullable=True)
    format = Column(String(10), nullable=True)  # jpg, png, svg, etc.
    quality = Column(Integer, nullable=True)  # Compression quality for lossy formats
    
    # Relationships
    user = relationship('User')
    original_design = relationship('DesignImage', back_populates='design_variants')
    
    def __repr__(self):
        return f"<DesignVariant(id='{self.id}', variant='{self.variant_name}', design_id='{self.original_design_id}')>"

class DesignCollection(MultiTenantBase, UserScopedMixin, SoftDeleteMixin):
    """Collections for organizing designs"""
    __tablename__ = 'design_collections'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code
    icon = Column(String(50), nullable=True)  # Icon name/class
    is_public = Column(Boolean, default=False)  # Can be shared with other users
    sort_order = Column(Integer, default=0)
    
    # Relationships
    user = relationship('User')
    design_collection_items = relationship('DesignCollectionItem', back_populates='collection', cascade='all, delete-orphan')
    
    @property
    def design_count(self):
        """Get count of designs in collection"""
        return len(self.design_collection_items)
    
    def __repr__(self):
        return f"<DesignCollection(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"

class DesignCollectionItem(MultiTenantBase, UserScopedMixin):
    """Items in design collections"""
    __tablename__ = 'design_collection_items'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey('design_collections.id', ondelete='CASCADE'), nullable=False, index=True)
    design_id = Column(UUID(as_uuid=True), ForeignKey('design_images.id', ondelete='CASCADE'), nullable=False, index=True)
    sort_order = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User')
    collection = relationship('DesignCollection', back_populates='design_collection_items')
    design = relationship('DesignImage')
    
    def __repr__(self):
        return f"<DesignCollectionItem(collection_id='{self.collection_id}', design_id='{self.design_id}')>"

class DesignAnalytics(MultiTenantBase, UserScopedMixin):
    """Analytics data for designs"""
    __tablename__ = 'design_analytics'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    design_id = Column(UUID(as_uuid=True), ForeignKey('design_images.id', ondelete='CASCADE'), nullable=False, index=True)
    metric_name = Column(String(50), nullable=False, index=True)  # views, downloads, mockups_created, etc.
    metric_value = Column(Integer, default=0)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    layer_metadata = Column(JSON, default=dict)
    
    # Relationships
    user = relationship('User')
    design = relationship('DesignImage')
    
    def increment(self, amount: int = 1):
        """Increment metric value"""
        self.metric_value += amount
    
    def __repr__(self):
        return f"<DesignAnalytics(design_id='{self.design_id}', metric='{self.metric_name}', value={self.metric_value})>"