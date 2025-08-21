from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from typing import Optional
from sqlalchemy.orm import Session

from .models import (
    UserRegistrationRequest, UserLoginRequest, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest,
    EmailVerificationConfirm, TwoFactorSetupRequest, TwoFactorConfirmRequest,
    TwoFactorLoginRequest, RefreshTokenRequest, AuthenticationResponse,
    RegistrationResponse, TwoFactorSetupResponse, UserSessionsResponse,
    UserSecurityResponse, AuthResponse, TokenResponse
)

from .service import AuthService
from database.core import get_db
from common.auth import (
    ActiveUserDep, get_current_user_optional, 
    extract_tenant_from_request, get_tenant_context
)
from common.exceptions import (
    AuthenticationError, ValidationError, UserNotFound,
    DuplicateEmailError, AccountLockedError
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

def get_auth_service(
    request: Request,
    db: Session = Depends(get_db)
) -> AuthService:
    """Dependency to get auth service with tenant context"""
    tenant_id = extract_tenant_from_request(request)
    return AuthService(db, tenant_id)

def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request"""
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return ip_address, user_agent

# Registration and Login Endpoints

@router.post("/register", response_model=RegistrationResponse)
async def register_user(
    registration_data: UserRegistrationRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user account"""
    try:
        ip_address, user_agent = get_client_info(request)
        
        response = auth_service.register_user(
            registration_data, ip_address, user_agent
        )
        
        return response
        
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=AuthenticationResponse)
async def login_user(
    login_data: UserLoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user with email and password"""
    try:
        ip_address, user_agent = get_client_info(request)
        
        response = auth_service.authenticate_user(
            login_data, ip_address, user_agent
        )
        
        return response
        
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e)
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/login/2fa", response_model=AuthenticationResponse)
async def login_with_2fa(
    login_data: TwoFactorLoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user with two-factor authentication"""
    try:
        ip_address, user_agent = get_client_info(request)
        
        response = auth_service.authenticate_with_2fa(
            login_data, ip_address, user_agent
        )
        
        return response
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"2FA login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Two-factor authentication failed"
        )

@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """OAuth2 compatible token endpoint"""
    try:
        ip_address, user_agent = get_client_info(request)
        
        login_data = UserLoginRequest(
            email=form_data.username,
            password=form_data.password
        )
        
        response = auth_service.authenticate_user(
            login_data, ip_address, user_agent
        )
        
        if not response.success:
            raise AuthenticationError("Authentication failed")
        
        return response.tokens
        
    except AccountLockedError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e)
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )

@router.post("/logout", response_model=AuthResponse)
async def logout_user(
    current_user: ActiveUserDep,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout current user"""
    try:
        # Extract refresh token from Authorization header or body
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # This would be the access token, we need the refresh token
            # In a real implementation, you'd extract this differently
            pass
        
        # For now, we'll invalidate all user sessions
        # In practice, you'd want to track the specific session
        success = auth_service.logout_user("", current_user.get_uuid())
        
        return AuthResponse(
            success=success,
            message="Logged out successfully" if success else "Logout failed"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return AuthResponse(
            success=False,
            message="Logout failed"
        )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token"""
    try:
        tokens = auth_service.refresh_token(refresh_data.refresh_token)
        return tokens
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

# Password Management Endpoints

@router.post("/password/change", response_model=AuthResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: ActiveUserDep,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password"""
    try:
        success = auth_service.change_password(
            current_user.get_uuid(), password_data
        )
        
        return AuthResponse(
            success=success,
            message="Password changed successfully" if success else "Password change failed"
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.post("/password/reset/request", response_model=AuthResponse)
async def request_password_reset(
    reset_data: PasswordResetRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset"""
    try:
        ip_address, user_agent = get_client_info(request)
        
        success = auth_service.request_password_reset(
            reset_data, ip_address, user_agent
        )
        
        return AuthResponse(
            success=True,  # Always return true for security
            message="If your email is registered, you will receive reset instructions"
        )
        
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return AuthResponse(
            success=True,  # Don't reveal errors for security
            message="If your email is registered, you will receive reset instructions"
        )

@router.post("/password/reset/confirm", response_model=AuthResponse)
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Confirm password reset with token"""
    try:
        success = auth_service.reset_password(reset_data)
        
        return AuthResponse(
            success=success,
            message="Password reset successfully" if success else "Password reset failed"
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Password reset confirm error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

# Email Verification Endpoints

@router.post("/email/verify/send", response_model=AuthResponse)
async def send_email_verification(
    current_user: ActiveUserDep,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Send email verification"""
    try:
        success = auth_service.send_email_verification(current_user.get_uuid())
        
        return AuthResponse(
            success=success,
            message="Verification email sent" if success else "Failed to send verification email"
        )
        
    except Exception as e:
        logger.error(f"Send email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )

@router.post("/email/verify/confirm", response_model=AuthResponse)
async def confirm_email_verification(
    verification_data: EmailVerificationConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Confirm email verification"""
    try:
        success = auth_service.verify_email(verification_data)
        
        return AuthResponse(
            success=success,
            message="Email verified successfully" if success else "Email verification failed"
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )

# Two-Factor Authentication Endpoints

@router.post("/2fa/setup", response_model=TwoFactorSetupResponse)
async def setup_two_factor_auth(
    setup_data: TwoFactorSetupRequest,
    current_user: ActiveUserDep,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Setup two-factor authentication"""
    try:
        response = auth_service.setup_two_factor(
            current_user.get_uuid(), setup_data
        )
        
        return response
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"2FA setup error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Two-factor authentication setup failed"
        )

@router.post("/2fa/confirm", response_model=AuthResponse)
async def confirm_two_factor_auth(
    confirm_data: TwoFactorConfirmRequest,
    current_user: ActiveUserDep,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Confirm and enable two-factor authentication"""
    try:
        success = auth_service.confirm_two_factor(
            current_user.get_uuid(), confirm_data
        )
        
        return AuthResponse(
            success=success,
            message="Two-factor authentication enabled" if success else "2FA confirmation failed"
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"2FA confirmation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Two-factor authentication confirmation failed"
        )

@router.post("/2fa/disable", response_model=AuthResponse)
async def disable_two_factor_auth(
    password_data: dict,  # {"password": "user_password"}
    current_user: ActiveUserDep,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Disable two-factor authentication"""
    try:
        password = password_data.get("password")
        if not password:
            raise ValidationError("Password is required")
        
        success = auth_service.disable_two_factor(
            current_user.get_uuid(), password
        )
        
        return AuthResponse(
            success=success,
            message="Two-factor authentication disabled" if success else "2FA disable failed"
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"2FA disable error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Two-factor authentication disable failed"
        )

# Session Management Endpoints

@router.get("/sessions", response_model=UserSessionsResponse)
async def get_user_sessions(
    current_user: ActiveUserDep,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user's active sessions"""
    try:
        # Extract current session token (this would need to be implemented)
        current_session_token = None  # TODO: Extract from request
        
        sessions = auth_service.get_user_sessions(
            current_user.get_uuid(), current_session_token
        )
        
        return sessions
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sessions"
        )

@router.delete("/sessions/{session_id}", response_model=AuthResponse)
async def revoke_session(
    session_id: str,
    current_user: ActiveUserDep,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke a specific session"""
    try:
        from uuid import UUID
        session_uuid = UUID(session_id)
        
        success = auth_service.revoke_session(
            current_user.get_uuid(), session_uuid
        )
        
        return AuthResponse(
            success=success,
            message="Session revoked" if success else "Session revocation failed"
        )
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID"
        )
    except Exception as e:
        logger.error(f"Session revocation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session revocation failed"
        )

# Security Information Endpoints

@router.get("/security", response_model=UserSecurityResponse)
async def get_security_info(
    current_user: ActiveUserDep,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user security information"""
    try:
        security_info = auth_service.get_user_security_info(current_user.get_uuid())
        return security_info
        
    except Exception as e:
        logger.error(f"Get security info error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security information"
        )

# Health and Status Endpoints

@router.get("/me", response_model=AuthResponse)
async def get_current_user_info(current_user: ActiveUserDep):
    """Get current authenticated user information"""
    return AuthResponse(
        success=True,
        message="User authenticated",
        data={
            "user_id": str(current_user.get_uuid()),
            "email": current_user.email,
            "tenant_id": current_user.get_tenant_id()
        }
    )

@router.get("/status", response_model=AuthResponse)
async def auth_status():
    """Authentication service status"""
    return AuthResponse(
        success=True,
        message="Authentication service is running",
        data={
            "service": "auth",
            "version": "1.0.0",
            "features": {
                "registration": True,
                "login": True,
                "password_reset": True,
                "email_verification": True,
                "two_factor_auth": True,
                "session_management": True
            }
        }
    )