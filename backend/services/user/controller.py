from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID

from .models import (
    UserCreateRequest, UserUpdateRequest, UserProfileUpdateRequest,
    UserRoleAssignmentRequest, UserSearchRequest, BulkUserActionRequest,
    UserResponse, UserDetailResponse, UserProfileResponse, UserWithProfileResponse,
    UserListResponse, UserStatsResponse, UserAuditListResponse,
    RoleListResponse, BulkActionResponse, UserManagementResponse
)

from .service import UserService
from database.core import get_db
from common.auth import (
    ActiveUserDep, get_current_user_optional, 
    extract_tenant_from_request, get_tenant_context
)
from common.exceptions import (
    ValidationError, UserNotFound, DuplicateEmailError,
    PermissionError, ServiceError
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/users",
    tags=["User Management"]
)

def get_user_service(
    request: Request,
    current_user: ActiveUserDep,
    db: Session = Depends(get_db)
) -> UserService:
    """Dependency to get user service with tenant context"""
    tenant_id = extract_tenant_from_request(request)
    return UserService(db, tenant_id, current_user.get_uuid())

# User CRUD Endpoints

@router.post("/", response_model=UserDetailResponse)
async def create_user(
    user_data: UserCreateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Create a new user (admin only)"""
    try:
        return user_service.create_user(user_data)
        
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Create user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )

@router.get("/search", response_model=UserListResponse)
async def search_users(
    query: Optional[str] = Query(None, description="Search term"),
    email: Optional[str] = Query(None, description="Filter by email"),
    shop_name: Optional[str] = Query(None, description="Filter by shop name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    email_verified: Optional[bool] = Query(None, description="Filter by email verification"),
    has_role: Optional[str] = Query(None, description="Filter by role"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", regex="^(created_at|last_login|email|shop_name)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    user_service: UserService = Depends(get_user_service)
):
    """Search users with filters and pagination"""
    try:
        search_request = UserSearchRequest(
            query=query,
            email=email,
            shop_name=shop_name,
            is_active=is_active,
            email_verified=email_verified,
            has_role=has_role,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return user_service.search_users(search_request)
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Search users error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User search failed"
        )

@router.get("/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_service: UserService = Depends(get_user_service)
):
    """Get user statistics (admin only)"""
    try:
        return user_service.get_user_stats()
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Get user stats error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID"""
    try:
        user = user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )

@router.get("/{user_id}/detail", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    """Get detailed user information including roles and permissions"""
    try:
        user = user_service.get_user_detail(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Get user detail error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details"
        )

@router.get("/{user_id}/profile", response_model=UserWithProfileResponse)
async def get_user_with_profile(
    user_id: UUID,
    user_service: UserService = Depends(get_user_service)
):
    """Get user with profile information"""
    try:
        user = user_service.get_user_with_profile(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return user
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Get user with profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@router.put("/{user_id}", response_model=UserDetailResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Update user information"""
    try:
        return user_service.update_user(user_id, user_data)
        
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User update failed"
        )

@router.put("/{user_id}/profile", response_model=UserProfileResponse)
async def update_user_profile(
    user_id: UUID,
    profile_data: UserProfileUpdateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Update user profile"""
    try:
        return user_service.update_user_profile(user_id, profile_data)
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update user profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User profile update failed"
        )

@router.delete("/{user_id}", response_model=UserManagementResponse)
async def delete_user(
    user_id: UUID,
    hard_delete: bool = Query(False, description="Perform hard delete"),
    user_service: UserService = Depends(get_user_service)
):
    """Delete user (soft delete by default)"""
    try:
        success = user_service.delete_user(user_id, hard_delete)
        
        return UserManagementResponse(
            success=success,
            message="User deleted successfully" if success else "User deletion failed"
        )
        
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Delete user error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )

# Role Management Endpoints

@router.get("/roles/list", response_model=RoleListResponse)
async def get_roles(
    user_service: UserService = Depends(get_user_service)
):
    """Get all available roles"""
    try:
        return user_service.get_roles()
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Get roles error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve roles"
        )

@router.post("/{user_id}/roles", response_model=UserManagementResponse)
async def assign_user_roles(
    user_id: UUID,
    role_names: List[str],
    expires_at: Optional[str] = None,
    user_service: UserService = Depends(get_user_service)
):
    """Assign roles to user"""
    try:
        from datetime import datetime
        
        expires_datetime = None
        if expires_at:
            expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        assignment_data = UserRoleAssignmentRequest(
            user_id=user_id,
            role_names=role_names,
            expires_at=expires_datetime
        )
        
        success = user_service.assign_roles(assignment_data)
        
        return UserManagementResponse(
            success=success,
            message="Roles assigned successfully" if success else "Role assignment failed"
        )
        
    except UserNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Assign roles error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role assignment failed"
        )

# Audit and Monitoring Endpoints

@router.get("/{user_id}/audit", response_model=UserAuditListResponse)
async def get_user_audit_log(
    user_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user_service: UserService = Depends(get_user_service)
):
    """Get user audit log"""
    try:
        return user_service.get_user_audit_log(user_id, page, per_page)
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Get user audit log error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit log"
        )

# Bulk Operations Endpoints

@router.post("/bulk-action", response_model=BulkActionResponse)
async def bulk_user_action(
    action_data: BulkUserActionRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Perform bulk actions on users"""
    try:
        return user_service.bulk_user_action(action_data)
        
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Bulk user action error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bulk action failed"
        )

# Convenience Endpoints

@router.get("/me/profile", response_model=UserWithProfileResponse)
async def get_my_profile(
    current_user: ActiveUserDep,
    user_service: UserService = Depends(get_user_service)
):
    """Get current user's profile"""
    try:
        user = user_service.get_user_with_profile(current_user.get_uuid())
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found"
            )
        
        return user
        
    except Exception as e:
        logger.error(f"Get my profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve profile"
        )

@router.put("/me/profile", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: ActiveUserDep,
    user_service: UserService = Depends(get_user_service)
):
    """Update current user's profile"""
    try:
        return user_service.update_user_profile(current_user.get_uuid(), profile_data)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update my profile error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )

# Status Endpoint

@router.get("/status", response_model=UserManagementResponse)
async def user_service_status():
    """User management service status"""
    return UserManagementResponse(
        success=True,
        message="User management service is running",
        data={
            "service": "user_management",
            "version": "1.0.0",
            "features": {
                "user_crud": True,
                "profile_management": True,
                "role_management": True,
                "bulk_operations": True,
                "audit_logging": True,
                "search_and_filter": True
            }
        }
    )