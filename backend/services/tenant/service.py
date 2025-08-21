from typing import Optional, Tuple
from uuid import UUID
from datetime import datetime, timezone, timedelta
import secrets
import logging
import os

from sqlalchemy.orm import Session
from sqlalchemy import and_

from .models import (
    TenantRegistrationRequest, TenantLoginRequest, 
    TenantRegistrationResponse, TenantLoginResponse,
    TenantResponse, TenantUserResponse, TenantTokenResponse,
    TenantRegistrationStep1Request, TenantRegistrationStep1Response,
    IntegrationConnectRequest, IntegrationConnectResponse,
    CompleteRegistrationRequest, CompleteRegistrationResponse,
    IntegrationPlatform
)

from database.entities.tenant import Tenant, TenantUser, TenantSubscription, TenantRegistrationSession
from common.auth import (
    verify_password, get_password_hash, create_access_token
)
from common.exceptions import (
    AuthenticationError, ValidationError, DuplicateEmailError
)

logger = logging.getLogger(__name__)

class TenantService:
    """Service for tenant registration and authentication"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def register_tenant(self, registration_data: TenantRegistrationRequest) -> TenantRegistrationResponse:
        """Register a new tenant with admin user"""
        try:
            # Check if subdomain already exists
            existing_tenant = self.db.query(Tenant).filter(
                Tenant.subdomain == registration_data.subdomain
            ).first()
            
            if existing_tenant:
                raise ValidationError("Subdomain is already taken")
            
            # Check if admin email already exists across all tenants
            existing_admin = self.db.query(TenantUser).filter(
                TenantUser.email == registration_data.admin_email.lower()
            ).first()
            
            if existing_admin:
                raise DuplicateEmailError("Email address is already registered")
            
            # Create tenant
            tenant = Tenant(
                subdomain=registration_data.subdomain,
                company_name=registration_data.company_name,
                subscription_tier="basic",
                database_schema="public",  # Using single schema with tenant_id filtering
                is_active=True
            )
            
            self.db.add(tenant)
            self.db.flush()  # Get tenant ID
            
            # Create admin user
            hashed_password = get_password_hash(registration_data.admin_password)
            
            admin_user = TenantUser(
                tenant_id=tenant.id,
                email=registration_data.admin_email.lower(),
                hashed_password=hashed_password,
                first_name=registration_data.admin_first_name,
                last_name=registration_data.admin_last_name,
                role="admin",
                is_active=True
            )
            
            self.db.add(admin_user)
            self.db.flush()  # Get user ID
            
            # Create default subscription
            subscription = TenantSubscription(
                tenant_id=tenant.id,
                plan_name=registration_data.subscription_plan,
                status="active",
                billing_cycle="monthly",
                price_per_cycle=0.00,  # Free basic plan
                features={
                    "max_users": 5,
                    "max_templates": 50,
                    "api_access": False,
                    "priority_support": False
                },
                limits={
                    "users": 5,
                    "templates": 50,
                    "api_calls_per_month": 0
                },
                current_period_start=datetime.now(timezone.utc),
                current_period_end=datetime.now(timezone.utc) + timedelta(days=30)
            )
            
            self.db.add(subscription)
            
            # Generate tokens
            access_token = create_access_token(
                admin_user.email, admin_user.id, str(tenant.id)
            )
            
            refresh_token = secrets.token_urlsafe(32)
            
            tokens = TenantTokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1440 * 60,  # 24 hours in seconds
                tenant_id=tenant.id,
                user_id=admin_user.id,
                email=admin_user.email
            )
            
            self.db.commit()
            
            tenant_response = TenantResponse.from_orm(tenant)
            user_response = TenantUserResponse.from_orm(admin_user)
            
            return TenantRegistrationResponse(
                success=True,
                message="Tenant registered successfully",
                tenant=tenant_response,
                admin_user=user_response,
                tokens=tokens.dict()
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Tenant registration error: {str(e)}")
            raise e
    
    def authenticate_tenant_admin(self, login_data: TenantLoginRequest) -> TenantLoginResponse:
        """Authenticate tenant admin user"""
        try:
            email = login_data.email.lower()
            
            # Find admin user
            query = self.db.query(TenantUser).filter(
                TenantUser.email == email,
                TenantUser.is_active == True
            )
            
            # If subdomain provided, filter by it
            if login_data.subdomain:
                query = query.join(Tenant).filter(
                    Tenant.subdomain == login_data.subdomain
                )
            
            admin_user = query.first()
            
            if not admin_user:
                raise AuthenticationError("Invalid email or password")
            
            # Verify password
            if not verify_password(login_data.password, admin_user.hashed_password):
                raise AuthenticationError("Invalid email or password")
            
            # Get tenant
            tenant = self.db.query(Tenant).filter(
                Tenant.id == admin_user.tenant_id
            ).first()
            
            if not tenant or not tenant.is_active:
                raise AuthenticationError("Tenant account is disabled")
            
            # Update last login
            admin_user.last_login = datetime.now(timezone.utc)
            
            # Generate tokens
            access_token = create_access_token(
                admin_user.email, admin_user.id, str(tenant.id)
            )
            
            refresh_token = secrets.token_urlsafe(32)
            
            tokens = TenantTokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1440 * 60,  # 24 hours in seconds
                tenant_id=tenant.id,
                user_id=admin_user.id,
                email=admin_user.email
            )
            
            self.db.commit()
            
            tenant_response = TenantResponse.from_orm(tenant)
            user_response = TenantUserResponse.from_orm(admin_user)
            
            return TenantLoginResponse(
                success=True,
                message="Login successful",
                tenant=tenant_response,
                user=user_response,
                tokens=tokens.dict()
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Tenant authentication error: {str(e)}")
            raise e
    
    def get_tenant_by_subdomain(self, subdomain: str) -> Optional[Tenant]:
        """Get tenant by subdomain"""
        return self.db.query(Tenant).filter(
            Tenant.subdomain == subdomain,
            Tenant.is_active == True
        ).first()
    
    def check_subdomain_availability(self, subdomain: str) -> bool:
        """Check if subdomain is available"""
        existing = self.db.query(Tenant).filter(
            Tenant.subdomain == subdomain
        ).first()
        return existing is None

    def start_registration(self, registration_data: TenantRegistrationStep1Request) -> TenantRegistrationStep1Response:
        """Step 1: Create tenant and admin user, return OAuth URLs for integrations"""
        try:
            # Check subdomain availability
            if not self.check_subdomain_availability(registration_data.subdomain):
                raise ValidationError("Subdomain is already taken")
            
            # Check email uniqueness
            existing_user = self.db.query(TenantUser).filter(
                TenantUser.email == registration_data.admin_email.lower()
            ).first()
            
            if existing_user:
                raise DuplicateEmailError("Email address is already registered")
            
            # Create tenant
            tenant = Tenant(
                subdomain=registration_data.subdomain,
                company_name=registration_data.company_name,
                subscription_tier="basic",
                database_schema="public",
                is_active=True
            )
            
            self.db.add(tenant)
            self.db.flush()  # Get tenant ID
            
            # Create admin user
            hashed_password = get_password_hash(registration_data.admin_password)
            
            admin_user = TenantUser(
                tenant_id=tenant.id,
                email=registration_data.admin_email.lower(),
                hashed_password=hashed_password,
                first_name=registration_data.admin_first_name,
                last_name=registration_data.admin_last_name,
                role="admin",
                is_active=True
            )
            
            self.db.add(admin_user)
            self.db.flush()  # Get user ID
            
            # Create registration session
            registration_token = secrets.token_urlsafe(32)
            session = TenantRegistrationSession(
                registration_token=registration_token,
                tenant_id=tenant.id,
                admin_user_id=admin_user.id,
                selected_integrations=[platform.value for platform in registration_data.selected_integrations],
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30)  # 30 minute timeout
            )
            
            self.db.add(session)
            
            # Generate OAuth URLs for selected integrations
            oauth_urls = {}
            for platform in registration_data.selected_integrations:
                oauth_state = secrets.token_urlsafe(16)
                session.oauth_states = session.oauth_states or {}
                session.oauth_states[platform.value] = oauth_state
                
                if platform == IntegrationPlatform.ETSY:
                    oauth_urls[platform.value] = self._generate_etsy_oauth_url(oauth_state)
                elif platform == IntegrationPlatform.SHOPIFY:
                    # For Shopify, we need the store domain from the user
                    # For now, return a placeholder that will be handled by frontend
                    oauth_urls[platform.value] = self._generate_shopify_oauth_placeholder(oauth_state)
            
            self.db.commit()
            
            return TenantRegistrationStep1Response(
                success=True,
                message="Registration started. Please connect your selected platforms.",
                tenant_id=tenant.id,
                registration_token=registration_token,
                oauth_urls=oauth_urls,
                expires_in=1800  # 30 minutes
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Registration start error: {str(e)}")
            raise e

    def connect_integration(self, connect_data: IntegrationConnectRequest) -> IntegrationConnectResponse:
        """Connect an integration during registration"""
        try:
            # Get registration session
            session = self.db.query(TenantRegistrationSession).filter(
                TenantRegistrationSession.registration_token == connect_data.registration_token,
                TenantRegistrationSession.is_completed == False
            ).first()
            
            if not session:
                raise ValidationError("Invalid or expired registration token")
            
            if session.is_expired():
                raise ValidationError("Registration session has expired")
            
            # Verify OAuth state
            expected_state = session.oauth_states.get(connect_data.platform.value)
            if not expected_state or expected_state != connect_data.oauth_state:
                raise ValidationError("Invalid OAuth state")
            
            # Process OAuth based on platform
            if connect_data.platform == IntegrationPlatform.ETSY:
                shop_data = self._process_etsy_oauth(connect_data.oauth_code, session.tenant_id, session.admin_user_id)
            elif connect_data.platform == IntegrationPlatform.SHOPIFY:
                shop_data = self._process_shopify_oauth(connect_data.oauth_code, session.tenant_id, session.admin_user_id)
            else:
                raise ValidationError(f"Unsupported platform: {connect_data.platform}")
            
            # Add to connected integrations
            session.add_connected_integration(connect_data.platform.value, shop_data)
            
            self.db.commit()
            
            return IntegrationConnectResponse(
                success=True,
                message=f"{connect_data.platform.value.title()} connected successfully",
                platform=connect_data.platform.value,
                shop_name=shop_data.get("shop_name"),
                remaining_integrations=session.get_remaining_integrations()
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Integration connection error: {str(e)}")
            raise e

    def complete_registration(self, complete_data: CompleteRegistrationRequest) -> CompleteRegistrationResponse:
        """Complete registration after all integrations are connected"""
        try:
            # Get registration session
            session = self.db.query(TenantRegistrationSession).filter(
                TenantRegistrationSession.registration_token == complete_data.registration_token,
                TenantRegistrationSession.is_completed == False
            ).first()
            
            if not session:
                raise ValidationError("Invalid or expired registration token")
            
            if session.is_expired():
                raise ValidationError("Registration session has expired")
            
            if not session.is_ready_to_complete():
                remaining = session.get_remaining_integrations()
                raise ValidationError(f"Please connect remaining integrations: {', '.join(remaining)}")
            
            # Get tenant and admin user
            tenant = self.db.query(Tenant).filter(Tenant.id == session.tenant_id).first()
            admin_user = self.db.query(TenantUser).filter(TenantUser.id == session.admin_user_id).first()
            
            # Create default subscription if it doesn't exist
            existing_subscription = self.db.query(TenantSubscription).filter(
                TenantSubscription.tenant_id == tenant.id
            ).first()
            
            if not existing_subscription:
                subscription = TenantSubscription(
                    tenant_id=tenant.id,
                    plan_name="basic",
                    status="active",
                    billing_cycle="monthly",
                    price_per_cycle=0.00,  # Free basic plan
                    features={
                        "max_users": 5,
                        "max_templates": 50,
                        "api_access": False,
                        "priority_support": False
                    },
                    limits={
                        "users": 5,
                        "templates": 50,
                        "api_calls_per_month": 0
                    },
                    current_period_start=datetime.now(timezone.utc),
                    current_period_end=datetime.now(timezone.utc) + timedelta(days=30)
                )
                self.db.add(subscription)
            
            # Mark session as completed
            session.is_completed = True
            
            # Generate login tokens
            access_token = create_access_token(
                admin_user.email, admin_user.id, str(tenant.id)
            )
            
            refresh_token = secrets.token_urlsafe(32)
            
            tokens = TenantTokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=1440 * 60,  # 24 hours in seconds
                tenant_id=tenant.id,
                user_id=admin_user.id,
                email=admin_user.email
            )
            
            self.db.commit()
            
            # Build response
            tenant_response = TenantResponse.from_orm(tenant)
            user_response = TenantUserResponse.from_orm(admin_user)
            connected_platforms = [item["platform"] for item in session.connected_integrations]
            
            return CompleteRegistrationResponse(
                success=True,
                message="Registration completed successfully",
                tenant=tenant_response,
                user=user_response,
                tokens=tokens.dict(),
                connected_integrations=connected_platforms
            )
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Registration completion error: {str(e)}")
            raise e

    def _generate_etsy_oauth_url(self, state: str) -> str:
        """Generate Etsy OAuth URL"""
        client_id = os.getenv('ETSY_CLIENT_ID')
        redirect_uri = os.getenv('ETSY_OAUTH_REDIRECT_URI', 'http://localhost:3000/tenant-signup-v2?platform=etsy')
        
        return (
            f"https://www.etsy.com/oauth/connect?"
            f"response_type=code&"
            f"client_id={client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=listings_r%20shops_r&"
            f"state={state}"
        )

    def _generate_shopify_oauth_placeholder(self, state: str) -> str:
        """Generate Shopify OAuth placeholder - frontend will collect store domain"""
        client_id = os.getenv('SHOPIFY_CLIENT_ID', 'demo-client-id')
        redirect_uri = os.getenv('SHOPIFY_REGISTRATION_REDIRECT_URI', 'http://localhost:3000/tenant-signup?platform=shopify')
        
        # Return placeholder URL that frontend will customize with actual store domain
        return (
            f"shopify-oauth-placeholder?"
            f"client_id={client_id}&"
            f"scope=read_products,read_orders,write_products&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}"
        )
    
    def _generate_shopify_oauth_url(self, state: str, shop_domain: str) -> str:
        """Generate Shopify OAuth URL with actual shop domain"""
        client_id = os.getenv('SHOPIFY_CLIENT_ID', 'demo-client-id')
        redirect_uri = os.getenv('SHOPIFY_REGISTRATION_REDIRECT_URI', 'http://localhost:3000/tenant-signup?platform=shopify')
        
        # Ensure shop_domain is properly formatted
        if not shop_domain.endswith('.myshopify.com'):
            shop_domain = f"{shop_domain}.myshopify.com"
            
        return (
            f"https://{shop_domain}/admin/oauth/authorize?"
            f"client_id={client_id}&"
            f"scope=read_products,read_orders,write_products&"
            f"redirect_uri={redirect_uri}&"
            f"state={state}"
        )

    def _process_etsy_oauth(self, code: str, tenant_id: UUID, user_id: UUID) -> dict:
        """Process Etsy OAuth callback and create integration"""
        # This would normally make API calls to Etsy
        # For now, return mock data
        return {
            "shop_name": "Demo Etsy Shop",
            "shop_id": "12345",
            "connected_at": datetime.now(timezone.utc).isoformat()
        }

    def _process_shopify_oauth(self, code: str, tenant_id: UUID, user_id: UUID) -> dict:
        """Process Shopify OAuth callback and create integration"""
        # This would normally make API calls to Shopify
        # For now, return mock data
        return {
            "shop_name": "demo-shop.myshopify.com",
            "shop_id": "67890",
            "connected_at": datetime.now(timezone.utc).isoformat()
        }