from fastapi import HTTPException
from uuid import UUID
from typing import Any

class BaseServiceException(HTTPException):
    """Base exception for all service-related errors"""
    pass

class AuthenticationError(BaseServiceException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=401, detail=detail)

class AuthorizationError(BaseServiceException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail)

class InvalidUserToken(AuthenticationError):
    def __init__(self):
        super().__init__(detail="User ID came back none. Invalid user token.")

class TenantNotFound(BaseServiceException):
    def __init__(self, tenant_id: str = None):
        detail = f"Tenant {tenant_id} not found" if tenant_id else "Tenant not found"
        super().__init__(status_code=404, detail=detail)

class UserNotFound(BaseServiceException):
    def __init__(self, user_id: UUID = None):
        detail = f"User {user_id} not found" if user_id else "User not found"
        super().__init__(status_code=404, detail=detail)

# Template Service Exceptions
class TemplateError(BaseServiceException):
    """Base exception for template-related errors"""
    pass

class TemplateNotFound(TemplateError):
    def __init__(self, template_id: UUID):
        super().__init__(status_code=404, detail=f"Template {template_id} not found")

class TemplateAlreadyExists(TemplateError):
    def __init__(self, template_name: str):
        super().__init__(status_code=409, detail=f"Template with name '{template_name}' already exists")

class TemplateCreateError(TemplateError):
    def __init__(self, detail: str = "Failed to create template"):
        super().__init__(status_code=500, detail=detail)

class TemplateUpdateError(TemplateError):
    def __init__(self, template_id: UUID, detail: str = None):
        detail = detail or f"Failed to update template {template_id}"
        super().__init__(status_code=500, detail=detail)

class TemplateDeleteError(TemplateError):
    def __init__(self, template_id: UUID):
        super().__init__(status_code=500, detail=f"Failed to delete template {template_id}")

# Design Service Exceptions
class DesignError(BaseServiceException):
    """Base exception for design-related errors"""
    pass

class DesignNotFound(DesignError):
    def __init__(self, design_id: UUID):
        super().__init__(status_code=404, detail=f"Design {design_id} not found")

class DesignUploadError(DesignError):
    def __init__(self, detail: str = "Failed to upload design"):
        super().__init__(status_code=500, detail=detail)

class DesignProcessingError(DesignError):
    def __init__(self, detail: str = "Failed to process design"):
        super().__init__(status_code=500, detail=detail)

# Mockup Service Exceptions
class MockupError(BaseServiceException):
    """Base exception for mockup-related errors"""
    pass

class MockupNotFound(MockupError):
    def __init__(self, mockup_id: UUID):
        super().__init__(status_code=404, detail=f"Mockup {mockup_id} not found")

class MockupCreateError(MockupError):
    def __init__(self, detail: str = "Failed to create mockup"):
        super().__init__(status_code=500, detail=detail)

class MockupProcessingError(MockupError):
    def __init__(self, detail: str = "Mockup processing failed"):
        super().__init__(status_code=500, detail=detail)

# Order Service Exceptions
class OrderError(BaseServiceException):
    """Base exception for order-related errors"""
    pass

class OrderNotFound(OrderError):
    def __init__(self, order_id: UUID):
        super().__init__(status_code=404, detail=f"Order {order_id} not found")

class OrderCreateError(OrderError):
    def __init__(self, detail: str = "Failed to create order"):
        super().__init__(status_code=500, detail=detail)

class OrderUpdateError(OrderError):
    def __init__(self, order_id: UUID, detail: str = None):
        detail = detail or f"Failed to update order {order_id}"
        super().__init__(status_code=500, detail=detail)

class InvalidOrderStatus(OrderError):
    def __init__(self, current_status: str, new_status: str):
        super().__init__(status_code=400, detail=f"Cannot change order status from {current_status} to {new_status}")

# Canvas Service Exceptions
class CanvasError(BaseServiceException):
    """Base exception for canvas-related errors"""
    pass

class CanvasConfigNotFound(CanvasError):
    def __init__(self, config_id: UUID):
        super().__init__(status_code=404, detail=f"Canvas configuration {config_id} not found")

class SizeConfigNotFound(CanvasError):
    def __init__(self, config_id: UUID):
        super().__init__(status_code=404, detail=f"Size configuration {config_id} not found")

class IncompatibleCanvasSize(CanvasError):
    def __init__(self, width: float, height: float):
        super().__init__(status_code=400, detail=f"Design size {width}x{height} is not compatible with canvas")

# User Service Exceptions
class UserError(BaseServiceException):
    """Base exception for user-related errors"""
    pass

class UserAlreadyExists(UserError):
    def __init__(self, email: str):
        super().__init__(status_code=409, detail=f"User with email '{email}' already exists")

class UserCreateError(UserError):
    def __init__(self, detail: str = "Failed to create user"):
        super().__init__(status_code=500, detail=detail)

class UserUpdateError(UserError):
    def __init__(self, user_id: UUID, detail: str = None):
        detail = detail or f"Failed to update user {user_id}"
        super().__init__(status_code=500, detail=detail)

# Validation Exceptions
class ValidationError(BaseServiceException):
    def __init__(self, field: str, message: str):
        super().__init__(status_code=422, detail=f"Validation error for field '{field}': {message}")

class FileValidationError(BaseServiceException):
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=f"File validation error: {detail}")

# Resource Limit Exceptions
class ResourceLimitExceeded(BaseServiceException):
    def __init__(self, resource: str, limit: int, current: int):
        super().__init__(
            status_code=429, 
            detail=f"{resource} limit exceeded. Limit: {limit}, Current: {current}"
        )

class StorageLimitExceeded(ResourceLimitExceeded):
    def __init__(self, limit_gb: int, current_gb: int):
        super().__init__("Storage", limit_gb, current_gb)

class APIRateLimitExceeded(BaseServiceException):
    def __init__(self, detail: str = "API rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)

# Etsy Service Exceptions
class EtsyError(BaseServiceException):
    """Base exception for Etsy-related errors"""
    pass

class EtsyAPIError(EtsyError):
    def __init__(self, detail: str = "Etsy API error", status_code: int = 500):
        super().__init__(status_code=status_code, detail=detail)

class EtsyAuthError(EtsyError):
    def __init__(self, detail: str = "Etsy authentication error"):
        super().__init__(status_code=401, detail=detail)

class EtsyTokenExpiredError(EtsyAuthError):
    def __init__(self, detail: str = "Etsy access token expired"):
        super().__init__(detail=detail)

class EtsyRateLimitError(EtsyError):
    def __init__(self, detail: str = "Etsy API rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)

class EtsyShopNotFound(EtsyError):
    def __init__(self, shop_id: int = None):
        detail = f"Etsy shop {shop_id} not found" if shop_id else "Etsy shop not found"
        super().__init__(status_code=404, detail=detail)

class EtsyListingError(EtsyError):
    def __init__(self, detail: str = "Etsy listing error"):
        super().__init__(status_code=500, detail=detail)

class EtsyOrderSyncError(EtsyError):
    def __init__(self, detail: str = "Failed to sync Etsy orders"):
        super().__init__(status_code=500, detail=detail)

# Dashboard Service Exceptions  
class DashboardError(BaseServiceException):
    """Base exception for dashboard-related errors"""
    pass

class DashboardDataError(DashboardError):
    def __init__(self, detail: str = "Failed to fetch dashboard data"):
        super().__init__(status_code=500, detail=detail)

# Integration Exceptions
class IntegrationError(BaseServiceException):
    """Base exception for third-party integration errors"""
    pass

class OAuthError(IntegrationError):
    def __init__(self, provider: str, detail: str = "OAuth authentication failed"):
        super().__init__(status_code=400, detail=f"{provider} OAuth error: {detail}")

class TokenRefreshError(IntegrationError):
    def __init__(self, provider: str, detail: str = "Failed to refresh access token"):
        super().__init__(status_code=401, detail=f"{provider} token refresh error: {detail}")

# Order Delete Exception
class OrderDeleteError(OrderError):
    def __init__(self, order_id: UUID):
        super().__init__(status_code=500, detail=f"Failed to delete order {order_id}")

# Shopify Service Exceptions
class ShopifyError(BaseServiceException):
    """Base exception for Shopify-related errors"""
    pass

class ShopifyAPIError(ShopifyError):
    def __init__(self, detail: str = "Shopify API error", status_code: int = 500):
        super().__init__(status_code=status_code, detail=detail)

class ShopifyAuthenticationError(ShopifyError):
    def __init__(self, detail: str = "Shopify authentication error"):
        super().__init__(status_code=401, detail=detail)

class ShopifyTokenExpiredError(ShopifyAuthenticationError):
    def __init__(self, detail: str = "Shopify access token expired"):
        super().__init__(detail=detail)

class ShopifyRateLimitError(ShopifyError):
    def __init__(self, detail: str = "Shopify API rate limit exceeded"):
        super().__init__(status_code=429, detail=detail)

class ShopifyShopNotFound(ShopifyError):
    def __init__(self, shop_domain: str = None):
        detail = f"Shopify shop {shop_domain} not found" if shop_domain else "Shopify shop not found"
        super().__init__(status_code=404, detail=detail)

class ShopifyProductError(ShopifyError):
    def __init__(self, detail: str = "Shopify product error"):
        super().__init__(status_code=500, detail=detail)

class ShopifyOrderSyncError(ShopifyError):
    def __init__(self, detail: str = "Failed to sync Shopify orders"):
        super().__init__(status_code=500, detail=detail)

class ShopifyWebhookError(ShopifyError):
    def __init__(self, detail: str = "Shopify webhook error"):
        super().__init__(status_code=400, detail=detail)

# Database Exceptions
class DatabaseError(BaseServiceException):
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=500, detail=detail)

# Additional Auth Service Exceptions
class DuplicateEmailError(BaseServiceException):
    def __init__(self, detail: str = "Email address already exists"):
        super().__init__(status_code=409, detail=detail)

class AccountLockedError(BaseServiceException):
    def __init__(self, detail: str = "Account is temporarily locked"):
        super().__init__(status_code=423, detail=detail)

class PermissionError(BaseServiceException):
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail)

class ServiceError(BaseServiceException):
    def __init__(self, detail: str = "Service operation failed"):
        super().__init__(status_code=500, detail=detail)