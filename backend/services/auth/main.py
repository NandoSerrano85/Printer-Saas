# services/auth/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import jwt
from datetime import datetime, timedelta

app = FastAPI(title="Authentication Service")

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    async def authenticate_tenant_user(self, 
                                     tenant_id: str, 
                                     email: str, 
                                     password: str) -> dict:
        """Authenticate user within specific tenant context"""
        user = self.db.query(TenantUser).filter(
            TenantUser.tenant_id == tenant_id,
            TenantUser.email == email,
            TenantUser.is_active == True
        ).first()
        
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(401, "Invalid credentials")
        
        # Generate tenant-scoped JWT
        payload = {
            "user_id": user.id,
            "tenant_id": tenant_id,
            "permissions": user.permissions,
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user.to_dict(),
            "tenant": user.tenant.to_dict()
        }

# Database Models
class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subdomain = Column(String(63), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    subscription_tier = Column(String(50), default="basic")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Etsy Integration
    etsy_shop_id = Column(String(100))
    etsy_access_token = Column(Text)
    etsy_refresh_token = Column(Text)

class TenantUser(Base):
    __tablename__ = "tenant_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    permissions = Column(JSON)  # Role-based permissions
    is_active = Column(Boolean, default=True)