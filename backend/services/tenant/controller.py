from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database.core import get_db
from .service import TenantService
from .models import (
    TenantRegistrationRequest, TenantLoginRequest,
    TenantRegistrationResponse, TenantLoginResponse,
    TenantRegistrationStep1Request, TenantRegistrationStep1Response,
    IntegrationConnectRequest, IntegrationConnectResponse,
    CompleteRegistrationRequest, CompleteRegistrationResponse
)
from common.exceptions import (
    AuthenticationError, ValidationError, DuplicateEmailError
)

router = APIRouter(prefix="/api/v1/tenants", tags=["Tenant Management"])

@router.post("/register", response_model=TenantRegistrationResponse)
async def register_tenant(
    registration_data: TenantRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Register a new tenant (company) with admin user"""
    try:
        tenant_service = TenantService(db)
        return tenant_service.register_tenant(registration_data)
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant registration failed"
        )

@router.post("/login", response_model=TenantLoginResponse)
async def login_tenant_admin(
    login_data: TenantLoginRequest,
    db: Session = Depends(get_db)
):
    """Login as tenant admin"""
    try:
        tenant_service = TenantService(db)
        return tenant_service.authenticate_tenant_admin(login_data)
    
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/check-subdomain/{subdomain}")
async def check_subdomain_availability(
    subdomain: str,
    db: Session = Depends(get_db)
):
    """Check if a subdomain is available"""
    tenant_service = TenantService(db)
    available = tenant_service.check_subdomain_availability(subdomain)
    
    return {
        "subdomain": subdomain,
        "available": available,
        "message": "Subdomain is available" if available else "Subdomain is already taken"
    }

# Multi-step registration endpoints

@router.post("/register/start", response_model=TenantRegistrationStep1Response)
async def start_registration(
    registration_data: TenantRegistrationStep1Request,
    db: Session = Depends(get_db)
):
    """Step 1: Start tenant registration with integration selection"""
    try:
        tenant_service = TenantService(db)
        return tenant_service.start_registration(registration_data)
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except DuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration start failed"
        )

@router.post("/register/connect", response_model=IntegrationConnectResponse)
async def connect_integration(
    connect_data: IntegrationConnectRequest,
    db: Session = Depends(get_db)
):
    """Step 2: Connect an integration during registration"""
    try:
        tenant_service = TenantService(db)
        return tenant_service.connect_integration(connect_data)
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Integration connection failed"
        )

@router.post("/register/complete", response_model=CompleteRegistrationResponse)
async def complete_registration(
    complete_data: CompleteRegistrationRequest,
    db: Session = Depends(get_db)
):
    """Step 3: Complete registration after all integrations are connected"""
    try:
        tenant_service = TenantService(db)
        return tenant_service.complete_registration(complete_data)
    
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration completion failed"
        )