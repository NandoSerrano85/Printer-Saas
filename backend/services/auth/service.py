from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
import secrets
import pyotp
import qrcode
import io
import base64
import logging
import os
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, text

from .models import (
    UserRegistrationRequest, UserLoginRequest, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest,
    EmailVerificationConfirm, TwoFactorSetupRequest, TwoFactorConfirmRequest,
    TwoFactorLoginRequest, TokenResponse, UserProfileResponse,
    AuthenticationResponse, RegistrationResponse, TwoFactorSetupResponse,
    SessionInfo, UserSessionsResponse, UserSecurityResponse,
    UserPermissionsResponse, PermissionResponse, SecurityEventResponse
)

from database.entities import (
    User, UserSession, UserAuditLog, UserRole, UserRoleAssignment,
    UserEmailVerification, UserPasswordReset, UserLoginAttempt, UserProfile
)

from common.auth import (
    verify_password, get_password_hash, create_access_token, 
    verify_token, JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES
)

from common.exceptions import (
    AuthenticationError, ValidationError, UserNotFound, 
    DuplicateEmailError, AccountLockedError
)

from services.email.service import email_service
from services.email.models import EmailVerificationRequest, PasswordResetRequest as EmailPasswordResetRequest

logger = logging.getLogger(__name__)

class AuthService:
    """Comprehensive authentication and user management service"""
    
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.app_url = os.getenv("APP_URL", "https://app.printer-saas.com")
        
    def _sanitize_tenant_id(self, tenant_id: str) -> str:
        """Sanitize tenant ID for use in database schema names"""
        # Remove invalid characters and replace with underscores
        # PostgreSQL schema names cannot contain colons, spaces, or other special chars
        sanitized = tenant_id.replace(':', '_').replace('.', '_').replace('-', '_')
        # Ensure it starts with a letter and only contains alphanumeric and underscores
        sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in sanitized)
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'tenant_' + sanitized
        return sanitized or 'default'
        
    def _set_tenant_context(self):
        """Set database tenant context using SQLAlchemy"""
        # For multi-tenant architecture, we'll filter by tenant_id in queries instead of schema switching
        # This is more compatible with SQLAlchemy ORM and easier to debug
        pass
    
    def _generate_secure_token(self, length: int = 32) -> str:
        """Generate a secure random token"""
        return secrets.token_urlsafe(length)
    
    def _create_user_session(self, user: User, device_info: Dict[str, Any] = None,
                           ip_address: str = None, user_agent: str = None,
                           remember_me: bool = False) -> UserSession:
        """Create a new user session"""
        session_token = self._generate_secure_token()
        expires_hours = 720 if remember_me else 24  # 30 days or 24 hours
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
        
        session = UserSession(
            tenant_id=self.tenant_id,
            user_id=user.id,
            session_token=session_token,
            device_info=device_info or {},
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            last_activity=datetime.now(timezone.utc),
            expires_at=expires_at,
            created_by=user.id
        )
        
        self.db.add(session)
        return session
    
    def _log_security_event(self, user_id: UUID, event_type: str, 
                          ip_address: str = None, user_agent: str = None,
                          details: Dict[str, Any] = None, success: bool = True):
        """Log security-related events"""
        audit_log = UserAuditLog(
            tenant_id=self.tenant_id,
            user_id=user_id,
            action=event_type,
            resource_type='authentication',
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
            created_by=user_id
        )
        self.db.add(audit_log)
    
    def _log_login_attempt(self, email: str, success: bool, 
                         ip_address: str = None, user_agent: str = None,
                         failure_reason: str = None):
        """Log login attempt for security monitoring"""
        attempt = UserLoginAttempt.log_attempt(
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=failure_reason,
            tenant_id=self.tenant_id
        )
        self.db.add(attempt)
    
    def register_user(self, registration_data: UserRegistrationRequest,
                     ip_address: str = None, user_agent: str = None) -> RegistrationResponse:
        """Register a new user within an existing tenant"""
        try:
            self._set_tenant_context()
            
            # Verify tenant exists and is active
            from database.entities.tenant import Tenant
            tenant = self.db.query(Tenant).filter(
                Tenant.id == self.tenant_id,
                Tenant.is_active == True
            ).first()
            
            if not tenant:
                raise ValidationError("Invalid tenant or tenant is disabled")
            
            # Check if email already exists in this tenant
            existing_user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.email == registration_data.email.lower(),
                User.is_deleted == False
            ).first()
            
            if existing_user:
                raise DuplicateEmailError("Email address already registered in this tenant")
            
            # Create user
            hashed_password = get_password_hash(registration_data.password)
            
            user = User(
                tenant_id=self.tenant_id,
                email=registration_data.email.lower(),
                hashed_password=hashed_password,
                shop_name=registration_data.shop_name,
                first_name=registration_data.first_name,
                last_name=registration_data.last_name,
                timezone=registration_data.timezone,
                language=registration_data.language,
                is_active=True,
                email_verified=False,
                last_password_change=datetime.now(timezone.utc),
                created_by=None  # Self-registration
            )
            
            self.db.add(user)
            self.db.flush()  # Get user ID
            
            # Create user profile
            profile = UserProfile(
                tenant_id=self.tenant_id,
                user_id=user.id,
                marketing_consent=registration_data.marketing_consent,
                analytics_consent=True,
                created_by=user.id
            )
            self.db.add(profile)
            
            # Assign default role
            default_role = self.db.query(UserRole).filter(
                UserRole.name == 'user',
                UserRole.is_system_role == True
            ).first()
            
            if default_role:
                role_assignment = UserRoleAssignment(
                    tenant_id=self.tenant_id,
                    user_id=user.id,
                    role_id=default_role.id,
                    assigned_by=user.id,
                    created_by=user.id
                )
                self.db.add(role_assignment)
            
            # Send email verification
            verification_sent = self._send_email_verification(user)
            
            # Log registration
            self._log_security_event(
                user.id, 'user_registered',
                ip_address=ip_address,
                user_agent=user_agent,
                details={'email': user.email, 'shop_name': user.shop_name}
            )
            
            self.db.commit()
            
            # Send welcome email after successful registration
            try:
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.shop_name
                email_service.send_welcome_email(
                    user.email, 
                    full_name, 
                    self.tenant_id, 
                    user.id
                )
            except Exception as e:
                logger.error(f"Failed to send welcome email: {str(e)}")
                # Don't fail registration if welcome email fails
            
            user_response = UserProfileResponse.from_orm(user)
            
            return RegistrationResponse(
                success=True,
                message="Account created successfully",
                user=user_response,
                verification_email_sent=verification_sent
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Registration error: {str(e)}")
            raise e
    
    def authenticate_user(self, login_data: UserLoginRequest,
                         ip_address: str = None, user_agent: str = None) -> AuthenticationResponse:
        """Authenticate user with email and password"""
        try:
            self._set_tenant_context()
            
            email = login_data.email.lower()
            
            # Find user
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.email == email,
                User.is_deleted == False
            ).first()
            
            if not user:
                self._log_login_attempt(
                    email, False, ip_address, user_agent, 'user_not_found'
                )
                raise AuthenticationError("Invalid email or password")
            
            # Check if account is locked
            if user.is_locked():
                self._log_login_attempt(
                    email, False, ip_address, user_agent, 'account_locked'
                )
                raise AccountLockedError("Account is temporarily locked due to failed login attempts")
            
            # Check if account is active
            if not user.is_active:
                self._log_login_attempt(
                    email, False, ip_address, user_agent, 'account_inactive'
                )
                raise AuthenticationError("Account is disabled")
            
            # Verify password
            if not verify_password(login_data.password, user.hashed_password):
                user.increment_failed_login()
                self.db.commit()
                
                self._log_login_attempt(
                    email, False, ip_address, user_agent, 'invalid_password'
                )
                raise AuthenticationError("Invalid email or password")
            
            # Check if 2FA is enabled
            if user.two_factor_enabled:
                # Return response indicating 2FA is required
                return AuthenticationResponse(
                    success=False,
                    message="Two-factor authentication required",
                    requires_2fa=True
                )
            
            # Check if email verification is required
            if not user.email_verified:
                return AuthenticationResponse(
                    success=False,
                    message="Email verification required",
                    requires_email_verification=True
                )
            
            # Successful login
            user.reset_failed_login()
            user.update_last_login()
            
            # Create session
            session = self._create_user_session(
                user, login_data.device_info, ip_address, user_agent, login_data.remember_me
            )
            
            # Create tokens
            expires_delta = timedelta(hours=24) if login_data.remember_me else None
            access_token = create_access_token(
                user.email, user.id, self.tenant_id, expires_delta
            )
            
            tokens = TokenResponse(
                access_token=access_token,
                refresh_token=session.session_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_id=user.id,
                email=user.email,
                tenant_id=self.tenant_id
            )
            
            # Log successful login
            self._log_login_attempt(email, True, ip_address, user_agent)
            self._log_security_event(
                user.id, 'login_success',
                ip_address=ip_address,
                user_agent=user_agent,
                details={'session_id': str(session.id)}
            )
            
            self.db.commit()
            
            user_response = UserProfileResponse.from_orm(user)
            
            return AuthenticationResponse(
                success=True,
                message="Login successful",
                user=user_response,
                tokens=tokens
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Authentication error: {str(e)}")
            raise e
    
    def authenticate_with_2fa(self, login_data: TwoFactorLoginRequest,
                            ip_address: str = None, user_agent: str = None) -> AuthenticationResponse:
        """Authenticate user with 2FA code"""
        try:
            self._set_tenant_context()
            
            email = login_data.email.lower()
            
            # Find user
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.email == email,
                User.is_deleted == False
            ).first()
            
            if not user or not verify_password(login_data.password, user.hashed_password):
                self._log_login_attempt(
                    email, False, ip_address, user_agent, 'invalid_credentials'
                )
                raise AuthenticationError("Invalid credentials")
            
            # Verify 2FA code
            if not user.two_factor_enabled or not user.two_factor_secret:
                raise AuthenticationError("Two-factor authentication not enabled")
            
            totp = pyotp.TOTP(user.two_factor_secret)
            if not totp.verify(login_data.two_factor_code):
                self._log_login_attempt(
                    email, False, ip_address, user_agent, 'invalid_2fa_code'
                )
                raise AuthenticationError("Invalid two-factor authentication code")
            
            # Complete authentication process (same as regular login)
            user.reset_failed_login()
            user.update_last_login()
            
            session = self._create_user_session(user, {}, ip_address, user_agent)
            
            access_token = create_access_token(user.email, user.id, self.tenant_id)
            
            tokens = TokenResponse(
                access_token=access_token,
                refresh_token=session.session_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_id=user.id,
                email=user.email,
                tenant_id=self.tenant_id
            )
            
            self._log_login_attempt(email, True, ip_address, user_agent)
            self._log_security_event(
                user.id, '2fa_login_success',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.commit()
            
            user_response = UserProfileResponse.from_orm(user)
            
            return AuthenticationResponse(
                success=True,
                message="Two-factor authentication successful",
                user=user_response,
                tokens=tokens
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"2FA authentication error: {str(e)}")
            raise e
    
    def logout_user(self, session_token: str, user_id: UUID = None) -> bool:
        """Logout user and invalidate session"""
        try:
            self._set_tenant_context()
            
            query = self.db.query(UserSession).filter(
                UserSession.session_token == session_token,
                UserSession.is_active == True
            )
            
            if user_id:
                query = query.filter(UserSession.user_id == user_id)
            
            session = query.first()
            
            if session:
                session.is_active = False
                self._log_security_event(
                    session.user_id, 'logout',
                    details={'session_id': str(session.id)}
                )
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Logout error: {str(e)}")
            return False
    
    def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        try:
            self._set_tenant_context()
            
            session = self.db.query(UserSession).filter(
                UserSession.session_token == refresh_token,
                UserSession.is_active == True
            ).first()
            
            if not session or session.is_expired():
                raise AuthenticationError("Invalid or expired refresh token")
            
            # Update session activity
            session.extend_session()
            
            # Get user
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == session.user_id
            ).first()
            if not user or not user.is_active:
                raise AuthenticationError("User account not found or inactive")
            
            # Create new access token
            access_token = create_access_token(user.email, user.id, self.tenant_id)
            
            tokens = TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user_id=user.id,
                email=user.email,
                tenant_id=self.tenant_id
            )
            
            self.db.commit()
            return tokens
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Token refresh error: {str(e)}")
            raise e
    
    def change_password(self, user_id: UUID, password_data: PasswordChangeRequest) -> bool:
        """Change user password"""
        try:
            self._set_tenant_context()
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == user_id
            ).first()
            if not user:
                raise UserNotFound("User not found")
            
            # Verify current password
            if not verify_password(password_data.current_password, user.hashed_password):
                raise AuthenticationError("Current password is incorrect")
            
            # Update password
            user.hashed_password = get_password_hash(password_data.new_password)
            user.last_password_change = datetime.now(timezone.utc)
            
            # Invalidate all sessions except current one
            self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).update({'is_active': False})
            
            self._log_security_event(
                user_id, 'password_changed',
                details={'method': 'user_initiated'}
            )
            
            self.db.commit()
            
            # Send password change notification email
            try:
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.shop_name
                email_service.send_password_changed_email(
                    user.email,
                    full_name,
                    self.tenant_id,
                    user.id
                )
            except Exception as e:
                logger.error(f"Failed to send password change notification: {str(e)}")
                # Don't fail password change if email fails
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Password change error: {str(e)}")
            raise e
    
    def request_password_reset(self, reset_data: PasswordResetRequest,
                             ip_address: str = None, user_agent: str = None) -> bool:
        """Request password reset"""
        try:
            self._set_tenant_context()
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.email == reset_data.email.lower(),
                User.is_deleted == False
            ).first()
            
            if not user:
                # Don't reveal if email exists
                return True
            
            # Create reset token
            token = self._generate_secure_token()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
            
            reset_request = UserPasswordReset(
                tenant_id=self.tenant_id,
                user_id=user.id,
                token=token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                created_by=user.id
            )
            
            self.db.add(reset_request)
            
            # Send password reset email
            reset_url = f"{self.app_url}/reset-password?token={token}"
            
            email_reset_request = EmailPasswordResetRequest(
                user_id=user.id,
                email=user.email,
                reset_token=token,
                reset_url=reset_url,
                expires_at=expires_at
            )
            
            email_result = email_service.send_password_reset_email(email_reset_request)
            
            if email_result.success:
                logger.info(f"Password reset email sent to {user.email}")
            else:
                logger.error(f"Failed to send password reset email: {email_result.error}")
            
            self._log_security_event(
                user.id, 'password_reset_requested',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Password reset request error: {str(e)}")
            return False
    
    def reset_password(self, reset_data: PasswordResetConfirm) -> bool:
        """Reset password using token"""
        try:
            self._set_tenant_context()
            
            reset_request = self.db.query(UserPasswordReset).filter(
                UserPasswordReset.token == reset_data.token,
                UserPasswordReset.is_used == False
            ).first()
            
            if not reset_request or not reset_request.is_valid():
                raise AuthenticationError("Invalid or expired reset token")
            
            # Update password
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == reset_request.user_id
            ).first()
            if not user:
                raise UserNotFound("User not found")
            
            user.hashed_password = get_password_hash(reset_data.new_password)
            user.last_password_change = datetime.now(timezone.utc)
            user.unlock_account()  # Unlock if locked
            
            # Mark reset token as used
            reset_request.mark_used()
            
            # Invalidate all user sessions
            self.db.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True
            ).update({'is_active': False})
            
            self._log_security_event(
                user.id, 'password_reset_completed',
                details={'reset_token_id': str(reset_request.id)}
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Password reset error: {str(e)}")
            raise e
    
    def _send_email_verification(self, user: User) -> bool:
        """Send email verification"""
        try:
            # Create verification token
            token = self._generate_secure_token()
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            
            verification = UserEmailVerification(
                tenant_id=self.tenant_id,
                user_id=user.id,
                email=user.email,
                token=token,
                expires_at=expires_at,
                created_by=user.id
            )
            
            self.db.add(verification)
            
            # Send verification email
            verification_url = f"{self.app_url}/verify-email?token={token}"
            
            email_request = EmailVerificationRequest(
                user_id=user.id,
                email=user.email,
                verification_token=token,
                verification_url=verification_url,
                expires_at=expires_at
            )
            
            email_result = email_service.send_verification_email(email_request)
            
            if email_result.success:
                logger.info(f"Email verification sent to {user.email}")
                return True
            else:
                logger.error(f"Failed to send verification email: {email_result.error}")
                return False
            
        except Exception as e:
            logger.error(f"Email verification send error: {str(e)}")
            return False
    
    def send_email_verification(self, user_id: UUID) -> bool:
        """Send email verification for user"""
        try:
            self._set_tenant_context()
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == user_id
            ).first()
            if not user:
                raise UserNotFound("User not found")
            
            if user.email_verified:
                return False  # Already verified
            
            return self._send_email_verification(user)
            
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            return False
    
    def verify_email(self, verification_data: EmailVerificationConfirm) -> bool:
        """Verify email using token"""
        try:
            self._set_tenant_context()
            
            verification = self.db.query(UserEmailVerification).filter(
                UserEmailVerification.token == verification_data.token,
                UserEmailVerification.is_verified == False
            ).first()
            
            if not verification or verification.is_expired():
                raise AuthenticationError("Invalid or expired verification token")
            
            # Mark as verified
            verification.mark_verified()
            
            # Update user
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == verification.user_id
            ).first()
            if user:
                user.mark_email_verified()
                
                self._log_security_event(
                    user.id, 'email_verified',
                    details={'verification_id': str(verification.id)}
                )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Email verification error: {str(e)}")
            raise e
    
    def setup_two_factor(self, user_id: UUID, setup_data: TwoFactorSetupRequest) -> TwoFactorSetupResponse:
        """Setup two-factor authentication"""
        try:
            self._set_tenant_context()
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == user_id
            ).first()
            if not user:
                raise UserNotFound("User not found")
            
            # Verify password
            if not verify_password(setup_data.password, user.hashed_password):
                raise AuthenticationError("Invalid password")
            
            # Generate TOTP secret
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            
            # Generate QR code
            provisioning_uri = totp.provisioning_uri(
                user.email,
                issuer_name="Printer SaaS"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            qr_code_data = base64.b64encode(buffer.getvalue()).decode()
            qr_code_url = f"data:image/png;base64,{qr_code_data}"
            
            # Generate backup codes
            backup_codes = [self._generate_secure_token(8) for _ in range(10)]
            
            # Store secret (not enabled until confirmed)
            user.two_factor_secret = secret
            
            self._log_security_event(
                user_id, '2fa_setup_initiated'
            )
            
            self.db.commit()
            
            return TwoFactorSetupResponse(
                success=True,
                secret=secret,
                qr_code_url=qr_code_url,
                backup_codes=backup_codes
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"2FA setup error: {str(e)}")
            raise e
    
    def confirm_two_factor(self, user_id: UUID, confirm_data: TwoFactorConfirmRequest) -> bool:
        """Confirm and enable two-factor authentication"""
        try:
            self._set_tenant_context()
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not user.two_factor_secret:
                raise AuthenticationError("Two-factor setup not found")
            
            # Verify TOTP code
            totp = pyotp.TOTP(user.two_factor_secret)
            if not totp.verify(confirm_data.code):
                raise AuthenticationError("Invalid verification code")
            
            # Enable 2FA
            user.two_factor_enabled = True
            
            self._log_security_event(
                user_id, '2fa_enabled'
            )
            
            self.db.commit()
            
            # Send 2FA enabled notification email
            try:
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.shop_name
                email_service.send_two_factor_enabled_email(
                    user.email,
                    full_name,
                    self.tenant_id,
                    user.id
                )
            except Exception as e:
                logger.error(f"Failed to send 2FA enabled notification: {str(e)}")
                # Don't fail 2FA enable if email fails
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"2FA confirmation error: {str(e)}")
            raise e
    
    def disable_two_factor(self, user_id: UUID, password: str) -> bool:
        """Disable two-factor authentication"""
        try:
            self._set_tenant_context()
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == user_id
            ).first()
            if not user:
                raise UserNotFound("User not found")
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                raise AuthenticationError("Invalid password")
            
            # Disable 2FA
            user.two_factor_enabled = False
            user.two_factor_secret = None
            
            self._log_security_event(
                user_id, '2fa_disabled'
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"2FA disable error: {str(e)}")
            raise e
    
    def get_user_sessions(self, user_id: UUID, current_session_token: str = None) -> UserSessionsResponse:
        """Get user's active sessions"""
        try:
            self._set_tenant_context()
            
            sessions = self.db.query(UserSession).filter(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).order_by(desc(UserSession.last_activity)).all()
            
            session_info = []
            for session in sessions:
                info = SessionInfo.from_orm(session)
                info.is_current = (session.session_token == current_session_token)
                session_info.append(info)
            
            return UserSessionsResponse(
                sessions=session_info,
                total_count=len(session_info)
            )
            
        except Exception as e:
            logger.error(f"Get sessions error: {str(e)}")
            raise e
    
    def revoke_session(self, user_id: UUID, session_id: UUID) -> bool:
        """Revoke a specific user session"""
        try:
            self._set_tenant_context()
            
            session = self.db.query(UserSession).filter(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
                UserSession.is_active == True
            ).first()
            
            if session:
                session.is_active = False
                self._log_security_event(
                    user_id, 'session_revoked',
                    details={'revoked_session_id': str(session_id)}
                )
                self.db.commit()
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Session revocation error: {str(e)}")
            return False
    
    def get_user_security_info(self, user_id: UUID) -> UserSecurityResponse:
        """Get user security information"""
        try:
            self._set_tenant_context()
            
            user = self.db.query(User).filter(
                User.tenant_id == self.tenant_id,
                User.id == user_id
            ).first()
            if not user:
                raise UserNotFound("User not found")
            
            # Get recent security events
            recent_events = self.db.query(UserAuditLog).filter(
                UserAuditLog.user_id == user_id,
                UserAuditLog.resource_type == 'authentication'
            ).order_by(desc(UserAuditLog.created_at)).limit(20).all()
            
            events = []
            for event in recent_events:
                events.append(SecurityEventResponse(
                    event_type=event.action,
                    timestamp=event.created_at,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    details=event.details or {},
                    success=not event.action.endswith('_failed')
                ))
            
            return UserSecurityResponse(
                recent_events=events,
                failed_login_attempts=user.failed_login_attempts,
                account_locked=user.is_locked(),
                locked_until=user.locked_until,
                two_factor_enabled=user.two_factor_enabled,
                email_verified=user.email_verified,
                last_password_change=user.last_password_change
            )
            
        except Exception as e:
            logger.error(f"Get security info error: {str(e)}")
            raise e