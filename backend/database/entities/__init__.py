# Database entities module
from .base import MultiTenantBase, CoreBase, TimestampMixin, TenantMixin, SoftDeleteMixin, AuditMixin, UserScopedMixin
from .tenant import Tenant, TenantUser, TenantApiKey, TenantSubscription, TenantUsage
from .user import (
    User, ThirdPartyOAuthToken, UserSession, UserAuditLog,
    UserRole, UserRoleAssignment, UserEmailVerification, 
    UserPasswordReset, UserLoginAttempt, UserProfile
)
from .template import EtsyProductTemplate, TemplateCategory, TemplateVersion, TemplateTag, design_template_association, template_custom_tags
from .design import DesignImage, DesignVariant, DesignCollection, DesignCollectionItem, DesignAnalytics, design_size_config_association
from .mockup import Mockup, MockupImage, MockupMaskData, MockupDesignAssociation, MockupTemplate, MockupBatch
from .order import Order, OrderItem, OrderFulfillment, OrderNote, OrderStatusHistory
from .canvas import CanvasConfig, SizeConfig, CanvasPreset, CanvasMaterial, canvas_material_compatibility
from .shopify import ShopifyProductTemplate, ShopifyProductSync, ShopifyOrderSync, ShopifyWebhook, ShopifyCollectionSync, ShopifyBatchOperation, shopify_template_tags

# Export all entities for easy importing
__all__ = [
    # Base classes
    'MultiTenantBase', 'CoreBase', 'TimestampMixin', 'TenantMixin', 
    'SoftDeleteMixin', 'AuditMixin', 'UserScopedMixin',
    
    # Core tenant entities
    'Tenant', 'TenantUser', 'TenantApiKey', 'TenantSubscription', 'TenantUsage',
    
    # User entities
    'User', 'ThirdPartyOAuthToken', 'UserSession', 'UserAuditLog',
    'UserRole', 'UserRoleAssignment', 'UserEmailVerification', 
    'UserPasswordReset', 'UserLoginAttempt', 'UserProfile',
    
    # Template entities
    'EtsyProductTemplate', 'TemplateCategory', 'TemplateVersion', 'TemplateTag',
    
    # Design entities
    'DesignImage', 'DesignVariant', 'DesignCollection', 'DesignCollectionItem', 'DesignAnalytics',
    
    # Mockup entities
    'Mockup', 'MockupImage', 'MockupMaskData', 'MockupDesignAssociation', 'MockupTemplate', 'MockupBatch',
    
    # Order entities
    'Order', 'OrderItem', 'OrderFulfillment', 'OrderNote', 'OrderStatusHistory',
    
    # Canvas entities
    'CanvasConfig', 'SizeConfig', 'CanvasPreset', 'CanvasMaterial',
    
    # Shopify entities
    'ShopifyProductTemplate', 'ShopifyProductSync', 'ShopifyOrderSync', 'ShopifyWebhook', 
    'ShopifyCollectionSync', 'ShopifyBatchOperation',
    
    # Association tables
    'design_template_association', 'template_custom_tags', 'design_size_config_association',
    'canvas_material_compatibility', 'shopify_template_tags'
]