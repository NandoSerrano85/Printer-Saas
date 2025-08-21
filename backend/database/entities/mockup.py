from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey, JSON, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin

class Mockup(MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin):
    """Main mockup entity containing metadata and settings"""
    __tablename__ = 'mockups'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    product_template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id'), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    starting_number = Column(Integer, default=100)
    
    # Status and processing
    status = Column(String(50), default='pending', index=True)  # pending, processing, completed, failed
    progress_percentage = Column(Integer, default=0)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Settings and configuration
    settings = Column(JSON, default=dict)  # Flexible settings storage
    quality_settings = Column(JSON, default=dict)  # Image quality, compression, etc.
    naming_pattern = Column(String(255), nullable=True)  # Pattern for generated file names
    batch_size = Column(Integer, default=1)  # How many designs to process at once
    
    # Output settings
    output_format = Column(String(10), default='png')  # png, jpg, pdf, etc.
    output_quality = Column(Integer, default=95)  # Quality percentage
    output_dpi = Column(Integer, default=300)
    output_width = Column(Integer, nullable=True)
    output_height = Column(Integer, nullable=True)
    
    # Organization
    category = Column(String(100), nullable=True, index=True)
    tags = Column(Text, nullable=True)  # Comma-separated tags
    priority = Column(Integer, default=0)  # For sorting/prioritization
    
    # Analytics
    total_images = Column(Integer, default=0)
    completed_images = Column(Integer, default=0)
    failed_images = Column(Integer, default=0)
    total_file_size = Column(Integer, default=0)  # Total size in bytes
    
    # Relationships
    user = relationship('User', back_populates='mockups')
    product_template = relationship('EtsyProductTemplate', back_populates='mockups')
    mockup_images = relationship('MockupImage', back_populates='mockup', cascade='all, delete-orphan')
    mockup_designs = relationship('MockupDesignAssociation', back_populates='mockup', cascade='all, delete-orphan')
    order_items = relationship('OrderItem', back_populates='mockup')
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if self.total_images == 0:
            return 0
        return (self.completed_images / self.total_images) * 100
    
    @property
    def is_completed(self):
        """Check if mockup is completed"""
        return self.status == 'completed'
    
    @property
    def is_processing(self):
        """Check if mockup is currently processing"""
        return self.status in ['pending', 'processing']
    
    def get_setting(self, key: str, default=None):
        """Get setting value"""
        return self.settings.get(key, default) if self.settings else default
    
    def set_setting(self, key: str, value):
        """Set setting value"""
        if self.settings is None:
            self.settings = {}
        self.settings[key] = value
    
    def increment_completed(self):
        """Increment completed images count"""
        self.completed_images += 1
        if self.completed_images >= self.total_images and self.total_images > 0:
            self.status = 'completed'
            if not self.processing_completed_at:
                from datetime import datetime, timezone
                self.processing_completed_at = datetime.now(timezone.utc)
    
    def increment_failed(self):
        """Increment failed images count"""
        self.failed_images += 1
    
    def __repr__(self):
        return f"<Mockup(id='{self.id}', name='{self.name}', status='{self.status}', user_id='{self.user_id}')>"

class MockupImage(MultiTenantBase, UserScopedMixin):
    """Individual mockup images generated from the mockup process"""
    __tablename__ = 'mockup_images'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    mockup_id = Column(UUID(as_uuid=True), ForeignKey('mockups.id', ondelete='CASCADE'), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=True)
    watermark_path = Column(String(500), nullable=True)
    
    # Image properties
    image_type = Column(String(50), nullable=True)  # base, variant, thumbnail
    width_pixels = Column(Integer, nullable=True)
    height_pixels = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    dpi = Column(Integer, nullable=True)
    format = Column(String(10), nullable=True)  # png, jpg, etc.
    
    # Processing information
    processing_status = Column(String(50), default='pending', index=True)
    processing_time_seconds = Column(Float, nullable=True)
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    mockup_metadata = Column(JSON, default=dict)
    sequence_number = Column(Integer, nullable=True)  # Order in batch
    
    # Analytics
    download_count = Column(Integer, default=0)
    last_downloaded = Column(DateTime(timezone=True), nullable=True)
    view_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship('User')
    mockup = relationship('Mockup', back_populates='mockup_images')
    mask_data = relationship('MockupMaskData', back_populates='mockup_image', cascade='all, delete-orphan')
    
    @property
    def is_processed(self):
        """Check if image is successfully processed"""
        return self.processing_status == 'completed'
    
    @property
    def has_error(self):
        """Check if image processing failed"""
        return self.processing_status == 'failed'
    
    def get_aspect_ratio(self):
        """Calculate aspect ratio"""
        if self.width_pixels and self.height_pixels and self.height_pixels != 0:
            return self.width_pixels / self.height_pixels
        return None
    
    def increment_download(self):
        """Increment download count"""
        from datetime import datetime, timezone
        self.download_count += 1
        self.last_downloaded = datetime.now(timezone.utc)
    
    def increment_view(self):
        """Increment view count"""
        self.view_count += 1
    
    def __repr__(self):
        return f"<MockupImage(id='{self.id}', filename='{self.filename}', mockup_id='{self.mockup_id}')>"

class MockupMaskData(MultiTenantBase, UserScopedMixin):
    """Mask data and positioning information for mockup images"""
    __tablename__ = 'mockup_mask_data'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    mockup_image_id = Column(UUID(as_uuid=True), ForeignKey('mockup_images.id', ondelete='CASCADE'), nullable=False, index=True)
    masks = Column(JSON, nullable=False)  # Array of mask objects
    points = Column(JSON, nullable=False)  # Array of positioning points
    is_cropped = Column(Boolean, default=False)
    alignment = Column(String(50), nullable=False)  # center, top-left, etc.
    
    # Transform settings
    rotation_degrees = Column(Float, default=0)
    scale_x = Column(Float, default=1.0)
    scale_y = Column(Float, default=1.0)
    offset_x = Column(Integer, default=0)
    offset_y = Column(Integer, default=0)
    
    # Processing settings
    blend_mode = Column(String(50), default='normal')  # normal, multiply, overlay, etc.
    opacity = Column(Float, default=1.0)  # 0.0 to 1.0
    shadow_settings = Column(JSON, default=dict)
    highlight_settings = Column(JSON, default=dict)
    
    # Relationships
    user = relationship('User')
    mockup_image = relationship('MockupImage', back_populates='mask_data')
    
    def get_transform_matrix(self):
        """Get transformation matrix for the mask"""
        return {
            'rotation': self.rotation_degrees,
            'scale_x': self.scale_x,
            'scale_y': self.scale_y,
            'offset_x': self.offset_x,
            'offset_y': self.offset_y
        }
    
    def __repr__(self):
        return f"<MockupMaskData(id='{self.id}', alignment='{self.alignment}', mockup_image_id='{self.mockup_image_id}')>"

class MockupDesignAssociation(MultiTenantBase, UserScopedMixin):
    """Association between mockups and design images"""
    __tablename__ = 'mockup_design_associations'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    mockup_id = Column(UUID(as_uuid=True), ForeignKey('mockups.id', ondelete='CASCADE'), nullable=False, index=True)
    design_image_id = Column(UUID(as_uuid=True), ForeignKey('design_images.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Association settings
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)  # Primary design for the mockup
    scale_factor = Column(Float, default=1.0)
    position_x = Column(Float, default=0)
    position_y = Column(Float, default=0)
    rotation = Column(Float, default=0)
    
    # Processing status
    processing_status = Column(String(50), default='pending', index=True)
    processing_error = Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User')
    mockup = relationship('Mockup', back_populates='mockup_designs')
    design_image = relationship('DesignImage', back_populates='mockup_designs')
    
    def __repr__(self):
        return f"<MockupDesignAssociation(mockup_id='{self.mockup_id}', design_id='{self.design_image_id}')>"

class MockupTemplate(MultiTenantBase, UserScopedMixin, SoftDeleteMixin):
    """Reusable mockup templates with predefined settings"""
    __tablename__ = 'mockup_templates'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    preview_image_path = Column(String(500), nullable=True)
    
    # Template settings
    template_settings = Column(JSON, nullable=False)  # Complete mockup settings
    mask_data = Column(JSON, nullable=True)  # Default mask configuration
    output_settings = Column(JSON, default=dict)
    
    # Metadata
    category = Column(String(100), nullable=True, index=True)
    tags = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)  # Can be shared with other tenants
    usage_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship('User')
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
    
    def __repr__(self):
        return f"<MockupTemplate(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"

class MockupBatch(MultiTenantBase, UserScopedMixin):
    """Batch processing for multiple mockups"""
    __tablename__ = 'mockup_batches'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Batch settings
    batch_settings = Column(JSON, default=dict)
    priority = Column(Integer, default=0)  # Higher priority batches process first
    
    # Status
    status = Column(String(50), default='pending', index=True)
    total_mockups = Column(Integer, default=0)
    completed_mockups = Column(Integer, default=0)
    failed_mockups = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_completion = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship('User')
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if self.total_mockups == 0:
            return 0
        return (self.completed_mockups / self.total_mockups) * 100
    
    def __repr__(self):
        return f"<MockupBatch(id='{self.id}', name='{self.name}', status='{self.status}')>"