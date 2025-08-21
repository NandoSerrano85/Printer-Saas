from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, text

from .models import (
    UserCreateRequest, UserUpdateRequest, UserProfileUpdateRequest,
    UserRoleAssignmentRequest, UserSearchRequest, BulkUserActionRequest,
    UserResponse, UserDetailResponse, UserProfileResponse, UserWithProfileResponse,
    UserListResponse, UserStatsResponse, UserAuditResponse, UserAuditListResponse,
    RoleResponse, RoleListResponse, BulkActionResponse, UserManagementResponse
)

from database.entities import (
    User, UserSession, UserAuditLog, UserRole, UserRoleAssignment,
    UserEmailVerification, UserPasswordReset, UserLoginAttempt, UserProfile
)

from common.auth import get_password_hash
from common.exceptions import (
    ValidationError, UserNotFound, DuplicateEmailError,
    PermissionError, ServiceError
)

logger = logging.getLogger(__name__)

class UserService:
    """Comprehensive user management service"""
    
    def __init__(self, db: Session, tenant_id: str, current_user_id: UUID = None):
        self.db = db
        self.tenant_id = tenant_id
        self.current_user_id = current_user_id
        
    def _set_tenant_context(self):
        """Set database tenant context using SQLAlchemy"""
        # For multi-tenant architecture, we'll filter by tenant_id in queries instead of schema switching
        # This is more compatible with SQLAlchemy ORM and easier to debug
        pass
    
    def _log_user_action(self, action: str, resource_type: str = 'user',
                        resource_id: str = None, details: Dict[str, Any] = None):
        """Log user management actions"""
        audit_log = UserAuditLog(
            tenant_id=self.tenant_id,
            user_id=self.current_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            created_by=self.current_user_id
        )
        self.db.add(audit_log)
    
    def _check_permission(self, permission: str) -> bool:
        """Check if current user has required permission"""
        if not self.current_user_id:
            return False
            
        user = self.db.query(User).filter(
            User.tenant_id == self.tenant_id,
            User.id == self.current_user_id
        ).first()
        if not user:
            return False
            
        return user.has_permission(permission)
    
    def _require_permission(self, permission: str):
        """Require specific permission or raise PermissionError"""
        if not self._check_permission(permission):
            raise PermissionError(f"Required permission: {permission}")
    
    def create_user(self, user_data: UserCreateRequest) -> UserDetailResponse:
        """Create a new user (admin only)"""
        try:
            self._set_tenant_context()
            self._require_permission("user.create")
            
            # Check if email already exists
            existing_user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.email == user_data.email.lower(),
                User.is_deleted == False
            ).first()
            
            if existing_user:
                raise DuplicateEmailError("Email address already registered")
            
            # Create user
            hashed_password = get_password_hash(user_data.password)
            
            user = User(
                tenant_id=self.tenant_id,
                email=user_data.email.lower(),
                hashed_password=hashed_password,
                shop_name=user_data.shop_name,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                timezone=user_data.timezone,
                language=user_data.language,
                is_active=user_data.is_active,
                email_verified=False,
                last_password_change=datetime.now(timezone.utc),
                created_by=self.current_user_id
            )
            
            self.db.add(user)
            self.db.flush()  # Get user ID
            
            # Create user profile
            profile = UserProfile(
                tenant_id=self.tenant_id,
                user_id=user.id,
                marketing_consent=False,
                analytics_consent=True,
                created_by=self.current_user_id
            )
            self.db.add(profile)
            
            # Assign roles
            for role_name in user_data.role_names:
                role = self.db.query(UserRole).filter(
                    UserRole.name == role_name
                ).first()
                
                if role:
                    role_assignment = UserRoleAssignment(
                        tenant_id=self.tenant_id,
                        user_id=user.id,
                        role_id=role.id,
                        assigned_by=self.current_user_id,
                        created_by=self.current_user_id
                    )
                    self.db.add(role_assignment)
            
            self._log_user_action(
                'user_created',
                resource_id=str(user.id),
                details={'email': user.email, 'roles': user_data.role_names}
            )
            
            self.db.commit()
            
            # Get user with roles and permissions
            return self.get_user_detail(user.id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"User creation error: {str(e)}")
            raise e
    
    def get_user(self, user_id: UUID) -> Optional[UserResponse]:
        """Get user by ID"""
        try:
            self._set_tenant_context()
            
            # Check permission
            if not (self._check_permission("user.read") or 
                   (self._check_permission("user.read_own") and user_id == self.current_user_id)):
                raise PermissionError("Insufficient permissions to read user")
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                return None
                
            return UserResponse.from_orm(user)
            
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            raise e
    
    def get_user_detail(self, user_id: UUID) -> Optional[UserDetailResponse]:
        """Get detailed user information including roles and permissions"""
        try:
            self._set_tenant_context()
            
            # Check permission
            if not (self._check_permission("user.read") or 
                   (self._check_permission("user.read_own") and user_id == self.current_user_id)):
                raise PermissionError("Insufficient permissions to read user details")
            
            user = self.db.query(User).options(
                joinedload(User.role_assignments).joinedload(UserRoleAssignment.role)
            ).filter(
                User.id == user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                return None
            
            # Get roles and permissions
            roles = user.get_roles()
            role_names = [role.name for role in roles]
            permissions = user.get_permissions()
            
            # Convert to response
            user_dict = user.__dict__.copy()
            user_dict['roles'] = role_names
            user_dict['permissions'] = permissions
            
            return UserDetailResponse(**user_dict)
            
        except Exception as e:
            logger.error(f"Get user detail error: {str(e)}")
            raise e
    
    def get_user_with_profile(self, user_id: UUID) -> Optional[UserWithProfileResponse]:
        """Get user with profile information"""
        try:
            self._set_tenant_context()
            
            # Check permission
            if not (self._check_permission("user.read") or 
                   (self._check_permission("user.read_own") and user_id == self.current_user_id)):
                raise PermissionError("Insufficient permissions to read user profile")
            
            user = self.db.query(User).options(
                joinedload(User.role_assignments).joinedload(UserRoleAssignment.role),
                joinedload(User.profile)
            ).filter(
                User.id == user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                return None
            
            # Get roles and permissions
            roles = user.get_roles()
            role_names = [role.name for role in roles]
            permissions = user.get_permissions()
            
            # Convert to response
            user_dict = user.__dict__.copy()
            user_dict['roles'] = role_names
            user_dict['permissions'] = permissions
            
            user_response = UserWithProfileResponse(**user_dict)
            
            if user.profile:
                user_response.profile = UserProfileResponse.from_orm(user.profile)
            
            return user_response
            
        except Exception as e:
            logger.error(f"Get user with profile error: {str(e)}")
            raise e
    
    def update_user(self, user_id: UUID, user_data: UserUpdateRequest) -> UserDetailResponse:
        """Update user information"""
        try:
            self._set_tenant_context()
            
            # Check permission
            if not (self._check_permission("user.update") or 
                   (self._check_permission("user.update_own") and user_id == self.current_user_id)):
                raise PermissionError("Insufficient permissions to update user")
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                raise UserNotFound("User not found")
            
            # Update fields
            update_data = user_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_by = self.current_user_id
            user.updated_at = datetime.now(timezone.utc)
            
            self._log_user_action(
                'user_updated',
                resource_id=str(user_id),
                details=update_data
            )
            
            self.db.commit()
            
            return self.get_user_detail(user_id)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"User update error: {str(e)}")
            raise e
    
    def update_user_profile(self, user_id: UUID, profile_data: UserProfileUpdateRequest) -> UserProfileResponse:
        """Update user profile"""
        try:
            self._set_tenant_context()
            
            # Check permission
            if not (self._check_permission("user.update") or 
                   (self._check_permission("user.update_own") and user_id == self.current_user_id)):
                raise PermissionError("Insufficient permissions to update user profile")
            
            # Get or create profile
            profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id,
                UserProfile.is_deleted == False
            ).first()
            
            if not profile:
                profile = UserProfile(
                    tenant_id=self.tenant_id,
                    user_id=user_id,
                    created_by=self.current_user_id
                )
                self.db.add(profile)
            
            # Update fields
            update_data = profile_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(profile, field):
                    setattr(profile, field, value)
            
            profile.updated_by = self.current_user_id
            profile.updated_at = datetime.now(timezone.utc)
            
            self._log_user_action(
                'user_profile_updated',
                resource_id=str(user_id),
                details=update_data
            )
            
            self.db.commit()
            
            return UserProfileResponse.from_orm(profile)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"User profile update error: {str(e)}")
            raise e
    
    def delete_user(self, user_id: UUID, hard_delete: bool = False) -> bool:
        """Delete user (soft delete by default)"""
        try:
            self._set_tenant_context()
            self._require_permission("user.delete")
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                raise UserNotFound("User not found")
            
            if hard_delete:
                # Hard delete - remove from database
                self.db.delete(user)
                action = 'user_hard_deleted'
            else:
                # Soft delete - mark as deleted
                user.soft_delete(self.current_user_id)
                action = 'user_soft_deleted'
            
            self._log_user_action(
                action,
                resource_id=str(user_id),
                details={'email': user.email}
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"User deletion error: {str(e)}")
            raise e
    
    def search_users(self, search_data: UserSearchRequest) -> UserListResponse:
        """Search users with filters and pagination"""
        try:
            self._set_tenant_context()
            self._require_permission("user.read")
            
            query = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.is_deleted == False
            )
            
            # Apply filters
            if search_data.query:
                search_term = f"%{search_data.query}%"
                query = query.filter(
                    or_(
                        User.email.ilike(search_term),
                        User.shop_name.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term)
                    )
                )
            
            if search_data.email:
                query = query.filter(User.email.ilike(f"%{search_data.email}%"))
            
            if search_data.shop_name:
                query = query.filter(User.shop_name.ilike(f"%{search_data.shop_name}%"))
            
            if search_data.is_active is not None:
                query = query.filter(User.is_active == search_data.is_active)
            
            if search_data.email_verified is not None:
                query = query.filter(User.email_verified == search_data.email_verified)
            
            if search_data.has_role:
                query = query.join(UserRoleAssignment).join(UserRole).filter(
                    UserRole.name == search_data.has_role
                )
            
            if search_data.created_after:
                query = query.filter(User.created_at >= search_data.created_after)
            
            if search_data.created_before:
                query = query.filter(User.created_at <= search_data.created_before)
            
            # Get total count
            total_count = query.count()
            
            # Apply sorting
            if search_data.sort_by == "email":
                sort_column = User.email
            elif search_data.sort_by == "shop_name":
                sort_column = User.shop_name
            elif search_data.sort_by == "last_login":
                sort_column = User.last_login
            else:
                sort_column = User.created_at
            
            if search_data.sort_order == "asc":
                query = query.order_by(asc(sort_column))
            else:
                query = query.order_by(desc(sort_column))
            
            # Apply pagination
            offset = (search_data.page - 1) * search_data.per_page
            users = query.offset(offset).limit(search_data.per_page).all()
            
            # Calculate pagination info
            total_pages = (total_count + search_data.per_page - 1) // search_data.per_page
            has_next = search_data.page < total_pages
            has_prev = search_data.page > 1
            
            user_responses = [UserResponse.from_orm(user) for user in users]
            
            return UserListResponse(
                users=user_responses,
                total_count=total_count,
                page=search_data.page,
                per_page=search_data.per_page,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            logger.error(f"User search error: {str(e)}")
            raise e
    
    def assign_roles(self, assignment_data: UserRoleAssignmentRequest) -> bool:
        """Assign roles to user"""
        try:
            self._set_tenant_context()
            self._require_permission("role.manage")
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == assignment_data.user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                raise UserNotFound("User not found")
            
            # Remove existing role assignments
            self.db.query(UserRoleAssignment).filter(
                UserRoleAssignment.user_id == assignment_data.user_id
            ).delete()
            
            # Add new role assignments
            for role_name in assignment_data.role_names:
                role = self.db.query(UserRole).filter(
                    UserRole.name == role_name
                ).first()
                
                if role:
                    role_assignment = UserRoleAssignment(
                        tenant_id=self.tenant_id,
                        user_id=assignment_data.user_id,
                        role_id=role.id,
                        assigned_by=self.current_user_id,
                        expires_at=assignment_data.expires_at,
                        created_by=self.current_user_id
                    )
                    self.db.add(role_assignment)
            
            self._log_user_action(
                'roles_assigned',
                resource_id=str(assignment_data.user_id),
                details={'roles': assignment_data.role_names}
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Role assignment error: {str(e)}")
            raise e
    
    def get_user_stats(self) -> UserStatsResponse:
        """Get user statistics"""
        try:
            self._set_tenant_context()
            self._require_permission("user.read")
            
            # Total users
            total_users = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.is_deleted == False
            ).count()
            
            # Active users
            active_users = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.is_deleted == False,
                User.is_active == True
            ).count()
            
            # Verified users
            verified_users = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.is_deleted == False,
                User.email_verified == True
            ).count()
            
            # Recent registrations (last 30 days)
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            recent_registrations = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.is_deleted == False,
                User.created_at >= thirty_days_ago
            ).count()
            
            # Locked accounts
            locked_accounts = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.is_deleted == False,
                User.locked_until.isnot(None),
                User.locked_until > datetime.now(timezone.utc)
            ).count()
            
            # Users with 2FA
            users_with_2fa = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.is_deleted == False,
                User.two_factor_enabled == True
            ).count()
            
            return UserStatsResponse(
                total_users=total_users,
                active_users=active_users,
                verified_users=verified_users,
                recent_registrations=recent_registrations,
                locked_accounts=locked_accounts,
                users_with_2fa=users_with_2fa
            )
            
        except Exception as e:
            logger.error(f"User stats error: {str(e)}")
            raise e
    
    def get_user_audit_log(self, user_id: UUID, page: int = 1, per_page: int = 20) -> UserAuditListResponse:
        """Get user audit log"""
        try:
            self._set_tenant_context()
            
            # Check permission
            if not (self._check_permission("user.read") or 
                   (self._check_permission("user.read_own") and user_id == self.current_user_id)):
                raise PermissionError("Insufficient permissions to read user audit log")
            
            query = self.db.query(UserAuditLog).filter(
                UserAuditLog.user_id == user_id
            ).order_by(desc(UserAuditLog.created_at))
            
            total_count = query.count()
            
            offset = (page - 1) * per_page
            audit_logs = query.offset(offset).limit(per_page).all()
            
            audit_responses = []
            for log in audit_logs:
                # Get performer info
                performer = None
                if log.created_by:
                    performer_user = self.db.query(User).filter(
                        User.tenant_id == self.tenant_id,
                        User.id == log.created_by
                    ).first()
                    performer = performer_user.email if performer_user else str(log.created_by)
                
                audit_responses.append(UserAuditResponse(
                    action=log.action,
                    resource_type=log.resource_type,
                    resource_id=log.resource_id,
                    details=log.details or {},
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    created_at=log.created_at,
                    performed_by=performer
                ))
            
            return UserAuditListResponse(
                audit_logs=audit_responses,
                total_count=total_count,
                page=page,
                per_page=per_page
            )
            
        except Exception as e:
            logger.error(f"User audit log error: {str(e)}")
            raise e
    
    def bulk_user_action(self, action_data: BulkUserActionRequest) -> BulkActionResponse:
        """Perform bulk actions on users"""
        try:
            self._set_tenant_context()
            
            # Check permissions based on action
            if action_data.action in ['activate', 'deactivate']:
                self._require_permission("user.update")
            elif action_data.action == 'delete':
                self._require_permission("user.delete")
            elif action_data.action in ['assign_role', 'remove_role']:
                self._require_permission("role.manage")
            
            processed_count = 0
            failed_count = 0
            errors = []
            
            for user_id in action_data.user_ids:
                try:
                    user = self.db.query(User).filter(
                        User.tenant_id == self.tenant_id,
                        User.id == user_id,
                        User.is_deleted == False
                    ).first()
                    
                    if not user:
                        errors.append({
                            'user_id': str(user_id),
                            'error': 'User not found'
                        })
                        failed_count += 1
                        continue
                    
                    if action_data.action == 'activate':
                        user.is_active = True
                    elif action_data.action == 'deactivate':
                        user.is_active = False
                    elif action_data.action == 'delete':
                        user.soft_delete(self.current_user_id)
                    elif action_data.action == 'assign_role':
                        role_name = action_data.parameters.get('role_name')
                        if role_name:
                            role = self.db.query(UserRole).filter(UserRole.name == role_name).first()
                            if role:
                                # Check if assignment already exists
                                existing = self.db.query(UserRoleAssignment).filter(
                                    UserRoleAssignment.user_id == user_id,
                                    UserRoleAssignment.role_id == role.id
                                ).first()
                                
                                if not existing:
                                    assignment = UserRoleAssignment(
                                        tenant_id=self.tenant_id,
                                        user_id=user_id,
                                        role_id=role.id,
                                        assigned_by=self.current_user_id,
                                        created_by=self.current_user_id
                                    )
                                    self.db.add(assignment)
                    elif action_data.action == 'remove_role':
                        role_name = action_data.parameters.get('role_name')
                        if role_name:
                            role = self.db.query(UserRole).filter(UserRole.name == role_name).first()
                            if role:
                                self.db.query(UserRoleAssignment).filter(
                                    UserRoleAssignment.user_id == user_id,
                                    UserRoleAssignment.role_id == role.id
                                ).delete()
                    
                    processed_count += 1
                    
                except Exception as e:
                    errors.append({
                        'user_id': str(user_id),
                        'error': str(e)
                    })
                    failed_count += 1
            
            if processed_count > 0:
                self._log_user_action(
                    f'bulk_{action_data.action}',
                    details={
                        'processed_count': processed_count,
                        'failed_count': failed_count,
                        'action': action_data.action,
                        'parameters': action_data.parameters
                    }
                )
                self.db.commit()
            
            return BulkActionResponse(
                success=failed_count == 0,
                message=f"Processed {processed_count} users, {failed_count} failed",
                processed_count=processed_count,
                failed_count=failed_count,
                errors=errors
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Bulk user action error: {str(e)}")
            raise e
    
    def get_roles(self) -> RoleListResponse:
        """Get all available roles"""
        try:
            self._set_tenant_context()
            self._require_permission("role.read")
            
            roles = self.db.query(UserRole).all()
            
            role_responses = []
            for role in roles:
                # Count users with this role
                user_count = self.db.query(UserRoleAssignment).filter(
                    UserRoleAssignment.role_id == role.id
                ).count()
                
                role_dict = role.__dict__.copy()
                role_dict['user_count'] = user_count
                role_responses.append(RoleResponse(**role_dict))
            
            return RoleListResponse(
                roles=role_responses,
                total_count=len(role_responses)
            )
            
        except Exception as e:
            logger.error(f"Get roles error: {str(e)}")
            raise e