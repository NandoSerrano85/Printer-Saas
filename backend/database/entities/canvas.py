from sqlalchemy import Column, String, Boolean, DateTime, Text, Float, Integer, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin

class CanvasConfig(MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin):
    """Canvas configuration for different product types"""
    __tablename__ = 'canvas_configs'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    product_template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Basic configuration
    name = Column(String(255), nullable=False)  # e.g., 'UVDTF Decal', 'T-Shirt Front'
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # apparel, decals, prints, etc.
    
    # Dimensions in inches (base unit)
    width_inches = Column(Float, nullable=False)
    height_inches = Column(Float, nullable=False)
    max_width_inches = Column(Float, nullable=True)   # Maximum allowable width
    max_height_inches = Column(Float, nullable=True)  # Maximum allowable height
    min_width_inches = Column(Float, nullable=True)   # Minimum allowable width
    min_height_inches = Column(Float, nullable=True)  # Minimum allowable height
    
    # Canvas properties
    is_active = Column(Boolean, default=True, index=True)
    is_stretch = Column(Boolean, default=True)  # Can the canvas stretch/resize designs
    maintain_aspect_ratio = Column(Boolean, default=True)
    allow_rotation = Column(Boolean, default=True)
    
    # Resolution and quality settings
    default_dpi = Column(Integer, default=300)
    min_dpi = Column(Integer, default=150)
    max_dpi = Column(Integer, default=600)
    
    # Color and format settings
    color_profile = Column(String(50), default='sRGB')  # sRGB, Adobe RGB, CMYK
    background_color = Column(String(7), default='#FFFFFF')  # Hex color
    supports_transparency = Column(Boolean, default=True)
    default_file_format = Column(String(10), default='png')  # png, jpg, pdf, svg
    
    # Positioning and alignment
    default_alignment = Column(String(20), default='center')  # center, top-left, bottom-right, etc.
    padding_inches = Column(Float, default=0.0)  # Padding around design
    safe_area_inches = Column(Float, default=0.0)  # Safe area for printing
    
    # Advanced settings
    bleed_inches = Column(Float, default=0.0)  # Bleed area for printing
    cut_line_color = Column(String(7), nullable=True)  # Color for cut lines
    registration_marks = Column(Boolean, default=False)  # Include registration marks
    
    # Metadata and organization
    sort_order = Column(Integer, default=0)
    tags = Column(JSON, default=list)  # Array of tags
    canvas_metadata = Column(JSON, default=dict)  # Flexible metadata storage
    
    # Usage tracking
    usage_count = Column(Integer, default=0)  # How many times this canvas is used
    
    # Relationships
    user = relationship('User')
    product_template = relationship('EtsyProductTemplate', back_populates='canvas_configs')
    size_configs = relationship('SizeConfig', back_populates='canvas_config', cascade='all, delete-orphan')
    design_images = relationship('DesignImage', back_populates='canvas_config')
    canvas_presets = relationship('CanvasPreset', back_populates='canvas_config', cascade='all, delete-orphan')
    
    @property
    def aspect_ratio(self):
        """Calculate aspect ratio"""
        if self.height_inches and self.height_inches != 0:
            return self.width_inches / self.height_inches
        return None
    
    @property
    def area_square_inches(self):
        """Calculate total area in square inches"""
        return self.width_inches * self.height_inches
    
    @property
    def printable_area_square_inches(self):
        """Calculate printable area excluding padding and bleed"""
        width = self.width_inches - (2 * self.padding_inches) - (2 * self.bleed_inches)
        height = self.height_inches - (2 * self.padding_inches) - (2 * self.bleed_inches)
        return max(0, width) * max(0, height)
    
    def get_dimensions_dict(self, unit='inches'):
        """Get dimensions as dictionary with unit conversion"""
        base_width = self.width_inches
        base_height = self.height_inches
        
        if unit == 'cm':
            return {
                'width': base_width * 2.54,
                'height': base_height * 2.54,
                'unit': 'cm'
            }
        elif unit == 'mm':
            return {
                'width': base_width * 25.4,
                'height': base_height * 25.4,
                'unit': 'mm'
            }
        elif unit == 'pixels':
            dpi = self.default_dpi
            return {
                'width': int(base_width * dpi),
                'height': int(base_height * dpi),
                'unit': 'pixels',
                'dpi': dpi
            }
        else:  # inches
            return {
                'width': base_width,
                'height': base_height,
                'unit': 'inches'
            }
    
    def is_design_compatible(self, design_width_inches, design_height_inches):
        """Check if a design fits within canvas constraints"""
        if self.max_width_inches and design_width_inches > self.max_width_inches:
            return False
        if self.max_height_inches and design_height_inches > self.max_height_inches:
            return False
        if self.min_width_inches and design_width_inches < self.min_width_inches:
            return False
        if self.min_height_inches and design_height_inches < self.min_height_inches:
            return False
        return True
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
    
    def __repr__(self):
        return f"<CanvasConfig(id='{self.id}', name='{self.name}', {self.width_inches}x{self.height_inches})>"

class SizeConfig(MultiTenantBase, UserScopedMixin, SoftDeleteMixin, AuditMixin):
    """Size configurations within a canvas (like Adult+, Youth, etc.)"""
    __tablename__ = 'size_configs'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    product_template_id = Column(UUID(as_uuid=True), ForeignKey('etsy_product_templates.id', ondelete='CASCADE'), nullable=False, index=True)
    canvas_config_id = Column(UUID(as_uuid=True), ForeignKey('canvas_configs.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Basic configuration
    name = Column(String(255), nullable=False)  # e.g., 'Adult+', 'Adult', 'Youth', 'Toddler'
    display_name = Column(String(255), nullable=True)  # User-friendly display name
    description = Column(Text, nullable=True)
    size_category = Column(String(50), nullable=True, index=True)  # adult, youth, toddler, etc.
    
    # Dimensions in inches
    width_inches = Column(Float, nullable=False)
    height_inches = Column(Float, nullable=False)
    
    # Position within canvas (relative to canvas dimensions)
    position_x_percent = Column(Float, default=50.0)  # 0-100, center by default
    position_y_percent = Column(Float, default=50.0)  # 0-100, center by default
    
    # Scaling and adjustments
    scale_factor = Column(Float, default=1.0)  # Scaling factor for designs
    rotation_degrees = Column(Float, default=0.0)  # Rotation in degrees
    
    # Size-specific settings
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False)  # Default size for this canvas
    priority = Column(Integer, default=0)  # Display order priority
    
    # Pricing modifiers (optional)
    price_modifier = Column(Float, default=0.0)  # Additional cost for this size
    price_modifier_type = Column(String(20), default='fixed')  # fixed, percentage
    
    # Production settings
    production_time_modifier = Column(Float, default=1.0)  # Multiplier for production time
    material_usage_modifier = Column(Float, default=1.0)   # Multiplier for material usage
    
    # Quality and technical settings
    recommended_dpi = Column(Integer, nullable=True)
    min_design_quality = Column(String(20), default='medium')  # low, medium, high
    
    # Metadata
    tags = Column(JSON, default=list)
    element_metadata = Column(JSON, default=dict)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship('User')
    product_template = relationship('EtsyProductTemplate', back_populates='size_configs')
    canvas_config = relationship('CanvasConfig', back_populates='size_configs')
    design_images = relationship('DesignImage', secondary='design_size_config_association', back_populates='size_configs')
    
    @property
    def aspect_ratio(self):
        """Calculate aspect ratio"""
        if self.height_inches and self.height_inches != 0:
            return self.width_inches / self.height_inches
        return None
    
    @property
    def area_square_inches(self):
        """Calculate area in square inches"""
        return self.width_inches * self.height_inches
    
    def get_position_dict(self):
        """Get position as dictionary with various formats"""
        return {
            'x_percent': self.position_x_percent,
            'y_percent': self.position_y_percent,
            'x_inches': (self.position_x_percent / 100) * (self.canvas_config.width_inches if self.canvas_config else 0),
            'y_inches': (self.position_y_percent / 100) * (self.canvas_config.height_inches if self.canvas_config else 0)
        }
    
    def calculate_price_adjustment(self, base_price: float):
        """Calculate price adjustment for this size"""
        if self.price_modifier_type == 'percentage':
            return base_price * (self.price_modifier / 100)
        else:  # fixed
            return self.price_modifier
    
    def increment_usage(self):
        """Increment usage count and update last used"""
        from datetime import datetime, timezone
        self.usage_count += 1
        self.last_used = datetime.now(timezone.utc)
    
    def __repr__(self):
        return f"<SizeConfig(id='{self.id}', name='{self.name}', {self.width_inches}x{self.height_inches})>"

class CanvasPreset(MultiTenantBase, UserScopedMixin):
    """Predefined canvas presets for quick setup"""
    __tablename__ = 'canvas_presets'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    canvas_config_id = Column(UUID(as_uuid=True), ForeignKey('canvas_configs.id', ondelete='CASCADE'), nullable=True, index=True)
    
    # Preset information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    
    # Preset settings (JSON blob of all canvas settings)
    preset_settings = Column(JSON, nullable=False)
    
    # Organization
    is_public = Column(Boolean, default=False)  # Can be shared across tenants
    is_system = Column(Boolean, default=False)  # System-provided preset
    tags = Column(JSON, default=list)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship('User')
    canvas_config = relationship('CanvasConfig', back_populates='canvas_presets')
    
    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
    
    def __repr__(self):
        return f"<CanvasPreset(id='{self.id}', name='{self.name}')>"

class CanvasMaterial(MultiTenantBase, UserScopedMixin):
    """Materials that can be used with canvases"""
    __tablename__ = 'canvas_materials'
    
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Material information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    material_type = Column(String(50), nullable=False, index=True)  # vinyl, fabric, paper, etc.
    brand = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    finish = Column(String(50), nullable=True)  # matte, gloss, satin, etc.
    
    # Technical specifications
    thickness_mils = Column(Float, nullable=True)  # Thickness in mils
    width_inches = Column(Float, nullable=True)    # Roll/sheet width
    weight_gsm = Column(Float, nullable=True)      # Weight in grams per square meter
    
    # Working properties
    max_temperature_f = Column(Integer, nullable=True)  # Max temperature in Fahrenheit
    min_temperature_f = Column(Integer, nullable=True)  # Min temperature
    pressure_psi = Column(Float, nullable=True)         # Recommended pressure
    application_time_seconds = Column(Integer, nullable=True)
    
    # Compatibility
    compatible_canvas_types = Column(JSON, default=list)  # Array of canvas categories
    incompatible_canvas_types = Column(JSON, default=list)
    
    # Cost and inventory
    cost_per_square_inch = Column(Float, nullable=True)
    cost_per_unit = Column(Float, nullable=True)
    units_in_stock = Column(Integer, default=0)
    reorder_point = Column(Integer, default=0)
    
    # Supplier information
    supplier_name = Column(String(255), nullable=True)
    supplier_sku = Column(String(100), nullable=True)
    supplier_url = Column(String(500), nullable=True)
    
    # Organization
    is_active = Column(Boolean, default=True, index=True)
    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship('User')
    
    def is_compatible_with_canvas(self, canvas_category: str):
        """Check if material is compatible with canvas category"""
        if self.compatible_canvas_types:
            return canvas_category in self.compatible_canvas_types
        if self.incompatible_canvas_types:
            return canvas_category not in self.incompatible_canvas_types
        return True  # Default to compatible if no restrictions
    
    def calculate_cost(self, square_inches: float):
        """Calculate material cost for given area"""
        if self.cost_per_square_inch:
            return square_inches * self.cost_per_square_inch
        return 0
    
    def __repr__(self):
        return f"<CanvasMaterial(id='{self.id}', name='{self.name}', type='{self.material_type}')>"

# Association table for canvas-material compatibility
canvas_material_compatibility = Table(
    'canvas_material_compatibility',
    MultiTenantBase.metadata,
    Column('canvas_config_id', UUID(as_uuid=True), ForeignKey('canvas_configs.id', ondelete='CASCADE'), primary_key=True),
    Column('material_id', UUID(as_uuid=True), ForeignKey('canvas_materials.id', ondelete='CASCADE'), primary_key=True),
    Column('tenant_id', String, nullable=False, index=True),
    Column('is_recommended', Boolean, default=False),
    Column('notes', Text, nullable=True)
)