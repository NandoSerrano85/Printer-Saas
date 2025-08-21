from datetime import datetime, timedelta, timezone
from uuid import UUID
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Annotated, Optional
import jwt
import os
from dotenv import load_dotenv

from .exceptions import InvalidUserToken, AuthenticationError, TenantNotFound
from database.core import get_tenant_db
from database.entities import User, Tenant

load_dotenv()

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-here')
ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '1440'))  # 24 hours

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
http_bearer = HTTPBearer(auto_error=False)
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class TokenData:
    def __init__(self, email: str = None, user_id: str = None, tenant_id: str = None):
        self.email = email
        self.user_id = user_id
        self.tenant_id = tenant_id

class CurrentUser:
    def __init__(self, user_id: UUID, tenant_id: str, email: str):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.email = email
    
    def get_uuid(self) -> UUID:
        return self.user_id
    
    def get_tenant_id(self) -> str:
        return self.tenant_id

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return bcrypt_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return bcrypt_context.hash(password)

def create_access_token(email: str, user_id: UUID, tenant_id: str, 
                       expires_delta: timedelta = None) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": email,
        "user_id": str(user_id),
        "tenant_id": tenant_id,
        "exp": expire
    }
    
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> TokenData:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        tenant_id: str = payload.get("tenant_id")
        
        if email is None or user_id is None or tenant_id is None:
            raise AuthenticationError("Invalid token payload")
        
        return TokenData(email=email, user_id=user_id, tenant_id=tenant_id)
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.JWTError:
        raise AuthenticationError("Could not validate credentials")

def extract_tenant_from_request(request: Request) -> str:
    """Extract tenant ID from request (subdomain or header)"""
    from database.core import SessionLocal
    from database.entities.tenant import Tenant
    
    # Try to get tenant ID from header first
    tenant_header = request.headers.get("X-Tenant-ID")
    if tenant_header:
        return tenant_header
    
    # Try to extract from subdomain and convert to tenant ID
    host = request.headers.get("host", "")
    subdomain = None
    
    if host:
        subdomain = host.split(".")[0]
        # Check if it's a valid tenant subdomain (not localhost or IP)
        if subdomain and subdomain in ["localhost", "127", "0"]:
            subdomain = "demo"  # Default for local development
    else:
        subdomain = "demo"  # Default for local development
    
    # Look up tenant ID by subdomain
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.subdomain == subdomain).first()
        if tenant:
            return str(tenant.id)
    finally:
        db.close()
    
    # Default tenant ID for development (demo tenant)
    return "4437bce5-78b3-4422-af1c-fc288d739751"

async def get_current_user(
    token: str = Depends(oauth2_bearer),
    request: Request = None
) -> CurrentUser:
    """Get current authenticated user"""
    token_data = verify_token(token)
    
    if not token_data.user_id:
        raise InvalidUserToken()
    
    # Extract tenant ID from request or use token tenant ID
    tenant_id = token_data.tenant_id
    if request:
        extracted_tenant = extract_tenant_from_request(request)
        # Validate that extracted tenant matches token tenant (security check)
        if extracted_tenant != tenant_id:
            raise AuthenticationError("Tenant mismatch")
    
    return CurrentUser(
        user_id=UUID(token_data.user_id),
        tenant_id=tenant_id,
        email=token_data.email
    )

async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_tenant_db)
) -> CurrentUser:
    """Get current active user with database validation"""
    try:
        # Set tenant context
        db.execute(f"SET search_path TO tenant_{current_user.tenant_id}, core, public")
        
        # Verify user exists and is active
        user = db.query(User).filter(
            User.id == current_user.user_id,
            User.is_active == True,
            User.is_deleted == False
        ).first()
        
        if not user:
            raise AuthenticationError("User not found or inactive")
        
        return current_user
    except Exception as e:
        raise AuthenticationError(f"Failed to validate user: {str(e)}")

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(http_bearer)
) -> Optional[dict]:
    """Get current user if valid token is provided, otherwise return None"""
    if not credentials:
        return None
    
    try:
        token_data = verify_token(credentials.credentials)
        return {
            "user_id": token_data.user_id,
            "tenant_id": token_data.tenant_id,
            "email": token_data.email
        }
    except Exception:
        return None

def get_tenant_context(request: Request) -> str:
    """Get tenant context from request"""
    return extract_tenant_from_request(request)

async def validate_tenant_access(
    tenant_id: str,
    user_id: UUID,
    db: Session = Depends(get_tenant_db)
) -> bool:
    """Validate that user has access to tenant"""
    try:
        # Check if tenant exists and is active
        tenant = db.query(Tenant).filter(
            Tenant.database_schema == f"tenant_{tenant_id}",
            Tenant.is_active == True
        ).first()
        
        if not tenant:
            return False
        
        # Set tenant context and check user
        db.execute(f"SET search_path TO tenant_{tenant_id}, core, public")
        
        user = db.query(User).filter(
            User.id == user_id,
            User.is_active == True,
            User.is_deleted == False
        ).first()
        
        return user is not None
    except Exception:
        return False

# Dependency annotations for FastAPI
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
ActiveUserDep = Annotated[CurrentUser, Depends(get_current_active_user)]

class CurrentTenantAdmin:
    def __init__(self, user_id: UUID, tenant_id: str, email: str, role: str = "admin"):
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.email = email
        self.role = role
    
    def get_uuid(self) -> UUID:
        return self.user_id
    
    def get_tenant_id(self) -> str:
        return self.tenant_id

async def get_current_tenant_admin(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentTenantAdmin:
    """Get current tenant admin with validation against TenantUser table"""
    from database.core import SessionLocal
    from database.entities.tenant import TenantUser
    
    db = SessionLocal()
    try:
        # Verify admin user exists and is active in core.tenant_users
        admin_user = db.query(TenantUser).filter(
            TenantUser.id == current_user.user_id,
            TenantUser.tenant_id == UUID(current_user.tenant_id),
            TenantUser.is_active == True
        ).first()
        
        if not admin_user:
            raise AuthenticationError("Tenant admin not found or inactive")
        
        return CurrentTenantAdmin(
            user_id=current_user.user_id,
            tenant_id=current_user.tenant_id,
            email=current_user.email,
            role=admin_user.role
        )
    except Exception as e:
        raise AuthenticationError(f"Failed to validate tenant admin: {str(e)}")
    finally:
        db.close()

async def get_current_user_or_admin(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Get current user, supporting both regular users and tenant admins"""
    from database.core import SessionLocal
    from database.entities.tenant import TenantUser
    
    # First try tenant admin (more common for newly registered tenants)
    db = SessionLocal()
    try:
        admin_user = db.query(TenantUser).filter(
            TenantUser.id == current_user.user_id,
            TenantUser.tenant_id == UUID(current_user.tenant_id),
            TenantUser.is_active == True
        ).first()
        
        if admin_user:
            return current_user  # Return as CurrentUser for compatibility
            
    except Exception:
        pass  # Fall through to regular user check
    finally:
        db.close()
    
    # If not a tenant admin, try regular user
    from database.core import get_tenant_db
    db_gen = get_tenant_db()
    db_session = next(db_gen)
    
    try:
        # Set tenant context
        db_session.execute(f"SET search_path TO tenant_{current_user.tenant_id}, core, public")
        
        # Verify user exists and is active in tenant users table
        user = db_session.query(User).filter(
            User.id == current_user.user_id,
            User.is_active == True,
            User.is_deleted == False
        ).first()
        
        if user:
            return current_user
            
    except Exception as e:
        raise AuthenticationError(f"Failed to validate user: {str(e)}")
    finally:
        next(db_gen, None)  # Close the generator
    
    raise AuthenticationError("User not found or inactive")

TenantAdminDep = Annotated[CurrentTenantAdmin, Depends(get_current_tenant_admin)]
UserOrAdminDep = Annotated[CurrentUser, Depends(get_current_user_or_admin)]
TenantContextDep = Annotated[str, Depends(get_tenant_context)]